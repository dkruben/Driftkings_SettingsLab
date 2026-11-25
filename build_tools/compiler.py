"""Build Driftkings locally: Python 2.7, Flash, native helpers and release artifacts."""
import argparse
from contextlib import ExitStack
import ast
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
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

from build_tools.build_diagnostics import exception_record, record_failure
from build_tools.isolated_output import IsolatedOutput, active_output, tool_environment
from build_tools import publication_state
from build_tools.package_tools import metadata, normalize_swf_compile_date, sha, validate_swf, verify_package, write_json, zip_entries
from build_tools.toolchain import KEYS as TOOL_KEYS, discover, reference_snapshot_matches, require_tools
from build_tools.validate_build_data import apply_patch_set, apply_battleinfo_patch, gameface_patch_for_build, read_gameface_resource, build_plan, source_client, production_profile, input_path, read_json, require
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
    contract = version_contract(root)
    configured = contract.Version(release['version'])
    configured_channel = 'beta' if configured.prerelease else 'stable'
    require(release['channel'] == configured_channel and configured.allowed(configured_channel),
            'Configured release version and channel disagree')
    version = contract.Version(requested or configured.text)
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
    scope = active_output()
    if scope is not None:
        scope.check(log)
        cwd = scope.check(cwd or scope.path / "workspace")
        env = tool_environment(env)
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('wb') as stream:
        startup = None
        if os.name == 'nt':
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
        result = subprocess.run([str(s) for s in command], cwd=cwd or ROOT, env=env, stdout=stream,
                                stderr=subprocess.STDOUT,
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


def supports_deterministic_csharp(csc):
    """Roslyn compilers omit timestamps and random module IDs on request; the .NET Framework 4 csc cannot."""
    try:
        scope = active_output()
        result = subprocess.run([str(csc), '-help'],
                                cwd=str(scope.path / 'workspace') if scope else None,
                                env=tool_environment(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except (OSError, subprocess.SubprocessError):
        return False
    return b'-deterministic' in result.stdout


def generate(root, config, plan, tools, run, epoch):
    outputs = {}
    deterministic_csharp = None
    needed = {a['generator'] for a in plan['assets'] if a['generator']}
    for name in sorted(needed):
        spec = config['generators'][name]
        scope = active_output()
        if scope:
            scope.phase, scope.component = 'generate', name
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
                        '-default-size=%s,%s' % (spec['width'], spec['height']),
                        '-default-frame-rate=' + str(spec['fps']),
                        '-output=' + str(destination), str(input_path(root, spec['entrypoint']))]
            run_tool(command, run / 'logs' / (name + '.log'))
            destination.write_bytes(normalize_swf_compile_date(destination.read_bytes(), epoch))
            validate_swf(destination.read_bytes())
        elif spec['kind'] == 'vehicle_markers':
            from build_tools.vehicle_markers import build as build_vehicle_markers
            build_vehicle_markers(root, destination, spec, tools, tools['game_root'],
                                  library_manifest=config['generators']['battle_flash']['library_manifest'])
        elif spec['kind'] == 'gameface_patch':
            raw = None
            for package in spec['game_packages']:
                with zipfile.ZipFile(Path(tools['game_root']) / package) as archive:
                    if spec['resource'] in archive.namelist():
                        require(raw is None, 'Ambiguous Gameface resource')
                        raw = archive.read(spec['resource'])
            require(raw is not None, 'Gameface resource not found')
            build = source_client(tools['game_root'], config)['build']
            patch = gameface_patch_for_build(root, spec, build)
            destination.write_bytes(apply_patch_set(raw, patch))
        elif spec['kind'] == 'native_battleinfo_patch':
            raw = read_gameface_resource(tools['game_root'], spec['game_packages'], spec['resource'])
            output = apply_battleinfo_patch(raw, read_json(input_path(root, spec['patch_file'])), root)
            destination.write_bytes(output)
        elif spec['kind'] == 'csharp':
            if deterministic_csharp is None:
                deterministic_csharp = supports_deterministic_csharp(tools['csc'])
            command = [tools['csc'], '/nologo', '/target:exe', '/platform:anycpu', '/optimize+', '/debug-',
                       '/out:' + str(destination)]
            if deterministic_csharp:
                command.append('/deterministic')
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


def git_state(root, readonly=False):
    def git(*args):
        options = dict(env=dict(os.environ, GIT_OPTIONAL_LOCKS='0')) if readonly else {}
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL, **options).decode('utf-8').strip()
    try:
        return dict(commit=git('rev-parse', 'HEAD'), dirty=bool(git('status', '--porcelain')),
                    epoch=int(git('log', '-1', '--format=%ct')))
    except (OSError, subprocess.CalledProcessError):
        return dict(commit=None, dirty=True, epoch=946684800)


def source_inventory(root, plan, extra_paths=()):
    paths = {item['source'] for key in ('python', 'defaults') for item in plan[key]}
    paths.update(item['source'] for item in plan['assets'] if not item['generator'])
    paths.update(plan['dependencies'])
    for folder, suffix in (('build_data', '.json'), ('build_tools', '.py'), ('installer/source', '.cs'),
                           ('flash_source', '.as'), ('flash_source/shared/swc', '.swc')):
        paths.update(p.relative_to(root).as_posix() for p in (root / folder).rglob('*' + suffix)
                     if p.name != 'toolchain.local.json')
    paths.update(extra_paths)
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


def check_release_identity(root, release):
    require(release['schema_version'] == 1, 'Unsupported release schema')
    require(release['package_id'] == 'driftkings.unified', 'Package identity must match the native installer contract')
    endpoint_tree = ast.parse((root / 'mod/res/scripts/client/driftkings/core/updater/endpoints.py').read_text(encoding='utf-8'))
    repository = next(ast.literal_eval(n.value) for n in endpoint_tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'REPOSITORY' for t in n.targets))
    require(release['repository'] == repository, 'Release repository must match the packaged updater')


