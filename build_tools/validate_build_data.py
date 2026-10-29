"""Validate build inputs and resolve a package plan without compiling or deploying."""
import argparse
import ast
import fnmatch
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import zipfile

try:
    from .components import read_components
    from .validate_locales import validate_catalogs
    from .generate_defaults import check_generated as check_default_values, defaults_sha256
    from .generate_ui_catalog import validate as validate_ui_catalog
    from .validate_installer_assets import validate as validate_installer_assets
except ImportError:
    from components import read_components
    from validate_locales import validate_catalogs
    from generate_defaults import check_generated as check_default_values, defaults_sha256
    from generate_ui_catalog import validate as validate_ui_catalog
    from validate_installer_assets import validate as validate_installer_assets

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_KEYS = {'schema_version', 'id', 'kind', 'enabled', 'entrypoint', 'config_files', 'assets'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, '%s: duplicate key %s' % (path, key))
            result[key] = value
        return result
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs)


def relative_path(value):
    require(isinstance(value, str) and value and '\\' not in value and ':' not in value,
            'Expected a relative POSIX path: %r' % value)
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(p not in ('', '.', '..') for p in value.split('/')),
            'Unsafe path: %s' % value)
    return path


def input_path(root, value):
    relative_path(value)
    result = root / value
    require(result.resolve().is_relative_to(root.resolve()), 'Input escapes repository: %s' % value)
    return result


def expand_asset(root, asset, exclusions):
    require(set(asset) == {'source', 'target', 'generator'}, 'Invalid asset fields: %r' % asset)
    source, target = asset['source'], asset['target']
    relative_path(target)
    require(target == 'licence' or target.startswith('res/'), 'Invalid WOTMOD target: %s' % target)
    source_path = input_path(root, source)
    recursive = source.endswith('/**')
    require(recursive == target.endswith('/**'), 'Source/target glob mismatch: %s' % source)
    require('*' not in source[:-3] and '*' not in target[:-3] if recursive else '*' not in source + target,
            'Only a trailing /** is supported: %s' % source)
    if asset['generator'] is not None:
        require(not recursive, 'Generated assets must name one file')
        return [dict(asset)]
    base = input_path(root, source[:-3]) if recursive else source_path
    files = sorted(p for p in base.rglob('*') if p.is_file()) if recursive else [base]
    result = []
    for path in files:
        source_name = path.relative_to(root).as_posix()
        if any(fnmatch.fnmatchcase(source_name, pattern) for pattern in exclusions):
            continue
        require(path.is_file(), 'Missing asset: %s' % source_name)
        require(path.resolve().is_relative_to(root.resolve()), 'Asset escapes repository: %s' % path)
        destination = target[:-3] + '/' + path.relative_to(base).as_posix() if recursive else target
        result.append({'source': source_name, 'target': destination, 'generator': None})
    require(result, 'Empty asset selection: %s' % source)
    return result


def apply_patch_set(raw, patch):
    """Apply a version-pinned text patch in memory; refuse different game bundles."""
    require(hashlib.sha256(raw).hexdigest() == patch['source_sha256'], 'Unsupported carousel bundle hash')
    text = raw.decode('utf-8')
    for operation in patch['operations']:
        require(text.count(operation['find']) == operation['count'], 'Carousel patch occurrence mismatch')
        text = text.replace(operation['find'], operation['replace'])
    result = text.encode('utf-8')
    require(hashlib.sha256(result).hexdigest() == patch['output_sha256'], 'Carousel patch output hash mismatch')
    return result


