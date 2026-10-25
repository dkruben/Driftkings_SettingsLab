"""Build Driftkings locally: Python 2.7, Flash, native helpers and release artifacts."""
import argparse
import ast
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.package_tools import metadata, sha, validate_swf, verify_package, write_json, zip_entries
from build_tools.toolchain import discover, require_tools
from build_tools.validate_build_data import apply_patch_set, build_plan, input_path, read_json, require
from build_tools.generate_defaults import TARGET as DEFAULT_VALUES, render as render_defaults, assemble as assemble_defaults
from build_tools.modpack import create as create_modpack


def version_contract(root=ROOT):
    path = root / 'mod/res/scripts/client/driftkings/core/updater/versioning.py'
    spec = importlib.util.spec_from_file_location('_dk_build_versioning', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def select_version(root, release, requested, channel):
    source = input_path(root, release['version_source'])
    tree = ast.parse(source.read_text(encoding='utf-8'))
    current = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets))
    configured = version_contract(root).Version(release['version'])
    configured_channel = 'beta' if configured.prerelease else 'stable'
    require(release['channel'] == configured_channel and configured.allowed(configured_channel),
            'Configured release version and channel disagree')
    version = version_contract(root).Version(requested or configured.text)
    resolved = 'beta' if version.prerelease else 'stable'
    require(channel in ('auto', resolved), 'Version and channel disagree: %s / %s' % (version.text, channel))
    require(version.allowed(resolved), 'Only beta/rc prereleases are supported by the updater')
    return version.text, resolved, current


def override_version(text, version):
    """Replace only the VERSION literal, retaining other package initialization."""
    tree = ast.parse(text)
    nodes = [node.value for node in tree.body if isinstance(node, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets)]
    require(len(nodes) == 1, 'Expected exactly one global VERSION assignment')
    node = nodes[0]
    lines = text.encode('utf-8').splitlines(keepends=True)
    start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
    end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
    raw = text.encode('utf-8')
    return (raw[:start] + repr(version).encode('ascii') + raw[end:]).decode('utf-8')


def sync_source_version(root, release, version):
    """Persist the selected version without changing encoding or line endings."""
    source = input_path(root, release['version_source'])
    original = source.read_bytes()
    updated = override_version(original.decode('utf-8'), version).encode('utf-8')
    if updated != original:
        source.write_bytes(updated)


def sync_release_version(root, release, version, channel):
    """Keep JSON authoritative, including explicit command-line version changes."""
    sync_source_version(root, release, version)
    if release['version'] != version or release['channel'] != channel:
        release.update(version=version, channel=channel)
        write_json(root / 'build_data/release.json', release)


def output_path(root, value):
    path = input_path(root, value)
    require(path.resolve().is_relative_to((root / 'build').resolve()) and path.resolve() != (root / 'build').resolve(),
            'Build output must stay inside the repository build directory: ' + value)
    return path