CT_REFERENCE_FILES = (
    'gui/impl/lobby/page/lobby_footer.py',
    'frameworks/wulf/view/view.py',
    'gui/impl/pub/view_component.py',
    'gui/impl/battle/random/hud.py',
    'gui/impl/lobby/hangar/random/random_hangar.py',
    'gui/impl/lobby/hangar/presenters/user_missions_presenter.py',
    'gui/Scaleform/daapi/view/meta/PlayersPanelMeta.py',
    'gui/Scaleform/framework/package_layout.py',
)


def check_client(root, config, tools):
    """Check CT identity and required reference files; never generate build outputs."""
    version_xml = ET.parse(Path(tools['game_root']) / 'version.xml')
    public = version_contract(root).normalize_game_version(version_xml.findtext('version'))
    require(public == config['game']['version'], 'Installed game version differs from build target')
    identity = source_client(tools['game_root'], config)
    realm, build, revision = (identity[key] for key in ('realm', 'build', 'revision'))
    if realm != 'CT':
        check_production_reference(root, config, tools, identity)
        return realm
    reference_root = Path(tools['reference_root'])
    name = (reference_root / '.version_name').read_text(encoding='utf-8-sig').strip()
    if name == config['reference']['version']:
        # The configured source label (2.4.2.5518) is bound to CT #996. Without a
        # manifest, only the provenance files are checked; the label is not a public version.
        require(build == '996', 'Reference label ' + name + ' is bound to CT #996, not #' + build)
        if not (reference_root / 'manifest.json').exists():
            for relative in CT_REFERENCE_FILES:
                target = reference_root / 'sources/res/scripts/client' / relative
                require(target.is_file() and target.resolve().is_relative_to(reference_root.resolve()),
                        'Missing or escaped legacy reference contract: ' + relative)
            return realm
    else:
        expected = public + ' Common Test #' + build
        require(name == expected, 'Reference source version/build mismatch')
    manifest = read_json(reference_root / 'manifest.json')
    identity = manifest.get('game_version', {})
    require(manifest.get('schema') == 1 and manifest.get('realm') == realm
            and manifest.get('version_name') == public + ' Common Test'
            and manifest.get('consistent') is True, 'Inconsistent CT reference manifest')
    require(identity.get('raw') == 'v.' + public + ' Common Test #' + build
            and identity.get('number') == public and identity.get('suffix') == 'Common Test'
            and type(identity.get('build')) is int and identity['build'] == int(build)
            and identity.get('client_revision') == revision and identity.get('realm') == realm,
            'CT reference identity contradicts installed version/build/revision')
    for directory in ('sources', 'sources_as', 'sources_gameface', '__stubs'):
        require((reference_root / directory).is_dir(), 'Incomplete CT reference: ' + directory)
    for relative in CT_REFERENCE_FILES:
        output = 'sources/res/scripts/client/' + relative
        entry = manifest.get('entries', {}).get('res/scripts/client/' + relative[:-3] + '.pyc', {})
        recovered = entry.get('decompiled', {})
        target = reference_root / output
        require(target.is_file() and target.resolve().is_relative_to(reference_root.resolve()),
                'Missing or escaped CT reference contract: ' + relative)
        require(recovered.get('status') == 'success' and recovered.get('output') == output
                and re.fullmatch(r'[0-9a-f]{64}', entry.get('sha256', '')) is not None
                and recovered.get('input_sha256') == entry['sha256']
                and recovered.get('sha256') == sha(target),
                'CT reference integrity mismatch: ' + relative)
    return realm