def build_plan(root=ROOT, check_generated=False, check_game=False, check_component_list=True, game_root=None, check_defaults=True):
    root = Path(root).resolve()
    config = read_json(root / 'build_data/build_config.json')
    require(config['schema_version'] == 1, 'Unsupported build schema')
    require(config['python']['version'] == '2.7', 'WoT client requires Python 2.7 bytecode')
    require(config['python']['optimize'] == 0, 'Only Python optimize=0 is supported for the runtime contract')
    require(config['package']['name'] == 'driftkings.wotmod', 'Package filename must match the updater contract')
    require(config['package']['compression'] == 'stored', 'WOTMOD must use ZIP_STORED')
    require(config['defaults']['install_policy'] == 'missing_only' and config['defaults']['in_wotmod'] is False,
            'Defaults must be installed separately without overwriting user settings')
    input_path(root, config['package']['output'])
    input_path(root, config['python']['staging_root'])
    relative_path(config['python']['archive_root'])
    relative_path(config['defaults']['install_root'])
    python_root = input_path(root, config['python']['source_root'])
    manifest_path = input_path(root, config['components']['source'])
    defaults_root = input_path(root, config['defaults']['source_root'])
    plan = {'python': [], 'assets': [], 'defaults': [], 'dependencies': [], 'components': [], 'warnings': []}
    owners = {}

    def claim(target, owner):
        relative_path(target)
        key = target.casefold()
        require(key not in owners, 'Duplicate archive target %s (%s, %s)' % (target, owners.get(key), owner))
        owners[key] = owner

    python_files = set()
    for pattern in config['python']['include']:
        python_files.update(p for p in python_root.glob(pattern) if p.is_file())
    for path in sorted(python_files):
        source = path.relative_to(python_root).as_posix()
        input_path(root, path.relative_to(root).as_posix())
        target = config['python']['archive_root'] + '/' + str(PurePosixPath(source).with_suffix('.pyc'))
        claim(target, 'python')
        plan['python'].append({'source': path.relative_to(root).as_posix(), 'target': target})
    require(python_files, 'No Python sources')
    require((python_root / config['python']['entrypoint']).is_file(), 'Missing mod entrypoint')
    active_entrypoints, declared_configs = [], set()
    manifests = read_components(root, config['components']['source'])
    for manifest in manifests:
        path = manifest_path
        require(set(manifest) == MANIFEST_KEYS and manifest['schema_version'] == 1,
                '%s: invalid component schema' % path.name)
        require(type(manifest['enabled']) is bool, '%s: enabled must be boolean' % path.name)
        require(manifest['kind'] in ('feature', 'shared'), '%s: unknown kind' % path.name)
        require(isinstance(manifest['config_files'], list) and isinstance(manifest['assets'], list),
                '%s: expected config_files and assets lists' % path.name)
        entrypoint = manifest['entrypoint']
        if manifest['kind'] == 'feature':
            require(isinstance(entrypoint, str) and entrypoint and all(p.isidentifier() for p in entrypoint.split('.')),
                    '%s: invalid entrypoint' % path.name)
            module = python_root / 'driftkings' / (entrypoint.replace('.', '/') + '.py')
            require(module.is_file(), '%s: missing entrypoint source' % path.name)
            if manifest['enabled']:
                active_entrypoints.append(entrypoint)
        else:
            require(entrypoint is None, '%s: shared modules cannot be startup features' % path.name)
        for name in manifest['config_files']:
            default = input_path(defaults_root, name)
            require(default.is_file(), '%s: missing default %s' % (path.name, name))
            require(name not in declared_configs, 'Duplicate config owner: %s' % name)
            declared_configs.add(name)
        # Validate disabled declarations too; only enabled assets enter the plan.
        for asset in manifest['assets']:
            for item in expand_asset(root, asset, config['assets']['exclude']):
                generator = item['generator']
                if generator is not None:
                    require(generator in config['generators'], 'Unknown generator: %s' % generator)
                    spec = config['generators'][generator]
                    require(item['source'] in (spec['output'], spec.get('metadata')), 'Generator output mismatch: %s' % generator)
                    input_path(root, spec['output'])
                    if check_generated:
                        require((root / item['source']).is_file(), 'Missing generated asset: %s' % item['source'])
                    elif manifest['enabled'] and not (root / item['source']).is_file():
                        plan['warnings'].append('Pending generation: ' + item['source'])
                if manifest['enabled']:
                    claim(item['target'], manifest['id'])
                    plan['assets'].append(item)
        plan['components'].append(manifest)

    plan['warnings'].extend(validate_installer_assets(root, plan['assets'])['warnings'])
    component_list = input_path(python_root, config['python']['component_list'])
    tree = ast.parse(component_list.read_text(encoding='utf-8'))
    current = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'COMPONENTS' for t in n.targets))
    require(len(set(active_entrypoints)) == len(active_entrypoints), 'Duplicate component entrypoint')
    if check_component_list:
        require(tuple(sorted(active_entrypoints)) == tuple(current), 'component_list.py does not match enabled manifests')

    selected_defaults = set()
    for pattern in config['defaults']['include']:
        selected_defaults.update(p for p in defaults_root.glob(pattern) if p.is_file())
    for path in sorted(selected_defaults):
        read_json(path)
        name = path.relative_to(defaults_root).as_posix()
        input_path(defaults_root, name)
        plan['defaults'].append({'source': path.relative_to(root).as_posix(),
                                 'target': config['defaults']['install_root'] + '/' + name})
    require({p.relative_to(defaults_root).as_posix() for p in selected_defaults} == declared_configs | {'load.json'},
            'Default profile files and component declarations differ')

    dependency_root = input_path(root, config['ui_dependencies']['directory'])
    names = set()
    for dependency in config['ui_dependencies']['files']:
        name = dependency['name']
        require('/' not in name and name.endswith('.wotmod') and name not in names, 'Invalid dependency name')
        path = input_path(dependency_root, name)
        require(path.is_file(), 'Missing UI dependency: %s' % name)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == dependency['sha256'], 'UI dependency hash mismatch: %s' % name)
        names.add(name)
        plan['dependencies'].append(path.relative_to(root).as_posix())
    require({p.name for p in dependency_root.glob('*.wotmod')} == names, 'Unexpected UI dependencies')

    locales = read_json(root / 'build_data/locales.json')
    require(locales['schema_version'] == 1 and locales['game_version'] == config['game']['version'], 'Locale target mismatch')
    require(len(set(locales['locales'])) == len(locales['locales']), 'Duplicate locales')
    locale_source = ast.parse((python_root / 'driftkings/locale_support.py').read_text(encoding='utf-8'))
    languages = next(ast.literal_eval(node.value) for node in locale_source.body
                     if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'LANGUAGES'
                                                            for target in node.targets))
    require([code for code, _ in languages] == locales['locales'], 'Runtime and build locale lists differ')
    require(set(locales['regions']) == {'EU', 'NA', 'ASIA'}, 'Missing locale region')
    for region, codes in locales['regions'].items():
        require(set(codes) <= set(locales['locales']), 'Unknown locale in region: %s' % region)
    for language in locales['locales']:
        resource = 'res/mods/driftkings/text/' + language + '.yml'
        require((root / 'mod' / resource).is_file(), 'Missing locale: %s' % language)
        require(any(item['target'] == resource for item in plan['assets']),
                'Locale is not packaged: %s' % language)
    validate_catalogs(root)
    validate_ui_catalog(root, plan)
    if check_defaults:
        check_default_values(root)
    snapshot = read_json(root / 'build_data/defaults_snapshot.json')
    require({item['path'] for item in snapshot['files']} == {p.relative_to(defaults_root).as_posix() for p in selected_defaults},
            'Defaults snapshot inventory mismatch')
    for item in snapshot['files']:
        path = input_path(defaults_root, item['path'])
        require(defaults_sha256(path) == item['sha256'], 'Defaults snapshot hash mismatch: %s' % item['path'])
    for generator, spec in config['generators'].items():
        if spec['kind'] == 'flash':
            require(input_path(root, spec['entrypoint']).is_file(), 'Missing Flash entrypoint')
            for name in spec['source_paths']:
                require(input_path(root, name).is_dir(), 'Missing Flash source directory: %s' % name)
            library_manifest = input_path(root, spec['library_manifest'])
            libraries = read_json(library_manifest)
            require(libraries['game_version'] == config['game']['version'] and
                    libraries['source_version'] == config['reference']['version'], 'Flash reference version mismatch')
            for library in libraries['libraries']:
                path = input_path(library_manifest.parent, library['name'])
                require(hashlib.sha256(path.read_bytes()).hexdigest().lower() == library['sha256'].lower(),
                        'Flash library hash mismatch: %s' % library['name'])
        elif spec['kind'] == 'vehicle_markers':
            require(input_path(root, spec['entrypoint']).is_file(), 'Missing vehicle marker Flash source')
            lock = read_json(input_path(root, spec['lock']))
            require(lock['gameVersion'] == config['game']['version'], 'Vehicle marker version mismatch')
            require(re.match(r'^[a-f0-9]{64}$', lock['sha256']), 'Invalid marker movie digest')
        elif spec['kind'] == 'gameface_patch':
            require(spec['implementation'] == 'replace_exact', 'Unsupported patch implementation')
            patch = read_json(input_path(root, spec['patch_file']))
            require(patch['schema_version'] == 1 and patch['game_version'] == config['game']['version']
                    and patch['realm'] == config['game']['realm'] and patch['resource'] == spec['resource'],
                    'Carousel patch target mismatch')
            require(patch['operations'], 'Empty carousel patch')
            for operation in patch['operations']:
                require(set(operation) == {'find', 'replace', 'count'} and isinstance(operation['find'], str)
                        and operation['find'] and isinstance(operation['replace'], str)
                        and type(operation['count']) is int and operation['count'] > 0, 'Invalid carousel patch operation')
            if check_game:
                raw = None
                for name in spec['game_packages']:
                    relative_path(name)
                    package = Path(game_root or config['game']['root']) / name
                    require(package.is_file(), 'Missing game resource package: %s' % package)
                    with zipfile.ZipFile(package) as archive:
                        if spec['resource'] in archive.namelist():
                            require(raw is None, 'Ambiguous carousel bundle in game packages')
                            raw = archive.read(spec['resource'])
                require(raw is not None, 'Carousel bundle not found in game packages')
                apply_patch_set(raw, patch)
        elif spec['kind'] == 'csharp':
            require(input_path(root, spec['source']).is_file(), 'Missing C# source: %s' % spec['source'])
            require(isinstance(spec.get('additional_sources', []), list), 'Invalid additional C# sources')
            for source in spec.get('additional_sources', []):
                require(input_path(root, source).is_file(), 'Missing additional C# source: ' + source)
            input_path(root, spec['metadata'])
            require(isinstance(spec['references'], list), 'Invalid C# references')
        else:
            raise ValueError('Unknown generator kind: ' + generator)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-generated', action='store_true', help='Require generated outputs to exist')
    parser.add_argument('--check-game', action='store_true', help='Verify carousel patches against read-only game packages')
    parser.add_argument('--write-plan', type=Path, help='Write a resolved JSON plan for compiler development')
    args = parser.parse_args()
    try:
        plan = build_plan(check_generated=args.check_generated, check_game=args.check_game)
    except (ValueError, KeyError, TypeError, OSError, StopIteration, zipfile.BadZipFile) as error:
        parser.exit(1, 'Build data error: %s\n' % error)
    if args.write_plan:
        args.write_plan.parent.mkdir(parents=True, exist_ok=True)
        args.write_plan.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Valid: %d manifests, %d Python modules, %d assets, %d defaults, %d dependencies' %
          tuple(len(plan[key]) for key in ('components', 'python', 'assets', 'defaults', 'dependencies')))
    for warning in plan['warnings']:
        print('NOTE: ' + warning)


if __name__ == '__main__':
    main()
