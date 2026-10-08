"""Build the unified package directly from compiled files and enabled manifests."""
import ast
import json
import re
import sys
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'res/scripts/client/gui/mods/'
TARGET = 'res/scripts/client/Driftkings/'
COMPONENT_PATHS = tuple(TARGET + scope + '/' for scope in ('components', 'battle', 'lobby'))


def package_version(root=ROOT):
    tree = ast.parse((root / 'source/scripts/client/Driftkings/__init__.py').read_text(encoding='utf-8-sig'))
    values = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'VERSION' for target in node.targets)]
    if len(values) != 1 or not isinstance(values[0], str) or not re.fullmatch(r'\d+\.\d+\.\d+', values[0]):
        raise ValueError('Declare one VERSION in Driftkings/__init__.py (major.minor.patch)')
    return values[0]


def manifest_files(config, root):
    for destination, relative in sorted(config.get('files', {}).items()):
        if destination.endswith('/**'):
            if not relative.endswith('/**'):
                raise ValueError('Recursive resource must map to a directory: ' + destination)
            folder = root / relative[:-3]
            files = sorted(path for path in folder.rglob('*') if path.is_file())
            if not folder.is_dir() or not files:
                raise ValueError('Missing or empty resource directory: ' + str(folder))
            for path in files:
                yield destination[:-3] + '/' + path.relative_to(folder).as_posix(), path
        else:
            path = root / relative
            if not path.is_file():
                raise ValueError('Missing resource: ' + str(path))
            yield destination, path



def validate_dependency_resources(entries, directory):
    """Mirror the client conflict check before publishing a local package."""
    resources = {name.lower(): data for name, data in entries.items() if name.lower().startswith('res/')}
    owners = {name: 'Driftkings.wotmod' for name in resources}
    for package in sorted(directory.glob('*.wotmod')):
        with zipfile.ZipFile(package) as archive:
            for name in archive.namelist():
                key = name.lower()
                if name.endswith('/') or not key.startswith('res/'):
                    continue
                data = archive.read(name)
                if key in resources and resources[key] != data:
                    raise ValueError('Package resource conflict: %s <> %s: %s' % (owners[key], package.name, name))
                resources[key] = data
                owners[key] = package.name


def validate_owned_bytecode_source(name, root=ROOT):
    if name.startswith(TARGET) and name.endswith('.pyc'):
        source = (root / 'source' / name[len('res/'):]).with_suffix('.py')
        if not source.is_file():
            raise ValueError('Packaged module has no source: ' + name)


