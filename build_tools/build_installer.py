"""Generate an Inno Setup wizard that changes JSON choices, never its payload."""
import argparse
import zipfile
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.generate_ui_catalog import installer_catalog
from build_tools.package_tools import sha, write_json, zip_entries
from build_tools.validate_build_data import relative_path
from build_tools.publication_state import require_mutable, require_signable
from build_tools.validate_locales import catalog
from build_tools.validate_build_data import build_plan, read_json, require, supported_realms, production_realms
from build_tools.validate_installer_assets import validate as validate_assets
from build_tools.modpack import verify as verify_modpack


BACK_IMAGE_OPACITY = 60


def text(value):
    require(isinstance(value, str) and value.strip(), 'Missing installer text')
    return re.sub(r'<[^>]*>', '', value).replace('\r', '').replace('\n', '%n')


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def quoted(value):
    return '"' + value.replace('"', '""') + '"'


def installer_messages(root=ROOT):
    """Wizard languages and texts; English is the fallback for any language a text omits."""
    document = read_json(Path(root) / 'installer/setup/messages.json')
    require(set(document) == {'languages', 'custom_messages', 'messages'}, 'Invalid installer messages')
    languages = document['languages']
    require(isinstance(languages, dict) and {'en', 'pt'} <= set(languages) and
            all(re.fullmatch(r'[a-z]{2}', code) and isinstance(path, str) and path.startswith('compiler:')
                for code, path in languages.items()), 'Installer languages require en, pt and compiler language files')
    for section in ('custom_messages', 'messages'):
        for key, values in document[section].items():
            require(re.fullmatch(r'[A-Za-z][A-Za-z0-9]*', key) and isinstance(values, dict) and
                    {'en', 'pt'} <= set(values) <= set(languages), 'Invalid installer message: ' + key)
            # Placeholders and preprocessor values must survive translation.
            expected = sorted(re.findall(r'%s|%n|\{#\w+\}', values['en']))
            for lang, value in values.items():
                text(value)
                require(sorted(re.findall(r'%s|%n|\{#\w+\}', value)) == expected,
                        'Installer message placeholders differ: %s/%s' % (lang, key))
    return document


def definitions(root=ROOT):
    root = Path(root)
    languages = tuple(installer_messages(root)['languages'])
    components = installer_catalog(root, languages)
    by_name = {entry['key']: entry for entry in components}
    catalogs = {lang: catalog(root / ('mod/res/mods/driftkings/text/' + lang + '.yml'))
                for lang in languages}
    options = read_json(root / 'installer/setup/options.json')
    presets = read_json(root / 'installer/setup/presets.json')
    require(set(options) == {'options'} and isinstance(options['options'], list), 'Invalid installer options')
    require(set(presets) == {'presets'} and isinstance(presets['presets'], list), 'Invalid installer presets')
    extras, seen = [], set()
    for item in options['options']:
        require(set(item) == {'component', 'key', 'label_key'} and item['component'] in by_name,
                'Unknown installer option component')
        require(re.fullmatch(r'[a-z][A-Za-z0-9_]*', item['key']) is not None and item['key'] != 'enabled',
                'Installer options must name a top-level boolean other than enabled')
        require((item['component'], item['key']) not in seen, 'Duplicate installer option')
        seen.add((item['component'], item['key']))
        component = by_name[item['component']]
        values = read_json(root / 'res/configs/driftkings' / component['file'])
        require(type(values.get(item['key'])) is bool, 'Installer option is not a boolean: ' + item['key'])
        labels = {lang: text(document['TEXT'].get(item['component'], {}).get(item['label_key']))
                  for lang, document in catalogs.items()}
        extras.append(dict(item, default=values[item['key']], labels=labels, file=component['file']))
    seen = {'recommended', 'custom'}
    for preset in presets['presets']:
        # "disabled" turns off recommended components; optional "enabled" turns on components that are off by default.
        require({'key', 'labels', 'disabled'} <= set(preset) <= {'key', 'labels', 'disabled', 'enabled'} and
                isinstance(preset['key'], str) and
                re.fullmatch(r'[a-z][a-z0-9_]*', preset['key']) is not None and preset['key'] not in seen,
                'Invalid or duplicate preset key')
        seen.add(preset['key'])
        require(isinstance(preset['disabled'], list) and len(set(preset['disabled'])) == len(preset['disabled']) and
                set(preset['disabled']).issubset(by_name), 'Unknown or duplicate disabled preset component')
        preset.setdefault('enabled', [])
        require(isinstance(preset['enabled'], list) and len(set(preset['enabled'])) == len(preset['enabled']) and
                set(preset['enabled']).issubset(by_name) and not set(preset['enabled']) & set(preset['disabled']),
                'Unknown, duplicate or conflicting enabled preset component')
        require({'en', 'pt'} <= set(preset['labels']) <= set(languages),
                'Preset requires en and pt labels in installer languages')
        for value in preset['labels'].values():
            text(value)
    return components, extras, presets['presets']