def run_tool(command, log, env=None, timeout=240, cwd=None):
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('wb') as stream:
        startup = None
        if os.name == 'nt':
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
        result = subprocess.run([str(s) for s in command], cwd=cwd or ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                timeout=timeout, startupinfo=startup,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        tail = log.read_text(encoding='utf-8', errors='replace')[-2500:]
        raise ValueError('Build tool failed (%s); see %s\n%s' % (result.returncode, log, tail))


def run_worker(tools, run, job, name):
    job_path = run / (name + '-job.json')
    result = run / (name + '-result.json')
    job['result'] = str(result)
    write_json(job_path, job)
    worker = ROOT / 'build_tools/python27_worker.py'
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    if tools['python27']:
        command = [tools['python27'], '-B', str(worker), str(job_path)]
    else:
        env['DK_COMPILE_JOB'] = str(job_path)
        command = [tools['hg'], '--config', 'extensions.dkcompiler=' + str(worker), 'dkcompile']
    run_tool(command, run / 'logs' / (name + '.log'), env)
    require(result.is_file(), 'Python 2.7 worker did not produce a result')
    return read_json(result)


def generate(root, config, plan, tools, run):
    outputs = {}
    needed = {a['generator'] for a in plan['assets'] if a['generator']}
    for name in sorted(needed):
        spec = config['generators'][name]
        output_path(root, spec['output'])
        destination = run / 'generated' / spec['output']
        destination.parent.mkdir(parents=True, exist_ok=True)
        print('Generating: ' + name, flush=True)
        if spec['kind'] == 'flash':
            sdk = Path(tools['flex_home'])
            libraries = input_path(root, spec['library_manifest'])
            command = [tools['java'], '-Xmx1024m', '-jar', tools['mxmlc_jar'],
                       '+flexlib=' + str(sdk / 'frameworks'), '-load-config=', '-compiler.theme=',
                       '-compiler.external-library-path=' + tools['playerglobal']]
            command += ['-compiler.external-library-path+=' + str(libraries.parent / item['name'])
                        for item in read_json(libraries)['libraries']]
            command += ['-compiler.library-path=' + str(sdk / 'frameworks/libs/framework.swc'),
                        '-compiler.source-path=' + ','.join(str(input_path(root, p)) for p in spec['source_paths']),
                        '-target-player=' + spec['target_player'], '-swf-version=' + str(spec['swf_version']),
                        '-debug=false', '-compiler.strict=true', '-compiler.optimize=true',
                        '-default-size=%s,%s' % (spec['width'], spec['height']), '-default-frame-rate=' + str(spec['fps']),
                        '-output=' + str(destination), str(input_path(root, spec['entrypoint']))]
            run_tool(command, run / 'logs' / (name + '.log'))
            validate_swf(destination.read_bytes())
        elif spec['kind'] == 'vehicle_markers':
            from build_tools.vehicle_markers import build as build_vehicle_markers
            build_vehicle_markers(root, destination, spec, tools, config['game']['root'])
        elif spec['kind'] == 'gameface_patch':
            raw = None
            for package in spec['game_packages']:
                with zipfile.ZipFile(Path(config['game']['root']) / package) as archive:
                    if spec['resource'] in archive.namelist():
                        require(raw is None, 'Ambiguous Gameface resource')
                        raw = archive.read(spec['resource'])
            require(raw is not None, 'Gameface resource not found')
            patch = read_json(input_path(root, spec['patch_file']))
            destination.write_bytes(apply_patch_set(raw, patch))
        elif spec['kind'] == 'csharp':
            command = [tools['csc'], '/nologo', '/target:exe', '/platform:anycpu', '/optimize+', '/debug-',
                       '/out:' + str(destination)]
            command += ['/reference:' + reference for reference in spec['references']]
            command.append(str(input_path(root, spec['source'])))
            command += [str(input_path(root, source)) for source in spec.get('additional_sources', [])]
            run_tool(command, run / 'logs' / (name + '.log'))
            binary = destination.read_bytes()
            require(binary.startswith(b'MZ') and len(binary) <= 256 * 1024, 'Invalid native helper: ' + name)
            output_path(root, spec['metadata'])
            meta = run / 'generated' / spec['metadata']
            write_json(meta, dict(schema=1, size=len(binary), sha256=sha(destination)))
            outputs[spec['metadata']] = meta
        else:
            raise ValueError('Unsupported generator: ' + name)
        outputs[spec['output']] = destination
    return outputs


def git_state(root):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    try:
        return dict(commit=git('rev-parse', 'HEAD'), dirty=bool(git('status', '--porcelain')),
                    epoch=int(git('log', '-1', '--format=%ct')))
    except (OSError, subprocess.CalledProcessError):
        return dict(commit=None, dirty=True, epoch=946684800)


def source_inventory(root, plan):
    paths = {item['source'] for key in ('python', 'defaults') for item in plan[key]}
    paths.update(item['source'] for item in plan['assets'] if not item['generator'])
    paths.update(plan['dependencies'])
    for folder, suffix in (('build_data', '.json'), ('build_tools', '.py'), ('installer/source', '.cs'), ('flash_source', '.as'), ('flash_source/shared/swc', '.swc')):
        paths.update(p.relative_to(root).as_posix() for p in (root / folder).rglob('*' + suffix)
                     if p.name != 'toolchain.local.json')
    return {name: sha(input_path(root, name)) for name in sorted(paths)}


def atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name('.' + destination.name + '.' + uuid.uuid4().hex + '.tmp')
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)