def check_production_reference(root, config, tools, identity):
    profile = production_profile(root, config, identity)
    reference = Path(tools['reference_root']).resolve()
    pin = config['reference']['production_clients'][identity['realm']]
    require(reference_snapshot_matches(reference, pin['snapshot']),
            'Production reference snapshot mismatch: %s expects %s (reference: %s)'
            % (identity['realm'], pin['snapshot'], reference.name))
    require(source_client(reference / 'sources', config) == identity, 'Production reference identity mismatch')
    hashes = profile['reference_sha256']
    required = {'sources/version.xml', 'sources/paths.xml'}
    required.update('sources/res/scripts/client/' + path for path in CT_REFERENCE_FILES)
    require(required <= set(hashes), 'Incomplete production source contract')
    for relative, digest in hashes.items():
        require(sha(input_path(reference, relative)) == digest, 'Production source hash mismatch: ' + relative)


def production_generators(root, config, profile, identity):
    """Use the normal generators with reviewed inputs for this production build."""
    generators = config['generators']
    pinned = profile['generators']
    fields = {'flash': 'library_manifest', 'vehicle_markers': 'locks',
              'gameface_patch': 'patch_file', 'native_battleinfo_patch': 'patch_file'}
    required = {name for name, spec in generators.items() if spec['kind'] in fields}
    require(set(pinned) == required, 'Incomplete production resource pins')
    # Shared pins name the realm and build they were reviewed for; the installed client must still
    # match their bytes (source hash, native movie digest, Flash library digests), checked below.
    pin = profile['pinned_identity']
    for name in required:
        spec = generators[name]
        kind = spec['kind']
        path = pinned[name]
        manifest = read_json(input_path(root, path))
        if kind == 'flash':
            require(manifest['game_version'] == config['game']['version']
                    and manifest['source_version'] == pin['snapshot'],
                    'Production Flash library manifest mismatch')
            for library in manifest['libraries']:
                binary = input_path(input_path(root, path).parent, library['name'])
                require(sha(binary).lower() == library['sha256'].lower(), 'Production Flash library hash mismatch')
            spec['library_manifest'] = path
        elif kind == 'vehicle_markers':
            require(manifest['gameVersion'] == config['game']['version']
                    and manifest['clientBuild'] == pin['build'] and manifest['realm'] == pin['realm']
                    and manifest['clientRevision'] == pin['revision'],
                    'Production vehicle markers lock mismatch')
            spec['locks'] = {identity['build']: path}
            spec['lock_pins'] = {identity['build']: pin['build']}
        else:
            require(manifest['game_version'] == config['game']['version']
                    and manifest['client_build'] == pin['build'] and manifest['realm'] == pin['realm']
                    and manifest['resource'] == spec['resource'], 'Production Gameface patch target mismatch: ' + name)
            spec.pop('patch_files', None)
            spec['patch_file'] = path
    return generators


