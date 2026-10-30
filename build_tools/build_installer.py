"""Generate an Inno Setup wizard that changes JSON choices, never its payload."""
import argparse
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
from build_tools.validate_locales import catalog
from build_tools.validate_build_data import build_plan, read_json, require, supported_realms
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
        require({'en', 'pt'} <= set(preset['labels']) <= set(languages), 'Preset requires en and pt labels in installer languages')
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
    root = Path(root)
    output = Path(output) if output else root / 'build/installer_input'
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
    (output / 'languages.generated.iss').write_text('\n'.join(languages + [''] + overrides) + '\n', encoding='utf-8-sig')
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
                included = ['recommended'] + [preset['key'] for preset in presets if entry['key'] not in preset['disabled']]
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
    for name, field, kind in [('ChoiceName', 'name', 'String'), ('ChoiceFile', 'file', 'String'), ('ChoiceKey', 'key', 'String'),
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
    sections = ['; Generated; edit JSON/defaults/i18n, never this file.', '\n'.join(types), '[Components]\n' + '\n'.join(rows),
                '[Tasks]\n' + '\n'.join(tasks), '[CustomMessages]\n' + '\n'.join(messages), '\n'.join(code)]
    (output / 'components.generated.iss').write_text('\n\n'.join(sections) + '\n', encoding='utf-8-sig')
    (output / 'previews.generated.iss').write_text('[Files]\n' + '\n'.join(preview_files) + '\n', encoding='utf-8-sig')
    branding = ['[Setup]']
    for directive, stem, extensions in [('SetupIconFile', 'setup-icon', ('.ico',)), ('WizardImageFile', 'wizard-large', ('.bmp', '.png')),
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
    (output / 'choices.generated.json').write_text(json.dumps(dict(components=components, options=options, presets=presets),
                                                            ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return components, options, presets


def prepare_payload(root, artifacts, output):
    artifacts = Path(artifacts).resolve()
    manifest = read_json(artifacts / 'release.json')
    report = read_json(artifacts / 'build-report.json')
    require(report['status'] == 'success' and manifest['version'] == report['version'], 'Invalid installer build artifacts')
    inventory = verify_modpack(artifacts, manifest, read_json(artifacts / 'modpack.json'))
    config = read_json(root / 'build_data/build_config.json')
    require(manifest['gameVersion'] == config['game']['version'] and report['realm'] in supported_realms(config),
            'Installer artifacts target another client')
    # Choices must correspond to the actual defaults already present in this build.
    defaults = root / config['defaults']['source_root']
    for path in defaults.rglob('*.json'):
        relative = path.relative_to(root).as_posix()
        require(report['inputs'].get(relative) == hashlib.sha256(path.read_bytes()).hexdigest(), 'Rebuild changed defaults before installer: ' + relative)
    rows = ['[Files]']
    conflicts = ['function ExistingDependenciesError: String;', 'begin', "  Result := '';", '  try']
    verification = ['procedure VerifyInstalledPayload;', 'begin']
    for entry in inventory.files:
        if entry['kind'] not in ('code', 'dependency'):
            continue
        source = artifacts / ('dependencies/' if entry['kind'] == 'dependency' else '') / Path(entry['path']).name
        require(source.is_file() and source.stat().st_size == entry['size'] and
                hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256'], 'Invalid installer payload: ' + str(source))
        destination = '{app}\\' + entry['path'].rsplit('/', 1)[0].replace('/', '\\')
        flags = 'ignoreversion' + (' uninsneveruninstall onlyifdoesntexist' if entry['kind'] == 'dependency' else '')
        rows.append('Source: ' + quoted(str(source)) + '; DestDir: ' + quoted(destination) + '; Flags: ' + flags)
        target = "ExpandConstant(" + literal('{app}\\' + entry['path'].replace('/', '\\')) + ')'
        check = 'GetSHA256OfFile(' + target + ') <> ' + literal(entry['sha256'])
        if entry['kind'] == 'dependency':
            conflicts.extend(['    if FileExists(' + target + ') then', '      if ' + check + ' then begin',
                              '        Result := ' + literal('Dependency differs from the verified modpack: ' + entry['path']) + ';',
                              '        Exit;', '      end;'])
        verification.extend(['  if ' + check + ' then', '    RaiseException(' + literal('Installed payload hash mismatch: ' + entry['path']) + ');'])
    conflicts.extend(['  except', '    Result := GetExceptionMessage;', '  end;', 'end;'])
    verification.append('end;')
    (output / 'payload.generated.iss').write_text('\n'.join(rows + ['[Code]'] + conflicts + verification) + '\n', encoding='utf-8-sig')
    # "What's new" page: the signed manifest's changelog, not a separately edited copy.
    notes = ['Driftkings %s - World of Tanks %s' % (manifest['version'], manifest['gameVersion'])]
    for line in manifest.get('changelog', []):
        notes += ['', '• ' + line]
    (output / 'changelog.generated.txt').write_bytes(('\r\n'.join(notes) + '\r\n').encode('utf-8-sig'))
    realms = supported_realms(config)
    metadata = dict(RepoRoot=str(root.resolve()), BuildVersion=manifest['version'], GameVersion=manifest['gameVersion'],
                    GameRealm=report['realm'], SupportedRealms='|' + '|'.join(realms) + '|',
                    SupportedRealmsText=', '.join(realms), InstallerOutput=str((root / 'build/installer').resolve()))
    (output / 'metadata.generated.iss').write_text('\n'.join('#define ' + key + ' ' + quoted(value) for key, value in metadata.items()) + '\n', encoding='utf-8-sig')


def attach_installer(artifacts, installer):
    """Add a compiled setup to the verified release inventory and checksums."""
    from build_tools.package_tools import sha, write_json
    artifacts, installer = Path(artifacts).resolve(), Path(installer).resolve()
    report = read_json(artifacts / 'build-report.json')
    manifest = read_json(artifacts / 'release.json')
    require(report.get('status') == 'success' and report.get('mode') == 'release' and report.get('publishable'),
            'Installer attachment requires a completed release build')
    require(report['version'] == manifest['version'] and report['gameVersion'] == manifest['gameVersion'],
            'Installer release version mismatch')
    expected = 'Driftkings-%s-WoT-%s-Setup.exe' % (manifest['version'], manifest['gameVersion'])
    require(installer.name == expected, 'Installer filename does not match the release')
    with installer.open('rb') as stream:
        require(stream.read(2) == b'MZ', 'Installer is not a Windows executable')
    target = artifacts / expected
    if installer != target:
        shutil.copy2(installer, target)
    report['artifacts'][expected] = dict(size=target.stat().st_size, sha256=sha(target))
    write_json(artifacts / 'build-report.json', report)
    names = sorted(set(report['artifacts']) | {'build-report.json'})
    (artifacts / 'SHA256SUMS.txt').write_bytes((''.join('%s  %s\n' % (sha(artifacts / name), name)
                                                     for name in names)).encode('utf-8'))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, help='Completed compiler output directory (debug or release)')
    parser.add_argument('--compile', action='store_true', help='Compile locally with Inno Setup 6.7.1+; never install or publish')
    parser.add_argument('--iscc', help='Inno compiler path')
    parser.add_argument('--attach-to-release', action='store_true', help='Include the compiled installer in the release inventory and checksums')
    args = parser.parse_args()
    if args.attach_to_release and not args.compile:
        parser.error('--attach-to-release requires --compile')
    if args.compile and not args.artifacts:
        parser.error('--compile requires --artifacts')
    try:
        plan = build_plan(ROOT)
        media = validate_assets(ROOT, plan['assets'])
        for warning in media['warnings']:
            print('WARNING: ' + warning)
        output = ROOT / 'build/installer_input'
        components, options, presets = generate_components(ROOT, output)
        if args.artifacts:
            prepare_payload(ROOT, args.artifacts, output)
        if args.compile:
            compiler = args.iscc or shutil.which('ISCC.exe') or 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe'
            subprocess.run([compiler, '/DInputDir=' + str(output), str(ROOT / 'installer/setup/driftkings.iss')], check=True)
            if args.attach_to_release:
                manifest = read_json(args.artifacts / 'release.json')
                name = 'Driftkings-%s-WoT-%s-Setup.exe' % (manifest['version'], manifest['gameVersion'])
                print('Release installer: ' + str(attach_installer(args.artifacts, ROOT / 'build/installer' / name)))
        print('Installer input: %d components, %d options, %d presets; %s' % (len(components), len(options), len(presets), output))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, 'Installer build failed: ' + str(error) + '\n')


if __name__ == '__main__':
    main()