def build():
    entries, modules, sources = {}, [], []

    def add(name, content):
        validate_owned_bytecode_source(name)
        if name.endswith('.pyc') and content[:4] != b'\x03\xf3\x0d\x0a':
            raise ValueError('Expected Python 2.7 bytecode: ' + name)
        if name in entries and entries[name] != content:
            raise ValueError('Conflicting resource: ' + name)
        entries[name] = content

    for manifest in sorted((ROOT / 'build_data/components').glob('*.json')):
        config = json.loads(manifest.read_text(encoding='utf-8-sig'))
        if not config.get('enabled'):
            continue
        for name in config.get('files', {}):
            if name.startswith(COMPONENT_PATHS) and name.endswith('.pyc') and Path(name).stem != '__init__':
                source = (ROOT / 'source' / name[len('res/'):]).with_suffix('.py')
                if not source.is_file():
                    raise ValueError('Enabled component has no source: ' + str(source))
        sources.append(manifest.relative_to(ROOT).as_posix())
        for name, path in manifest_files(config, ROOT):
            if name == 'meta.xml':
                continue
            if name == 'LICENSE':
                name = 'licenses/' + manifest.stem + '.txt'
            if name.startswith(PREFIX + 'mod_'):
                raise ValueError('Legacy game entry point in component manifest: ' + name)
            if name.startswith(COMPONENT_PATHS) and name.endswith('.pyc') and Path(name).stem != '__init__':
                basename = name[len(TARGET):]
                if basename.count('/') != 1 or Path(basename).name.startswith('mod_'):
                    raise ValueError('Invalid internal component: ' + name)
                modules.append(basename[:-4].replace('/', '.'))
            add(name, path.read_bytes())
    declared = ast.literal_eval((ROOT / 'source/scripts/client/Driftkings/component_list.py').read_text().split('COMPONENTS = ', 1)[1])
    if sorted(modules) != sorted(declared):
        raise ValueError('Component list differs from enabled manifests; regenerate before compiling')
    infrastructure = [Path('Driftkings/__init__.py'), Path('Driftkings/_constants.py'), Path('Driftkings/component_list.py'),
                      Path('Driftkings/components/__init__.py'), Path('Driftkings/battle/__init__.py'),
                      Path('Driftkings/lobby/__init__.py'), Path('gui/mods/mod_Driftkings.py')]
    for scope in ('core', 'views', 'meta', 'settings', 'i18n'):
        infrastructure.extend(path.relative_to(ROOT / 'source/scripts/client')
                              for path in sorted((ROOT / 'source/scripts/client/Driftkings' / scope).rglob('*.py')))
    for source in infrastructure:
        relative = source.with_suffix('.pyc').as_posix()
        content = (ROOT / 'build/scripts/client' / relative).read_bytes()
        if content[:4] != b'\x03\xf3\x0d\x0a': raise ValueError('Expected Python 2.7 bytecode: ' + relative)
        add('res/scripts/client/' + relative, content)
    bank = ROOT / 'res/sound_bank_wwise/SixthSense/GeneratedSoundBanks/Windows/driftkings_sixthsense.bnk'
    name = 'res/audioww/driftkings_sixthsense.bnk'
    if bank.is_file():
        add(name, bank.read_bytes())
    else:
        add(name, (ROOT / 'res/audioww/driftkings_sixthsense.bnk').read_bytes())
    add('res/gui/flash/DriftkingsBattle.swf', (ROOT / 'res/flash/battle/DriftkingsBattle.swf').read_bytes())
    version = package_version()
    add('meta.xml', ('<root><id>driftkings.unified</id><version>%s</version><name>Driftkings</name><description>Unified laboratory build</description></root>' % version).encode('utf-8'))
    validate_dependency_resources(entries, ROOT / 'res/wotmods')
    folder = ROOT / 'build/unified'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / 'Driftkings.wotmod'
    temporary = folder / 'Driftkings.wotmod.tmp'
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(entries.items()): archive.writestr(name, content)
    with zipfile.ZipFile(temporary) as archive:
        assert archive.testzip() is None
        assert [n for n in archive.namelist() if n.startswith(PREFIX + 'mod_')] == [PREFIX + 'mod_Driftkings.pyc']
    temporary.replace(target)
    (folder / 'components.json').write_text(json.dumps({'version': version, 'modules': sorted(modules), 'source_manifests': sources}, indent=2))
    print('%s: %d components, %d entries' % (target, len(modules), len(entries)))


def prepare():
    modules = []
    for path in sorted((ROOT / 'build_data/components').glob('*.json')):
        config = json.loads(path.read_text(encoding='utf-8-sig'))
        if config.get('enabled'):
            modules.extend(name[len(TARGET):-4].replace('/', '.') for name in config.get('files', {}) if name.startswith(COMPONENT_PATHS) and name.endswith('.pyc') and Path(name).stem != '__init__')
    target = ROOT / 'source/scripts/client/Driftkings/component_list.py'
    content = '# Generated from enabled package manifests.\nCOMPONENTS = ' + repr(tuple(sorted(modules))) + '\n'
    if not target.exists() or target.read_text() != content:
        target.write_text(content)
    print('Prepared %d components' % len(modules))


if __name__ == '__main__':
    if '--prepare' in sys.argv: prepare()
    else: build()