def python_overrides(root, config, release, version, components):
    """Generated sources compiled in place of their checked-in counterparts."""
    python_spec = config['python']
    runtime_relative = Path(release['version_source']).relative_to(python_spec['source_root']).as_posix()
    runtime_target = python_spec['archive_root'] + '/' + str(Path(runtime_relative).with_suffix('.pyc')).replace('\\', '/')
    component_target = python_spec['archive_root'] + '/' + str(Path(python_spec['component_list']).with_suffix('.pyc')).replace('\\', '/')
    overrides = {runtime_target: override_version((root / release['version_source']).read_text(encoding='utf-8'),
                                                  version),
                 component_target: '# Generated from enabled build manifests.\nCOMPONENTS = %r\n' % (tuple(components),)}
    defaults_relative = Path(DEFAULT_VALUES).relative_to(python_spec['source_root']).with_suffix('.pyc').as_posix()
    overrides[python_spec['archive_root'] + '/' + defaults_relative] = render_defaults(root)
    return overrides


def package_entries(root, release, plan, compiled, generated, version):
    entries = {item['target']: (compiled / item['target']).read_bytes() for item in plan['python']}
    for item in plan['assets']:
        require(item['target'] not in entries, 'Duplicate archive target')
        entries[item['target']] = (generated[item['source']] if item['generator']
                                   else root / item['source']).read_bytes()
    require('meta.xml' not in entries, 'Manifest overrides package metadata')
    entries['meta.xml'] = metadata(release, version)
    return entries


def read_changelog(release, path):
    changelog = release['changelog']
    if path:
        changelog = [line.strip() for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    require(isinstance(changelog, list) and len(changelog) <= 50
            and all(isinstance(s, str) and len(s) <= 500 for s in changelog), 'Invalid changelog')
    return changelog


def write_distribution(root, config, plan, candidate, package, version, channel):
    """Write the defaults archive, dependency copies and manual-installation ZIP; return the defaults."""
    game_version = config['game']['version']
    defaults = {item['target']: (root / item['source']).read_bytes() for item in plan['defaults']}
    zip_entries(candidate / 'Driftkings-defaults.zip', defaults, zipfile.ZIP_DEFLATED)
    distribution = {'mods/' + game_version + '/driftkings.wotmod': package.read_bytes(),
                    'Driftkings-defaults.zip': (candidate / 'Driftkings-defaults.zip').read_bytes()}
    for name in plan['dependencies']:
        path = root / name
        target = candidate / 'dependencies' / path.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, target)
        distribution['mods/' + game_version + '/' + path.name] = path.read_bytes()
    instructions = ('Driftkings %s (%s), World of Tanks %s\n\n'
                    'Extract the mods directory into the game directory.\n'
                    'First installation: extract Driftkings-defaults.zip only when no Driftkings settings exist.\n'
                    'Updates: keep your existing mods/configs/driftkings settings.\n'
                    'No game files were installed by this build.\n') % (version, channel, game_version)
    distribution['INSTALL.txt'] = instructions.encode('utf-8')
    zip_entries(candidate / ('Driftkings-%s-WoT-%s.zip' % (version, game_version)), distribution, zipfile.ZIP_DEFLATED)
    return defaults


def artifact_files(candidate):
    return [p for p in sorted(candidate.rglob('*')) if p.is_file()]


def validate_isolated_args(args, channel=None):
    if not getattr(args, 'isolated_output', False):
        return
    require(args.mode == 'debug', '--isolated-output requires --mode debug; publication is forbidden')
    require(args.keep_source_version, '--isolated-output requires --keep-source-version')
    require(args.channel != 'stable' and channel != 'stable', '--isolated-output requires an experimental prerelease')


def build(args):
    validate_isolated_args(args)
    previous_bytecode = sys.dont_write_bytecode
    if getattr(args, 'isolated_output', False):
        sys.dont_write_bytecode = True
    try:
        with ExitStack() as stack:
            return _build(args, stack)
    finally:
        sys.dont_write_bytecode = previous_bytecode


