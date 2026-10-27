"""Generate and validate UI contracts without importing the game runtime."""
import argparse
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'mod/res/scripts/client/driftkings/interface_catalog.py'
AS3 = 'flash_source/battle/src/driftkings/battle/factory/componentcatalog.as'
BOOTSTRAP = 'mod/res/gui/gameface/mods/driftkings/shared/bootstrap.js'
START, END = '    /* GENERATED CATALOG START */', '    /* GENERATED CATALOG END */'
PREFIX = 'coui://gui/gameface/mods/driftkings/'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_catalog(root=ROOT):
    tree = ast.parse((Path(root) / SOURCE).read_text(encoding='utf-8'))
    return {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}


def installer_catalog(root=ROOT):
    """Installer choices come from canonical JSON and the same UI translations."""
    try:
        from .components import read_components
        from .validate_locales import catalog
    except ImportError:
        from components import read_components
        from validate_locales import catalog
    root = Path(root)
    config = json.loads((root / 'build_data/build_config.json').read_text(encoding='utf-8'))
    manifests = {item['id']: item for item in read_components(root, config['components']['source'])}
    catalogs = {lang: catalog(root / ('mod/res/mods/driftkings/text/' + lang + '.yml'))
                for lang in ('en', 'pt')}
    choices = []
    for path in sorted((root / config['defaults']['source_root'] / 'default').glob('*.json')):
        values = json.loads(path.read_text(encoding='utf-8'))
        if 'enabled' not in values:
            continue
        require(type(values['enabled']) is bool, 'Installer enabled must be boolean: ' + path.stem)
        spec = manifests.get(path.stem)
        require(spec is not None and spec['kind'] == 'feature' and spec['enabled'],
                'Installer section has no enabled feature: ' + path.stem)
        relative = 'default/' + path.name
        require(relative in spec['config_files'], 'Installer JSON not declared: ' + relative)
        prefix = spec['entrypoint'].split('.')[0]
        group = {'battle': 'battle', 'lobby': 'hangar'}.get(prefix, 'general')
        labels, descriptions, groups = {}, {}, {}
        for lang, document in catalogs.items():
            text = document['TEXT'].get(path.stem, {})
            label = text.get('UI_description')
            require(isinstance(label, str) and label.strip(), 'Missing installer label: ' + lang + '/' + path.stem)
            group_label = document['PANEL'].get('category.' + group)
            require(isinstance(group_label, str) and group_label.strip(), 'Missing installer group: ' + lang + '/' + group)
            labels[lang] = label
            descriptions[lang] = text.get('UI_tooltip') or label
            groups[lang] = group_label
        choices.append(dict(key=path.stem, file=relative, default=values['enabled'], group=group,
                            labels=labels, descriptions=descriptions, group_labels=groups))
    return choices


def asset_target(url):
    require(isinstance(url, str) and url.startswith(PREFIX), 'UI asset must belong to Driftkings: %r' % url)
    relative = url[len('coui://'):]
    require('\\' not in relative and ':' not in relative and all(part not in ('', '.', '..') for part in relative.split('/')),
            'Unsafe UI asset URL: ' + url)
    return 'res/' + relative


def outputs(root=ROOT):
    root = Path(root)
    catalog = read_catalog(root)
    flash, face = catalog['FLASH_COMPONENTS'], catalog['GAMEFACE']
    imports = '\n'.join('    import %s;' % name for name in sorted({spec['as3'] for spec in flash.values()}))
    methods = []
    for surface in ('battle', 'ratings'):
        entries = ['                %s:%s' % (alias, spec['as3'].rsplit('.', 1)[1])
                   for alias, spec in sorted(flash.items()) if surface in spec['surfaces']]
        methods.append('''        if (surface == "%s") return {
%s
            };''' % (surface, ',\n'.join(entries)))
    as3 = '''// Generated from driftkings/interface_catalog.py; regenerate with generate_ui_catalog.py --write.
package driftkings.battle.factory
{
%s

    public class componentcatalog
    {
        public static function classes(surface:String):Object
        {
%s
            return {};
        }
    }
}
''' % (imports, '\n'.join(methods))
    text = (root / BOOTSTRAP).read_text(encoding='utf-8')
    require(text.count(START) == text.count(END) == 1, 'Missing UI catalog generation markers')
    definitions = {name: {key: spec[key] for key in ('owner', 'styles', 'scripts')}
                   for name, spec in sorted(face.items()) if spec['owner'] is not None}
    generated = json.dumps(definitions, ensure_ascii=True, sort_keys=True, indent=4)
    block = START + '\n    var features = ' + generated.replace('\n', '\n    ') + ';\n'
    bootstrap = text[:text.index(START)] + block + text[text.index(END):]
    return {AS3: as3, BOOTSTRAP: bootstrap}