def partial_choices(components, options, selected, selected_options):
    """Reference contract for the generated Pascal writer: differences only."""
    require(set(selected).issubset({entry['key'] for entry in components}), 'Unknown selected component')
    option_keys = {entry['component'] + '_' + entry['key'] for entry in options}
    require(set(selected_options).issubset(option_keys), 'Unknown selected option')
    documents = {}
    for entry in components:
        value = entry['key'] in selected
        if value != entry['default']:
            documents.setdefault(entry['file'], {})['enabled'] = value
    for entry in options:
        value = entry['component'] + '_' + entry['key'] in selected_options
        if value != entry['default']:
            documents.setdefault(entry['file'], {})[entry['key']] = value
    return documents


def case_function(name, values, kind='String'):
    fallback = "''" if kind == 'String' else 'False'
    lines = [f'function {name}(Index: Integer): {kind};', 'begin', f'  Result := {fallback};', '  case Index of']
    for index, value in enumerate(values):
        lines.append(f'    {index}: Result := {literal(value) if kind == "String" else str(value)};')
    return '\n'.join(lines + ['  end;', 'end;', ''])


def generate_components(root=ROOT, output=None):
    """Write the installer input into an explicit folder, normally a run workspace; there is no global default."""
    root = Path(root)
    require(output is not None, 'The installer input needs an explicit output folder, such as a run workspace')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    components, options, presets = definitions(root)
    wizard = installer_messages(root)
    messages = []
    def message(key, values):
        # The unprefixed entry is Inno's fallback for languages without their own text.
        messages.append(key + '=' + text(values['en']))
        for lang, value in values.items():
            messages.append(lang + '.' + key + '=' + text(value))
        return '{cm:' + key + '}'
    for key, values in wizard['custom_messages'].items():
        message(key, values)
    languages = ['[Languages]'] + ['Name: ' + quoted(code) + '; MessagesFile: ' + quoted(path)
                                   for code, path in wizard['languages'].items()]
    overrides = ['[Messages]'] + [lang + '.' + key + '=' + text(value)
                                  for key, values in wizard['messages'].items() for lang, value in values.items()]
    (output / 'languages.generated.iss').write_text('\n'.join(languages + [''] + overrides) + '\n',
                                                    encoding='utf-8-sig')
    types = ['[Types]', 'Name: "recommended"; Description: "{cm:Recommended}"',
             'Name: "custom"; Description: "{cm:Customized}"; Flags: iscustom']
    for preset in presets:
        types.append('Name: ' + quoted(preset['key']) + '; Description: ' + quoted(message('preset_' + preset['key'], preset['labels'])))
    rows, choices, preview_keys, preview_descriptions = [], [], [], []
    groups = sorted({entry['group'] for entry in components})
    all_types = ' '.join(['recommended'] + [entry['key'] for entry in presets])
    for group in groups:
        members = [entry for entry in components if entry['group'] == group]
        rows.append('Name: ' + quoted(group) + '; Description: ' + quoted(message('group_' + group, members[0]['group_labels'])) +
                    '; Types: ' + all_types + '; Flags: fixed')
        preview_keys.append('')
        preview_descriptions.append('group_' + group)
        for entry in members:
            name = group + '\\' + entry['key']
            if entry['default']:
                included = ['recommended'] + [preset['key'] for preset in presets
                                              if entry['key'] not in preset['disabled']]
            else:
                included = [preset['key'] for preset in presets if entry['key'] in preset['enabled']]
            row = 'Name: ' + quoted(name) + '; Description: ' + quoted(message('component_' + entry['key'], entry['labels']))
            if included:
                row += '; Types: ' + ' '.join(included)
            rows.append(row)
            preview_keys.append(entry['key'])
            preview_descriptions.append('description_' + entry['key'])
            message('description_' + entry['key'], entry['descriptions'])
            choices.append(dict(name=name, file=entry['file'], key='enabled', default=entry['default'], task=False))
    tasks = []
    for entry in options:
        name = entry['component'] + '_' + entry['key']
        row = 'Name: ' + quoted(name) + '; Description: ' + quoted(message('option_' + name, entry['labels']))
        row += '; GroupDescription: ' + quoted('{cm:component_' + entry['component'] + '}')
        if not entry['default']:
            row += '; Flags: unchecked'
        tasks.append(row)
        choices.append(dict(name=name, file=entry['file'], key=entry['key'], default=entry['default'], task=True))
    code = ['[Code]', f'const ChoiceCount = {len(choices)};', f'const PreviewCount = {len(preview_keys)};']
    for name, field, kind in [('ChoiceName', 'name', 'String'), ('ChoiceFile', 'file', 'String'),
                              ('ChoiceKey', 'key', 'String'),
                               ('ChoiceDefault', 'default', 'Boolean'), ('ChoiceIsTask', 'task', 'Boolean')]:
        values = [entry[field].replace('/', '\\') if field == 'file' else entry[field] for entry in choices]
        code.append(case_function(name, values, kind))
    previews = []
    preview_files = []
    for key in preview_keys:
        path = root / 'installer/setup/assets/previews' / (key + '.png')
        name = 'preview_' + key + '.png' if key and path.is_file() else ''
        previews.append(name)
        if name:
            preview_files.append('Source: ' + quoted(str(path.resolve())) + '; DestName: ' + quoted(name) + '; Flags: dontcopy')
    code.append(case_function('PreviewFile', previews))
    code.append(case_function('PreviewMessage', preview_descriptions))
    code.append('''function ChoiceSelected(Index: Integer): Boolean;
begin
  if ChoiceIsTask(Index) then Result := WizardIsTaskSelected(ChoiceName(Index))
  else Result := WizardIsComponentSelected(ChoiceName(Index));
end;
''')
    sections = ['; Generated; edit JSON/defaults/i18n, never this file.', '\n'.join(types),
                '[Components]\n' + '\n'.join(rows),
                '[Tasks]\n' + '\n'.join(tasks), '[CustomMessages]\n' + '\n'.join(messages), '\n'.join(code)]
    (output / 'components.generated.iss').write_text('\n\n'.join(sections) + '\n', encoding='utf-8-sig')
    (output / 'previews.generated.iss').write_text('[Files]\n' + '\n'.join(preview_files) + '\n', encoding='utf-8-sig')
    branding = ['[Setup]']
    for directive, stem, extensions in [('SetupIconFile', 'setup-icon', ('.ico',)),
                                        ('WizardImageFile', 'wizard-large', ('.bmp', '.png')),
                                        ('WizardSmallImageFile', 'wizard-small', ('.bmp', '.png')),
                                        ('WizardBackImageFile', 'wizard-back', ('.png', '.bmp'))]:
        for extension in extensions:
            path = root / 'installer/setup/assets/branding' / (stem + extension)
            if path.is_file():
                branding.append(directive + '=' + str(path.resolve()))
                if directive == 'WizardBackImageFile':
                    # Keep page text readable over the game artwork.
                    branding.append('WizardBackImageOpacity=' + str(BACK_IMAGE_OPACITY))
                break
    (output / 'branding.generated.iss').write_text('\n'.join(branding) + '\n', encoding='utf-8-sig')
    (output / 'choices.generated.json').write_text(json.dumps(dict(components=components, options=options,
                                                                   presets=presets),
                                                            ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return components, options, presets


RUN_ID = re.compile(r'\d{8}T\d{6}Z-[0-9a-f]{8}')


def run_directory(artifacts, root=ROOT, explicit=None):
    """The compiler run that produced these artifacts: the explicit one, or the run the build report names.
    The run's WOTMOD must be byte-identical to the candidate's, so the installer never wraps another build."""
    artifacts = Path(artifacts).resolve()
    if explicit is not None:
        run = Path(explicit).resolve()
    else:
        run_id = read_json(artifacts / 'build-report.json').get('run_id')
        require(isinstance(run_id, str) and RUN_ID.fullmatch(run_id),
                'The build report names no compiler run; pass --run <run directory> explicitly')
        run = Path(root).resolve() / 'build/runs' / run_id
    runs = (Path(root).resolve() / 'build/runs')
    require(run.is_dir() and run.parent == runs, 'The installer run must be a directory directly under build/runs')
    require(read_json(run / 'evidence/build-report.json').get('run_id') == run.name,
            'Run metadata does not match its directory')
    manifest = read_json(artifacts / 'release.json')
    require(sha(run / 'output/driftkings.wotmod') == manifest['sha256'],
            'The run WOTMOD is not the candidate package; the installer must wrap the same bytes')
    return run


def installer_workspace(run):
    """Intermediates, Inno Setup output, compilation log and verification evidence of one run; nothing global."""
    run = Path(run)
    layout = dict(input=run / 'workspace/installer/input', output=run / 'workspace/installer/output',
                  logs=run / 'evidence/installer/logs', evidence=run / 'evidence/installer')
    for folder in layout.values():
        folder.mkdir(parents=True, exist_ok=True)
    return layout


def prepare_payload(root, artifacts, output, setup_output=None):
    artifacts = Path(artifacts).resolve()
    require(not artifacts.is_dir() or (artifacts / 'release.json').is_file(),
            'Development packages have no distribution and cannot be installed; build a release')
    manifest = read_json(artifacts / 'release.json')
    report = read_json(artifacts / 'build-report.json')
    require(report['status'] == 'success' and manifest['version'] == report['version'],
            'Invalid installer build artifacts')
    inventory = verify_modpack(artifacts, manifest, read_json(artifacts / 'modpack.json'))
    config = read_json(root / 'build_data/build_config.json')
    require(manifest['gameVersion'] == config['game']['version'],
            'Installer artifacts target another client')
    realms = production_realms(root, config, report)
    # Choices must correspond to the actual defaults already present in this build.
    defaults = root / config['defaults']['source_root']
    for path in defaults.rglob('*.json'):
        relative = path.relative_to(root).as_posix()
        require(report['inputs'].get(relative) == hashlib.sha256(path.read_bytes()).hexdigest(),
                'Rebuild changed defaults before installer: ' + relative)
    with zipfile.ZipFile(artifacts / 'driftkings.wotmod') as archive:
        helper = archive.read('res/gui/driftkings/updater/Driftkings.UpdateInstaller.exe')
    migration = output / 'Driftkings.UpdateInstaller.exe'
    migration.write_bytes(helper)
    rows = ['[Files]', 'Source: ' + quoted(str(migration)) + '; Flags: dontcopy']
    conflicts = ['function ExistingDependenciesError: String;', 'begin', "  Result := '';", '  try']
    verification = ['procedure VerifyInstalledPayload;', 'begin']
    for entry in inventory.files:
        if entry['kind'] not in ('code', 'dependency'):
            continue
        source = artifacts / ('dependencies/' if entry['kind'] == 'dependency' else '') / Path(entry['path']).name
        require(source.is_file() and source.stat().st_size == entry['size'] and
                hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256'],
                'Invalid installer payload: ' + str(source))
        destination = '{app}\\' + entry['path'].rsplit('/', 1)[0].replace('/', '\\')
        flags = 'ignoreversion' + (' uninsneveruninstall onlyifdoesntexist' if entry['kind'] == 'dependency' else '')
        rows.append('Source: ' + quoted(str(source)) + '; DestDir: ' + quoted(destination) + '; Flags: ' + flags)
        target = "ExpandConstant(" + literal('{app}\\' + entry['path'].replace('/', '\\')) + ')'
        check = 'GetSHA256OfFile(' + target + ') <> ' + literal(entry['sha256'])
        if entry['kind'] == 'dependency':
            conflicts.extend(['    if FileExists(' + target + ') then', '      if ' + check + ' then begin',
                              '        Result := ' + literal('Dependency differs from the verified modpack: ' + entry['path']) + ';',
                              '        Exit;', '      end;'])
        verification.extend(['  if ' + check + ' then',
                             '    RaiseException(' + literal('Installed payload hash mismatch: ' + entry['path']) + ');'])
    conflicts.extend(['  except', '    Result := GetExceptionMessage;', '  end;', 'end;'])
    verification.append('end;')
    (output / 'payload.generated.iss').write_text('\n'.join(rows + ['[Code]'] + conflicts + verification) + '\n',
                                                  encoding='utf-8-sig')
    # "What's new" page: the signed manifest's changelog, not a separately edited copy.
    notes = ['Driftkings %s - World of Tanks %s' % (manifest['version'], manifest['gameVersion'])]
    for line in manifest.get('changelog', []):
        notes += ['', '• ' + line]
    (output / 'changelog.generated.txt').write_bytes(('\r\n'.join(notes) + '\r\n').encode('utf-8-sig'))
    metadata = dict(RepoRoot=str(root.resolve()), BuildVersion=manifest['version'], GameVersion=manifest['gameVersion'],
                    GameRealm=report['realm'], SupportedRealms='|' + '|'.join(realms) + '|',
                    SupportedRealmsText=', '.join(realms),
                    InstallerOutput=str(Path(setup_output or output / 'setup').resolve()))
    (output / 'metadata.generated.iss').write_text('\n'.join('#define ' + key + ' ' + quoted(value) for key,
                                                             value in metadata.items()) + '\n', encoding='utf-8-sig')


def setup_archive_name(manifest):
    return 'Driftkings-%s-WoT-%s-Setup.zip' % (manifest['version'], manifest['gameVersion'])


def build_setup_archive(setup, archive):
    """The WGMods archive: the final Setup executable and nothing else, with deterministic metadata."""
    setup = Path(setup)
    zip_entries(archive, {setup.name: setup.read_bytes()}, zipfile.ZIP_DEFLATED)
    return archive


def verify_setup_archive(archive, setup):
    """The archive holds exactly one entry, the same executable byte for byte, under a safe name."""
    setup = Path(setup)
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        require(names == [setup.name], 'The Setup archive must contain exactly the Setup executable: %r' % names)
        relative_path(names[0])
        infos = bundle.infolist()
        require(infos[0].file_size == setup.stat().st_size, 'Setup archive entry size differs from the executable')
        extracted = bundle.read(names[0])
    require(hashlib.sha256(extracted).hexdigest() == sha(setup),
            'The executable inside the Setup archive is not the standalone executable')
    return sha(setup)


def attach_installer(artifacts, installer):
    """Add the compiled setup and its WGMods archive to the staging inventory, before the candidate is frozen."""
    artifacts, installer = Path(artifacts).resolve(), Path(installer).resolve()
    require_mutable(artifacts)
    report = read_json(artifacts / 'build-report.json')
    manifest = read_json(artifacts / 'release.json')
    require_signable(report)  # eligibility only; publication is decided by publish_release.py
    require(report['version'] == manifest['version'] and report['gameVersion'] == manifest['gameVersion'],
            'Installer release version mismatch')
    expected = 'Driftkings-%s-WoT-%s-Setup.exe' % (manifest['version'], manifest['gameVersion'])
    require(installer.name == expected, 'Installer filename does not match the release')
    with installer.open('rb') as stream:
        require(stream.read(2) == b'MZ', 'Installer is not a Windows executable')
    target = artifacts / expected
    if installer != target:
        shutil.copy2(installer, target)
    archive = artifacts / setup_archive_name(manifest)
    build_setup_archive(target, archive)
    verify_setup_archive(archive, target)
    report['artifacts'][expected] = dict(size=target.stat().st_size, sha256=sha(target))
    report['artifacts'][archive.name] = dict(size=archive.stat().st_size, sha256=sha(archive))
    report['setupArchive'] = archive.name
    write_json(artifacts / 'build-report.json', report)
    names = sorted(set(report['artifacts']) | {'build-report.json'})
    (artifacts / 'SHA256SUMS.txt').write_bytes((''.join('%s  %s\n' % (sha(artifacts / name), name)
                                                     for name in names)).encode('utf-8'))
    return target


def compile_installer(root, workspace, iscc=None):
    """Run Inno Setup with its log in the run evidence; exactly one setup must come out of the run workspace."""
    compiler = iscc or shutil.which('ISCC.exe') or 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe'
    log = workspace['logs'] / 'iscc.log'
    with log.open('wb') as stream:
        result = subprocess.run([compiler, '/DInputDir=' + str(workspace['input']),
                                 str(Path(root) / 'installer/setup/driftkings.iss')],
                                stdout=stream, stderr=subprocess.STDOUT)
    require(result.returncode == 0, 'Inno Setup failed; see ' + str(log))
    setups = sorted(workspace['output'].glob('*.exe'))
    require(len(setups) == 1, 'Inno Setup must produce exactly one installer in the run workspace')
    return setups[0]


def record_installer_evidence(workspace, setup, artifacts, run):
    """Verification evidence of the compiled setup: its identity, the candidate it wraps and the run it came from."""
    manifest = read_json(Path(artifacts) / 'release.json')
    data = dict(schema=1, setup=setup.name, sha256=sha(setup), size=setup.stat().st_size, run_id=Path(run).name,
                candidateWotmodSha256=manifest['sha256'], candidateVersion=manifest['version'], frozen=False)
    write_json(workspace['evidence'] / 'verification.json', data)
    return data


def release_directory(path):
    """Accept a completed release directory, or a run directory whose output/ holds the release."""
    path = Path(path).resolve()
    if (path / 'output' / 'release.json').is_file():
        return path / 'output'
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path,
                        help='Release directory (a run output or a candidate folder); defines the installer')
    parser.add_argument('--run', type=Path,
                        help='Compiler run that owns the installer workspace (default: the run named by the build report)')
    parser.add_argument('--compile', action='store_true',
                        help='Compile locally with Inno Setup 6.7.1+ into the run workspace; never install or publish')
    parser.add_argument('--iscc', help='Inno compiler path')
    parser.add_argument('--attach-to-release', action='store_true',
                        help='Include the compiled installer in the candidate inventory and checksums; refused once frozen')
    args = parser.parse_args()
    if args.attach_to_release and not args.compile:
        parser.error('--attach-to-release requires --compile')
    artifacts = release_directory(args.artifacts)
    try:
        plan = build_plan(ROOT)
        media = validate_assets(ROOT, plan['assets'])
        for warning in media['warnings']:
            print('WARNING: ' + warning)
        run = run_directory(artifacts, ROOT, args.run)
        workspace = installer_workspace(run)
        components, options, presets = generate_components(ROOT, workspace['input'])
        prepare_payload(ROOT, artifacts, workspace['input'], setup_output=workspace['output'])
        print('Installer input: %d components, %d options, %d presets; %s' % (len(components), len(options),
                                                                              len(presets), workspace['input']))
        if args.compile:
            setup = compile_installer(ROOT, workspace, args.iscc)
            evidence = record_installer_evidence(workspace, setup, artifacts, run)
            print('Installer built in the run workspace: %s (sha256 %s)' % (setup, evidence['sha256']))
            if args.attach_to_release:
                print('Release installer: ' + str(attach_installer(artifacts, setup)))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, 'Installer build failed: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
