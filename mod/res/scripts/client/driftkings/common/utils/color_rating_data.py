# -*- coding: utf-8 -*-
"""Load shared colours and separate statistical palettes with JSON references."""
import json
import os
import re

from driftkings._constants import MARK_LEVELS as MOE_LEVELS

RESOURCE_ROOT = 'mods/driftkings/colors/'
RESOURCE = RESOURCE_ROOT + 'shared.json'
_REFERENCE = re.compile(r'\A\$\{(def(?:\.[A-Za-z0-9_]+)+)\}\Z')
_FILENAME = re.compile(r'\A[a-z0-9_]+\.json\Z')
try:
    _TEXT = basestring
except NameError:
    _TEXT = str


def read_resource(path=RESOURCE):
    try:
        import ResMgr
    except ImportError:
        # Standalone tools and tests read the same resources as the game client.
        path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', path)
        with open(path, 'rb') as stream:
            return stream.read()
    section = ResMgr.openSection(path)
    if section is None or not ResMgr.isFile(path):
        raise IOError('Missing colour resource: ' + path)
    return section.asBinary


def resolve(value, document, trail=()):
    """Resolve whole-value ${def.name} references, rejecting missing paths and cycles."""
    if isinstance(value, dict):
        return dict((key, resolve(item, document, trail)) for key, item in value.items())
    if isinstance(value, list):
        return [resolve(item, document, trail) for item in value]
    if isinstance(value, _TEXT) and value.startswith('${'):
        match = _REFERENCE.match(value)
        if match is None:
            raise ValueError('Invalid colour reference: ' + value)
        path = match.group(1)
        if path in trail:
            raise ValueError('Circular colour reference: ' + path)
        target = document
        for key in path.split('.'):
            if not isinstance(target, dict) or key not in target:
                raise ValueError('Unknown colour reference: ' + path)
            target = target[key]
        return resolve(target, document, trail + (path,))
    return value


def load_document(reader, path):
    document = json.loads(reader(path).decode('utf-8-sig'))
    if not isinstance(document, dict) or not isinstance(document.get('def'), dict):
        raise ValueError('Invalid colour definitions: ' + path)
    colors = document.get('colors')
    if not isinstance(colors, dict):
        raise ValueError('Invalid colour tables: ' + path)
    return document, resolve(colors, document)


def load_tables(reader=read_resource):
    document, shared = load_document(reader, RESOURCE)
    palettes = document.get('palettes')
    if not isinstance(palettes, list) or not palettes:
        raise ValueError('Missing rating palette list')
    tables, names, files = [], set(), set()
    for entry in palettes:
        if not isinstance(entry, dict):
            raise ValueError('Invalid rating palette entry')
        name, filename = entry.get('name'), entry.get('file')
        if not isinstance(name, _TEXT) or not name or name in names:
            raise ValueError('Invalid or duplicate rating palette name')
        if not isinstance(filename, _TEXT) or not _FILENAME.match(filename) or filename in files or filename == 'shared.json':
            raise ValueError('Invalid or duplicate rating palette file')
        names.add(name)
        files.add(filename)
        unused, colors = load_document(reader, RESOURCE_ROOT + filename)
        if set(colors).intersection(shared):
            raise ValueError('Palette overrides shared colours: ' + name)
        colors.update(shared)
        tables.append({'ScaleColor': name, 'colors': colors})
    return {'color_tables': tables, 'system_colors': shared['system']}


_data = load_tables()
color_tables = _data['color_tables']
system_colors = _data['system_colors']
_by_name = dict((table['ScaleColor'], table['colors']) for table in color_tables)
noob_meter_colors = _by_name['NoobMeter']
xvm_colors = _by_name['XVM']
wot_life_colors = _by_name['WoT-Life']
vehicle_type_colors = noob_meter_colors['vtype']
total_hp_colors = noob_meter_colors['totalHP']
damage_colors = noob_meter_colors['damage']
del _data, _by_name