def replace_directory(source, destination):
    """Bound transient Windows scanner/sharing locks; never retry other errors."""
    for attempt in range(8):
        try:
            os.replace(source, destination)
            return
        except OSError as error:
            if getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 7:
                raise
            time.sleep(min(2.0, 0.25 * (2 ** attempt)))


def publish_local(root, candidate, destination, config, generated, compiled, plan):
    """Promote only verified outputs; preserve the previous version directory."""
    require(candidate.resolve().is_relative_to((root / 'build').resolve()) and
            destination.resolve().is_relative_to((root / 'build').resolve()) and
            candidate.parent.resolve() == destination.parent.resolve(), 'Unsafe artifact promotion paths')
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = None
    if destination.exists():
        previous = output_path(root, 'build/previous/' + destination.name + '-' + uuid.uuid4().hex)
        previous.parent.mkdir(parents=True, exist_ok=True)
        replace_directory(destination, previous)
    try:
        replace_directory(candidate, destination)
    except OSError:
        if previous is not None:
            replace_directory(previous, destination)
        raise
    atomic_copy(destination / 'driftkings.wotmod', output_path(root, config['package']['output']))
    for name, source in generated.items():
        atomic_copy(source, output_path(root, name))
    for item in plan['python']:
        name = item['target'][len(config['python']['archive_root']) + 1:]
        atomic_copy(compiled / item['target'], output_path(root, config['python']['staging_root'] + '/' + name))