def _build(args, stack):
    root = ROOT
    config = read_json(root / 'build_data/build_config.json')
    release = read_json(root / 'build_data/release.json')
    check_release_identity(root, release)
    version, channel, source_version = select_version(root, release, args.version, args.channel)
    validate_isolated_args(args, channel)
    isolated = getattr(args, "isolated_output", False)
    tools = discover(root, vars(args))
    plan = build_plan(root, check_component_list=False, game_root=tools['game_root'], check_defaults=False)
    destination = output_path(root,
                              config['package']['release_root' if args.mode == 'release'
                                                else 'debug_root'] + '/' + channel + '/' + version)
    if args.plan:
        preview = dict(version=version, source_version=source_version, channel=channel, mode=args.mode,
                       output=str(destination), tools=tools, python=len(plan['python']),
                       assets=len(plan['assets']), defaults=len(plan['defaults']))
        if isolated:
            preview.update(output='build/experiments/<exclusive-run-id>/output', isolated_output=True)
        print(json.dumps(preview, indent=2))
        return destination
    if args.mode == 'release':
        identity = source_client(tools['game_root'], config)
        profile = production_profile(root, config, identity)
    require_tools(tools)
    realm = check_client(root, config, tools)
    expected_realm = getattr(args, 'expect_realm', None)
    require(expected_realm in (None, realm),
            'Game installation realm %s differs from --expect-realm %s' % (realm, expected_realm))
    identity = source_client(tools['game_root'], config)
    profile = production_profile(root, config, identity) if realm != 'CT' else None
    runtime_realms = sorted(profile['realm_evidence']) if profile else [realm]
    production_inputs = []
    if profile:
        production_generators(root, config, profile, identity)
        production_inputs = list(profile['generators'].values()) + list(profile['realm_evidence'].values())
    build_git = git_state(root, True) if isolated else None
    if not args.keep_source_version:
        sync_release_version(root, release, version, channel)
        source_version = version
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    if isolated:
        # Validate all configuration-derived output names BEFORE reserving anything.
        for spec in config['generators'].values():
            output_path(root, spec['output'])
            if 'metadata' in spec:
                output_path(root, spec['metadata'])
        read_changelog(release, args.changelog)
        epoch = int(os.environ.get('SOURCE_DATE_EPOCH', build_git['epoch']))
        require(0 <= epoch <= 0xffffffff, 'SOURCE_DATE_EPOCH outside Python 2.7 header range')
        scope = stack.enter_context(IsolatedOutput(root, stamp))
        run = scope.path / 'workspace'
        destination = scope.path / 'output'
    else:
        run = output_path(root, 'build/runs/' + stamp)
        run.mkdir(parents=True)
    report = dict(schema=1, status='running', version=version, source_version=source_version, channel=channel,
                  mode=args.mode, publishable=False, gameVersion=config['game']['version'],
                  realm=realm, source_client=identity, runtime_realms=runtime_realms, tools=tools, git=build_git if isolated else git_state(root), logs=str(run / 'logs'))
    started = time.monotonic()
    try:
        if isolated:
            write_json(scope.path / 'diagnostics' / 'state.json', dict(status='running', publishable=False))
        inventory = source_inventory(root, plan, production_inputs)
        report['inputs'] = inventory
        components = sorted(c['entrypoint'] for c in plan['components'] if c['enabled'] and c['kind'] == 'feature')
        overrides = python_overrides(root, config, release, version, components)
        epoch = int(os.environ.get('SOURCE_DATE_EPOCH', report['git']['epoch']))
        require(0 <= epoch <= 0xffffffff, 'SOURCE_DATE_EPOCH outside Python 2.7 header range')
        if isolated:
            scope.phase, scope.component = 'compile', 'python27'
        compiled = run / 'compiled'
        print('Compiling Python 2.7: %d modules (%s, %s)' % (len(plan['python']), version, channel), flush=True)
        report['python'] = run_worker(tools, run,
                                      dict(action='compile',
                                           files=[dict(source=str(root / i['source']), target=i['target'])
                                                  for i in plan['python']],
                                                    output=str(compiled), overrides=overrides, epoch=epoch), 'python')
        generated = generate(root, config, plan, tools, run, epoch)
        if isolated:
            scope.phase, scope.component = 'package', None
        entries = package_entries(root, release, plan, compiled, generated, version)
        candidate = destination if isolated else destination.parent / ('.' + version + '-' + stamp)
        if not isolated:
            candidate.mkdir(parents=True)
        package = candidate / 'driftkings.wotmod'
        zip_entries(package, entries)
        verify_package(package, entries, version, release['package_id'])
        release_manifest = dict(schema=1, version=version, channel=channel, gameVersion=config['game']['version'],
                                file='driftkings.wotmod', size=package.stat().st_size, sha256=sha(package),
                                download='https://github.com/%s/releases/download/v%s/driftkings.wotmod' % (release['repository'], version),
                                changelog=read_changelog(release, args.changelog))
        defaults = write_distribution(root, config, plan, candidate, package, version, channel)
        modpack = create_modpack(candidate, version, channel, config['game']['version'], defaults)
        write_json(candidate / 'modpack.json', modpack)
        release_manifest.update(schema=2, modpack=modpack)
        write_json(candidate / 'release.json', release_manifest)
        expected_defaults, selector, _ = assemble_defaults(root)
        if isolated:
            scope.phase, scope.component = 'verify', 'python27'
        report['verification'] = run_worker(tools, run,
                                            dict(action='verify', package=str(package),
                                                 manifest=str(candidate / 'release.json'),
                                                           modpack=str(candidate / 'modpack.json'),
                                                           version=version, channel=channel,
                                                           game_version=config['game']['version'],
                                                           components=components,
                                                           defaults=expected_defaults, selector=selector), 'verify')
        require(source_inventory(root, plan, production_inputs) == inventory,
                'Build inputs changed during compilation; previous output preserved')
        # Publication is never granted by the compiler: signing, runtime evidence and approval are separate facts.
        report.update(status='success', publishable=False,
                      profile=publication_state.DEVELOPMENT_PROFILE if realm == 'CT' else publication_state.PRODUCTION_PROFILE,
                      counts=dict(components=len(components), python=len(plan['python']), assets=len(plan['assets']),
                                  entries=len(entries), defaults=len(defaults)),
                      generated={name: sha(path) for name, path in generated.items()},
                      seconds=round(time.monotonic() - started, 3))
        report['eligible_for_signing'] = publication_state.eligible_for_signing(report)
        report['publication_state'] = publication_state.classify(report)
        report['artifacts'] = {p.relative_to(candidate).as_posix(): dict(size=p.stat().st_size, sha256=sha(p))
                               for p in artifact_files(candidate)}
        write_json(candidate / 'build-report.json', report)
        sums = '\n'.join('%s  %s' % (sha(p), p.relative_to(candidate).as_posix())
                         for p in artifact_files(candidate)) + '\n'
        (candidate / 'SHA256SUMS.txt').write_bytes(sums.encode('utf-8'))
        if isolated:
            write_json(scope.path / 'manifests' / 'build-report.json', report)
        else:
            publish_local(root, candidate, destination, config, generated, compiled, plan)
        write_json(run / 'build-report.json', report)
        if isolated:
            write_json(scope.path / 'diagnostics' / 'state.json', dict(status='complete', publishable=False))
        print('Build complete: ' + str(destination), flush=True)
        return destination
    except Exception as error:
        if isolated:
            report['seconds'] = round(time.monotonic() - started, 3)
            record_failure(scope, report, error, write_json)
        else:
            report.update(status='failed', error=str(error), seconds=round(time.monotonic() - started, 3))
            write_json(run / 'build-report.json', report)
        raise


def argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-output', action='store_true',
                        help='Debug prerelease only; requires --keep-source-version; keep ALL outputs in a fresh experiment')
    parser.add_argument('--mode', choices=('debug', 'release'), default='debug')
    parser.add_argument('--version', help='Override JSON version and synchronize release.json and source VERSION')
    parser.add_argument('--keep-source-version', action='store_true',
                        help='Override only packaged VERSION, for temporary compatibility/update tests')
    parser.add_argument('--channel', choices=('auto', 'stable', 'beta'), default='auto')
    parser.add_argument('--game-root', help='Read-only game installation override')
    parser.add_argument('--expect-realm', choices=('NA', 'EU', 'ASIA', 'CN', 'CT'),
                        help='Refuse to build unless the installed client has this realm')
    parser.add_argument('--changelog', help='UTF-8 changelog, one entry per line')
    parser.add_argument('--plan', action='store_true',
                        help='Display version, outputs and tool discovery without building')
    for key in TOOL_KEYS:
        if key != 'game_root':
            parser.add_argument('--' + key.replace('_', '-'), dest=key)
    return parser


def main():
    parser = argument_parser()
    args = parser.parse_args()
    try:
        build(args)
    except (ValueError, OSError, KeyError, TypeError, StopIteration, subprocess.SubprocessError,
            zipfile.BadZipFile) as error:
        if args.isolated_output:
            parser.exit(1, 'Build failed:\n' + exception_record(error)['traceback'])
        parser.exit(1, 'Build failed: %s\n' % error)


if __name__ == '__main__':
    main()
