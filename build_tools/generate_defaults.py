"""Generate Python 2.7 fallback values from the distribution JSON defaults."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import pprint

try:
    from .components import read_components
except ImportError:
    from components import read_components

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'mod/res/scripts/client/driftkings/settings/default_values.py'
PROFILES = ('none', 'short', 'medium', 'medium2', 'large')


def read_object(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key in %s: %s' % (path, key))
            result[key] = value
        return result
    value = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=pairs,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON value: ' + value)))
    if not isinstance(value, dict):
        raise ValueError('Expected JSON object: ' + str(path))
    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError('Nonfinite JSON number: ' + str(path))
        if isinstance(item, dict):
            for child in item.values(): finite(child)
        elif isinstance(item, list):
            for child in item: finite(child)
    finite(value)
    return value


def assemble(root=ROOT):
    config = read_object(root / 'build_data/build_config.json')
    source = root / config['defaults']['source_root']
    constants = ast.parse((root / 'mod/res/scripts/client/driftkings/_constants.py').read_text(encoding='utf-8'))
    declared_names = set()
    for node in constants.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == 'NAME':
                            declared_names.add(ast.literal_eval(item.value))
                        elif isinstance(target, ast.Name) and target.id == 'ID':
                            raise ValueError('Configuration classes must use NAME only: ' + node.name)
    documents = {}
    def document(name):
        if name not in documents:
            documents[name] = read_object(source / name)
        return documents[name]
    defaults = {}
    for manifest in read_components(root, config['components']['source']):
        if manifest['kind'] != 'feature':
            continue
        identifier = manifest['id']
        if identifier not in declared_names:
            raise ValueError('Unknown canonical configuration section: ' + identifier)
        declared = set(manifest['config_files'])
        if not declared:
            # Features may share another section instead of owning a settings page.
            continue
        def get(name):
            if name not in declared:
                raise ValueError('%s does not declare default %s' % (identifier, name))
            return document(name)
        if identifier == 'team_panels':
            prefix = 'default/team_panels/'
            data = dict(get(prefix + 'general.json'))
            data.update(get(prefix + 'playerspanel.json'))
            data['loading'] = dict(get(prefix + 'battleloading.json'))
            data['loading'].pop('tips', None)  # Retired native loading option.
            data['tab'] = get(prefix + 'statisticform.json')
            data['profiles'] = {name: get(prefix + 'panel' + name.lower() + '.json') for name in PROFILES}
        elif identifier == 'vehicle_carousel':
            prefix = 'default/vehicle_carousel/'
            general = get(prefix + 'carousel.json')
            data = {key: general[key] for key in ('enabled', 'showIcons', 'colorRating')}
            data['carousel'] = {key: value for key, value in general.items() if key not in data}
            data['carousel'].update(normal=get(prefix + 'carouselnormal.json'), small=get(prefix + 'carouselsmall.json'))
        elif identifier == 'vehicle_markers':
            # Marker layout: markers.json (its enabled is the section switch) and four state files.
            markers = dict(get('default/vehicle_markers/markers.json')['markers'])
            data = {'enabled': markers.pop('enabled'), 'markers': markers}
            for name in ('markersAliveNormal', 'markersAliveExtended', 'markersDeadNormal', 'markersDeadExtended'):
                data[name] = get('default/vehicle_markers/' + name + '.json')
        elif identifier == 'minimap_enhancements':
            data = {}
            for name in ('minimap.json', 'minimap_labels.json', 'minimap_circles.json', 'minimap_lines.json'):
                part = get('default/minimap_enhancements/' + name)
                overlap = set(part) & set(data)
                if overlap:
                    raise ValueError('Duplicate minimap sections: ' + ', '.join(sorted(overlap)))
                data.update(part)
        else:
            if len(declared) != 1:
                raise ValueError('Expected one defaults document for ' + identifier)
            data = get(next(iter(declared)))
        defaults[identifier] = data
    selector = document('load.json')
    if not isinstance(selector.get('loadConfig'), str) or not selector['loadConfig']:
        raise ValueError('Missing default configuration profile')
    return defaults, selector, documents


def render(root=ROOT):
    defaults, selector, documents = assemble(root)
    hashes = {name: hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
              for name, value in sorted(documents.items())}
    # ASCII literals plus unicode_literals work identically on Python 2.7 and 3.
    literal = lambda value: pprint.pformat(json.loads(json.dumps(value)), width=110, sort_dicts=True).encode('ascii', 'backslashreplace').decode('ascii')
    return ('# -*- coding: utf-8 -*-\n'
            '"""Generated from res/configs/Driftkings. Edit the JSON, never this file.\n\n'
            'Regenerate: python build_tools/generate_defaults.py --write\n'
            '"""\nfrom __future__ import unicode_literals\n\n'
            'SOURCE_HASHES = ' + literal(hashes) + '\n\n'
            'SELECTOR = ' + literal(selector) + '\n\n'
            'DEFAULTS = ' + literal(defaults) + '\n')


def check_generated(root=ROOT):
    path = root / TARGET
    if not path.is_file() or path.read_text(encoding='utf-8') != render(root):
        raise ValueError('Python defaults differ from JSON. Run python build_tools/generate_defaults.py --write')


def defaults_sha256(path):
    """Hash JSON text consistently across LF and CRLF working-tree checkouts."""
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def refresh_snapshot(root=ROOT):
    path = root / 'build_data/defaults_snapshot.json'
    snapshot = read_object(path)
    config = read_object(root / 'build_data/build_config.json')
    source = root / config['defaults']['source_root']
    for item in snapshot['files']:
        item['sha256'] = defaults_sha256(source / item['path'])
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Check that the Python fallback matches the canonical JSON without writing')
    mode.add_argument('--write', action='store_true', help='Regenerate the checked-in Python fallback')
    parser.add_argument('--refresh-snapshot', action='store_true', help='Record intentional edits to the JSON defaults')
    args = parser.parse_args()
    if args.refresh_snapshot and not args.write:
        parser.error('--refresh-snapshot requires --write')
    if args.write:
        (ROOT / TARGET).write_text(render(ROOT), encoding='utf-8')
        if args.refresh_snapshot:
            refresh_snapshot(ROOT)
    try:
        check_generated(ROOT)
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
    print('Defaults match the canonical JSON: %d components' % len(assemble(ROOT)[0]))