def build(args):
    root = ROOT
    config = read_json(root / 'build_data/build_config.json')
    release = read_json(root / 'build_data/release.json')
    require(release['schema_version'] == 1, 'Unsupported release schema')
    require(release['package_id'] == 'driftkings.unified', 'Package identity must match the native installer contract')
    endpoint_tree = ast.parse((root / 'mod/res/scripts/client/driftkings/core/updater/endpoints.py').read_text(encoding='utf-8'))
    repository = next(ast.literal_eval(n.value) for n in endpoint_tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'REPOSITORY' for t in n.targets))
    require(release['repository'] == repository, 'Release repository must match the packaged updater')
    version, channel, source_version = select_version(root, release, args.version, args.channel)
    if args.game_root:
        config['game']['root'] = str(Path(args.game_root).resolve())
    plan = build_plan(root, check_component_list=False, game_root=config['game']['root'], check_defaults=False)
    tools = discover(root, vars(args))
    destination = output_path(root, config['package']['release_root' if args.mode == 'release' else 'debug_root'] + '/' + channel + '/' + version)
    if args.plan:
        print(json.dumps(dict(version=version, source_version=source_version, channel=channel, mode=args.mode,
                              output=str(destination), tools=tools,
                              python=len(plan['python']), assets=len(plan['assets']), defaults=len(plan['defaults'])), indent=2))
        return destination
    require_tools(tools)
    game = Path(config['game']['root'])
    version_xml = ET.parse(game / 'version.xml')
    require(version_contract(root).normalize_game_version(version_xml.findtext('version')) == config['game']['version'], 'Installed game version differs from build target')
    require((version_xml.findtext('meta/realm') or '').strip() == config['game']['realm'], 'Installed game realm differs from build target')
    reference = Path(config['reference']['root']) / '.version_name'
    require(reference.read_text(encoding='utf-8-sig').strip() == config['reference']['version'], 'Reference source version mismatch')
    if not args.keep_source_version:
        sync_release_version(root, release, version, channel)
        source_version = version
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    run = output_path(root, 'build/runs/' + stamp)
    run.mkdir(parents=True)
    report = dict(schema=1, status='running', version=version, source_version=source_version, channel=channel,
                  mode=args.mode, publishable=False, gameVersion=config['game']['version'],
                  realm=config['game']['realm'], tools=tools, git=git_state(root), logs=str(run / 'logs'))
    started = time.monotonic()
    try:
        inventory = source_inventory(root, plan)
        report['inputs'] = inventory
        components = sorted(c['entrypoint'] for c in plan['components'] if c['enabled'] and c['kind'] == 'feature')
        python_spec = config['python']
        runtime_relative = Path(release['version_source']).relative_to(python_spec['source_root']).as_posix()
        runtime_target = python_spec['archive_root'] + '/' + str(Path(runtime_relative).with_suffix('.pyc')).replace('\\', '/')
        component_target = python_spec['archive_root'] + '/' + str(Path(python_spec['component_list']).with_suffix('.pyc')).replace('\\', '/')
        overrides = {runtime_target: override_version((root / release['version_source']).read_text(encoding='utf-8'), version),
                     component_target: '# Generated from enabled build manifests.\nCOMPONENTS = %r\n' % (tuple(components),)}
        defaults_relative = Path(DEFAULT_VALUES).relative_to(python_spec['source_root']).with_suffix('.pyc').as_posix()
        overrides[python_spec['archive_root'] + '/' + defaults_relative] = render_defaults(root)
        epoch = int(os.environ.get('SOURCE_DATE_EPOCH', report['git']['epoch']))
        require(0 <= epoch <= 0xffffffff, 'SOURCE_DATE_EPOCH outside Python 2.7 header range')
        compiled = run / 'compiled'
        print('Compiling Python 2.7: %d modules (%s, %s)' % (len(plan['python']), version, channel), flush=True)
        report['python'] = run_worker(tools, run, dict(action='compile', files=[dict(source=str(root / i['source']), target=i['target']) for i in plan['python']],
                                                    output=str(compiled), overrides=overrides, epoch=epoch), 'python')
        generated = generate(root, config, plan, tools, run)
        entries = {item['target']: (compiled / item['target']).read_bytes() for item in plan['python']}
        for item in plan['assets']:
            require(item['target'] not in entries, 'Duplicate archive target')
            entries[item['target']] = (generated[item['source']] if item['generator'] else root / item['source']).read_bytes()
        require('meta.xml' not in entries, 'Manifest overrides package metadata')
        entries['meta.xml'] = metadata(release, version)
        candidate = destination.parent / ('.' + version + '-' + stamp)
        candidate.mkdir(parents=True)
        package = candidate / 'driftkings.wotmod'
        zip_entries(package, entries)
        verify_package(package, entries, version, release['package_id'])
        changelog = release['changelog']
        if args.changelog:
            changelog = [line.strip() for line in Path(args.changelog).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        require(isinstance(changelog, list) and len(changelog) <= 50 and all(isinstance(s, str) and len(s) <= 500 for s in changelog), 'Invalid changelog')
        release_manifest = dict(schema=1, version=version, channel=channel, gameVersion=config['game']['version'],
                                file='driftkings.wotmod', size=package.stat().st_size, sha256=sha(package),
                                download='https://github.com/%s/releases/download/v%s/driftkings.wotmod' % (release['repository'], version), changelog=changelog)
        defaults = {item['target']: (root / item['source']).read_bytes() for item in plan['defaults']}
        zip_entries(candidate / 'Driftkings-defaults.zip', defaults, zipfile.ZIP_DEFLATED)
        distribution = {'mods/' + config['game']['version'] + '/driftkings.wotmod': package.read_bytes(),
                        'Driftkings-defaults.zip': (candidate / 'Driftkings-defaults.zip').read_bytes()}
        for name in plan['dependencies']:
            path = root / name
            target = candidate / 'dependencies' / path.name
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(path, target)
            distribution['mods/' + config['game']['version'] + '/' + path.name] = path.read_bytes()
        instructions = ('Driftkings %s (%s), World of Tanks %s\n\n'
                        'Extract the mods directory into the game directory.\n'
                        'First installation: extract Driftkings-defaults.zip only when no Driftkings settings exist.\n'
                        'Updates: keep your existing mods/configs/driftkings settings.\n'
                        'No game files were installed by this build.\n') % (version, channel, config['game']['version'])
        distribution['INSTALL.txt'] = instructions.encode('utf-8')
        zip_entries(candidate / ('Driftkings-%s-WoT-%s.zip' % (version, config['game']['version'])), distribution, zipfile.ZIP_DEFLATED)
        modpack = create_modpack(candidate, version, channel, config['game']['version'], defaults)
        write_json(candidate / 'modpack.json', modpack)
        release_manifest.update(schema=2, modpack=modpack)
        write_json(candidate / 'release.json', release_manifest)
        report['verification'] = run_worker(tools, run, dict(action='verify', package=str(package), manifest=str(candidate / 'release.json'),
                                                           modpack=str(candidate / 'modpack.json'),
                                                           version=version, channel=channel, game_version=config['game']['version'], components=components,
                                                           defaults=assemble_defaults(root)[0], selector=assemble_defaults(root)[1]), 'verify')
        require(source_inventory(root, plan) == inventory, 'Build inputs changed during compilation; previous output preserved')
        report.update(status='success', publishable=bool(args.mode == 'release'),
                      counts=dict(components=len(components), python=len(plan['python']), assets=len(plan['assets']), entries=len(entries), defaults=len(defaults)),
                      generated={name: sha(path) for name, path in generated.items()}, seconds=round(time.monotonic() - started, 3))
        report['artifacts'] = {p.relative_to(candidate).as_posix(): dict(size=p.stat().st_size, sha256=sha(p))
                               for p in sorted(candidate.rglob('*')) if p.is_file()}
        write_json(candidate / 'build-report.json', report)
        sums = '\n'.join('%s  %s' % (sha(p), p.relative_to(candidate).as_posix()) for p in sorted(candidate.rglob('*')) if p.is_file()) + '\n'
        (candidate / 'SHA256SUMS.txt').write_bytes(sums.encode('utf-8'))
        publish_local(root, candidate, destination, config, generated, compiled, plan)
        write_json(run / 'build-report.json', report)
        print('Build complete: ' + str(destination), flush=True)
        return destination
    except Exception as error:
        report.update(status='failed', error=str(error), seconds=round(time.monotonic() - started, 3))
        write_json(run / 'build-report.json', report)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('debug', 'release'), default='debug')
    parser.add_argument('--version', help='Override JSON version and synchronize release.json and source VERSION')
    parser.add_argument('--keep-source-version', action='store_true',
                        help='Override only packaged VERSION, for temporary compatibility/update tests')
    parser.add_argument('--channel', choices=('auto', 'stable', 'beta'), default='auto')
    parser.add_argument('--game-root', help='Read-only game installation override')
    parser.add_argument('--changelog', help='UTF-8 changelog, one entry per line')
    parser.add_argument('--plan', action='store_true', help='Display version, outputs and tool discovery without building')
    for key in ('python27', 'hg', 'flex_home', 'mxmlc_jar', 'playerglobal', 'java', 'csc', 'rabcdasm_home'):
        parser.add_argument('--' + key.replace('_', '-'), dest=key)
    args = parser.parse_args()
    try:
        build(args)
    except (ValueError, OSError, KeyError, TypeError, StopIteration, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        parser.exit(1, 'Build failed: %s\n' % error)


if __name__ == '__main__':
    main()