def validate(root=ROOT, plan=None):
    root = Path(root)
    data = read_catalog(root)
    flash, face = data['FLASH_COMPONENTS'], data['GAMEFACE']
    require(bool(flash) and bool(face), 'Empty UI catalog')
    constants = ast.parse((root / 'mod/res/scripts/client/driftkings/_constants.py').read_text(encoding='utf-8'))
    aliases = next(node for node in constants.body if isinstance(node, ast.ClassDef) and node.name == 'BATTLE_ALIASES')
    declared = {ast.literal_eval(node.value) for node in aliases.body if isinstance(node, ast.Assign)}
    require(set(flash) == declared, 'Flash catalog and BATTLE_ALIASES differ')
    defaults = ast.parse((root / 'mod/res/scripts/client/driftkings/settings/default_values.py').read_text(encoding='utf-8'))
    sections = set(next(ast.literal_eval(node.value) for node in defaults.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DEFAULTS' for t in node.targets))) | {'driftkings'}
    for alias, spec in flash.items():
        require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', alias) is not None, 'Invalid Flash alias: ' + alias)
        require(set(spec['surfaces']) <= {'battle', 'ratings'} and spec['surfaces'], 'Invalid Flash surface: ' + alias)
        require(spec['section'] is None or spec['section'] in sections, 'Unknown Flash section: ' + alias)
        as3_path = root / ('flash_source/battle/src/' + spec['as3'].replace('.', '/') + '.as')
        require(as3_path.is_file(), 'Missing Flash class: ' + str(as3_path))
        module, name = spec['python'].rsplit('.', 1)
        path = root / ('mod/res/scripts/client/' + module.replace('.', '/') + '.py')
        require(path.is_file(), 'Missing Python UI module: ' + str(path))
        tree = ast.parse(path.read_text(encoding='utf-8'))
        require(any(isinstance(node, ast.ClassDef) and node.name == name for node in tree.body), 'Missing Python view/controller: ' + spec['python'])
    meta_classes = set()
    for path in (root / 'mod/res/scripts/client/driftkings/flash/battle/meta').glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'FLASH_CLASS' for t in node.targets):
                meta_classes.add(ast.literal_eval(node.value))
    require(meta_classes == {spec['as3'] for spec in flash.values()}, 'DAAPI meta and Flash catalog differ')
    resources, resource_sources = {}, {}
    for path in (root / 'mod/res/gui/gen_resources').glob('*.json'):
        for entry in json.loads(path.read_text(encoding='utf-8')):
            key = entry['id'].removeprefix('R.').replace('.', '/')
            require(key not in resources, 'Duplicate R resource: ' + key)
            require(entry['type'] == 'Layout' and entry['parameters'] == {'entrance': 'main', 'impl': 'gameface'}, 'Invalid UI resource: ' + key)
            resources[key] = entry['path']
            resource_sources[key] = path.relative_to(root / 'mod').as_posix()
    require(set(resources) == {spec['resource'] for spec in face.values()}, 'R resources and Gameface catalog differ')
    require(len(set(resources.values())) == len(resources), 'Independent UI resources must have distinct layout paths')
    targets = {item['target'] for item in plan['assets']} if plan is not None else None
    owners = set()
    for name, spec in face.items():
        require(spec['section'] in sections, 'Unknown Gameface section: ' + name)
        require((root / ('mod/res/scripts/client/' + spec['python'].replace('.', '/') + '.py')).is_file(), 'Missing Gameface Python module: ' + name)
        if targets is not None:
            require(resource_sources[spec['resource']] in targets, 'R declaration is not packaged: ' + spec['resource'])
        require(resources[spec['resource']] == spec['layout'], 'Wrong layout for ' + name)
        require(len(spec['resource'].split('/')) == 4, 'Invalid R path: ' + name)
        require(len(set(spec['styles'] + spec['scripts'])) == len(spec['styles'] + spec['scripts']), 'Duplicate assets: ' + name)
        if spec['owner'] is not None:
            require(spec['owner'].startswith('__dk') and spec['owner'] not in owners, 'Invalid/duplicate JS owner: ' + name)
            owners.add(spec['owner'])
            require(spec['scripts'], 'Injected feature has no scripts: ' + name)
        for url in [spec['layout']] + spec['styles'] + spec['scripts']:
            target = asset_target(url)
            require((root / 'mod' / target).is_file(), 'Missing UI asset: ' + target)
            if targets is not None:
                require(target in targets, 'UI asset is not packaged: ' + target)
    if targets is not None:
        require('res/gui/flash/' + data['FLASH_LIBRARY'] in targets, 'Flash library is not packaged')
        require(BOOTSTRAP.removeprefix('mod/') in targets, 'UI bootstrap is not packaged')
    for relative, expected in outputs(root).items():
        require((root / relative).is_file() and (root / relative).read_text(encoding='utf-8') == expected,
                'Stale generated UI catalog: ' + relative + '; run python build_tools/generate_ui_catalog.py --write')
    return {'flash': len(flash), 'gameface': len(face), 'injected': len(owners)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        for relative, content in outputs().items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
    print('UI catalog valid: ' + json.dumps(validate(), sort_keys=True))


if __name__ == '__main__':
    main()
