# -*- coding: utf-8 -*-
"""Minimap presentation policy; no game dependencies."""
import re
try:
    text_type = unicode
except NameError:
    text_type = str

CIRCLES = ('draw', 'maxView', 'proximity', 'view')
ARTILLERY_AIMS = tuple('gui/maps/Driftkings/Minimap/MinimapAim_%d.png' % i for i in range(7))


def migrate_artillery_aim(data):
    """The original PNG was renamed to _0; leave custom resource paths intact."""
    aim = data['artilleryAim']
    if aim.get('src') == 'gui/maps/Driftkings/Minimap/MinimapAim.png':
        aim['src'] = ARTILLERY_AIMS[0]


def artillery_aim_choices(current):
    paths = list(ARTILLERY_AIMS)
    if current not in paths:
        paths.append(current)
    return paths


MACRO = re.compile(r'\{\{(vehicle|name|level|type|state|hp|maxHp|hpPercent|lostSeconds)(?:%\.(\d{1,2})s)?\}\}')


def defaults():
    from Driftkings.settings.settings_data import defaults as component_defaults
    data = component_defaults('MinimapPlugins')
    return dict((key, data[key]) for key in ('labels', 'circles', 'lines', 'presentation', 'artilleryAim'))


def visible(mode, native):
    return native if mode == 'client' else mode == 'on'


def render(template, values):
    """Plain text only; never evaluate arbitrary expressions or player HTML."""
    if not isinstance(template, text_type):
        try:
            template = template.decode('utf-8')
        except (AttributeError, UnicodeError):
            return ''
    def replace(match):
        value = values.get(match.group(1), '')
        if isinstance(value, bytes) and not isinstance(value, text_type):
            value = value.decode('utf-8', 'replace')
        value = text_type(value) if value is not None else ''
        limit = match.group(2)
        if limit and len(value) > int(limit):
            value = value[:max(0, int(limit)-2)] + '..'
        return value
    return MACRO.sub(replace, template[:256]).replace('<', '').replace('>', '')[:256]


def label(options, values, alternative=False):
    if not options['enabled']:
        return ''
    state = values.get('state', 'alive')
    key = state if state in ('dead', 'lost') else 'alternative' if alternative else 'normal'
    group = values.get('group', 'ally')
    specific = ('alternative' + group.capitalize()) if alternative else group
    template = options.get(specific) if state == 'alive' else None
    return render(template or options[key], values)


def health_values(current, maximum):
    if current is None or not maximum or current > maximum:
        return {'hp': '--', 'maxHp': maximum or '--', 'hpPercent': '--'}
    current = max(0, int(current))
    return {'hp': current, 'maxHp': int(maximum), 'hpPercent': int(round(100.0 * current / maximum))}


def color(value):
    if not re.match(r'^(?:#|0x)?[a-fA-F0-9]{6}\Z', str(value)):
        raise ValueError('Invalid minimap color')


def stroke(value):
    numeric(value.get('thickness'), 0.5, 5)
    numeric(value.get('dash'), 0, 100)
    numeric(value.get('gap'), 1, 100)


def validate(data):
    for name in ('labels', 'circles', 'lines', 'presentation', 'artilleryAim'):
        if not isinstance(data.get(name), dict):
            raise ValueError('Invalid minimap section: ' + name)
    for key in CIRCLES:
        value = data['circles'].get(key)
        if not isinstance(value, dict) or value.get('mode') not in ('client', 'on', 'off'):
            raise ValueError('Invalid minimap circle: ' + key)
        numeric(value.get('alpha'), 0, 100)
        stroke(value)
    for key in ('direction', 'sector'):
        if data['lines'].get(key) not in ('client', 'on', 'off'):
            raise ValueError('Invalid minimap line mode')
    for key in ('directionColor', 'sectorColor'):
        if not re.match(r'^(?:#|0x)?[a-fA-F0-9]{6}$', str(data['lines'].get(key, ''))):
            raise ValueError('Invalid minimap line color')
    for key in ('normal', 'alternative', 'dead', 'lost'):
        value = data['labels'].get(key)
        if not isinstance(value, (str, text_type)) or len(value) > 256:
            raise ValueError('Invalid minimap label')
    for key in ('alternativeEnabled', 'zoom', 'center'):
        if type(data['presentation'].get(key)) is not bool:
            raise ValueError('Invalid minimap presentation switch')
    for section, key in (('labels', 'enabled'), ('lines', 'customStyle')):
        if type(data[section].get(key)) is not bool:
            raise ValueError('Invalid minimap switch')
    numeric(data['labels'].get('fontSize'), 8, 24)
    numeric(data['labels'].get('alpha'), 0, 100)
    numeric(data['lines'].get('alpha'), 0, 100)
    numeric(data['presentation'].get('normalAlpha'), 10, 100)
    numeric(data['presentation'].get('alternativeAlpha'), 10, 100)
    numeric(data['presentation'].get('sizeIndex'), 0, 5)
    numeric(data['presentation'].get('backgroundAlpha'), 0, 100)
    if type(data['presentation']['sizeIndex']) is not int:
        raise ValueError('Minimap size index must be an integer')
    numeric(data.get('zoomFactor'), 1, 3)
    numeric(data.get('zoomFactorMax'), 1, 3)
    numeric(data.get('lastPositionDuration'), 0, 300)
    aim = data['artilleryAim']
    if type(aim.get('enabled')) is not bool:
        raise ValueError('Invalid artillery aim switch')
    numeric(aim.get('scale'), 10, 200)
    numeric(aim.get('alpha'), 0, 100)
    path = aim.get('src')
    if not isinstance(path, (str, text_type)) or not path.strip() or len(path) > 512 or '\n' in path or '\r' in path or not path.lower().endswith('.png'):
        raise ValueError('Invalid artillery aim PNG path')
    for section in ('icons', 'health', 'lostMarker', 'mapSize'):
        if not isinstance(data.get(section), dict):
            raise ValueError('Invalid minimap section: ' + section)
    labels = data['labels']
    if labels.get('align') not in ('left', 'center', 'right'):
        raise ValueError('Invalid label alignment')
    for key in ('ally', 'enemy', 'squad', 'alternativeAlly', 'alternativeEnemy', 'alternativeSquad'):
        if not isinstance(labels.get(key), (str, text_type)) or len(labels[key]) > 256:
            raise ValueError('Invalid label format: ' + key)
    for section, keys in (('labels', ('shadow', 'customColors', 'avoidOverlap')),
                          ('lostMarker', ('showSeconds', 'fade')), ('mapSize', ('enabled',)),
                          ('lines', ('geometry',))):
        for key in keys:
            if type(data[section].get(key)) is not bool:
                raise ValueError('Invalid minimap switch: ' + section + '.' + key)
    for key in ('allyColor', 'enemyColor', 'squadColor', 'deadColor'):
        color(labels.get(key))
    color(data['icons'].get('selfColor'))
    color(data['mapSize'].get('color'))
    numeric(labels.get('compactLength'), 4, 40)
    for section in ('labels', 'health', 'mapSize'):
        for key in ('x', 'y'):
            numeric(data[section].get(key), -300, 300)
    for key in ('scale', 'selfScale'):
        numeric(data['icons'].get(key), .5, 3)
    for key in ('alpha', 'selfAlpha'):
        numeric(data['icons'].get(key), 0, 100)
    numeric(data['lostMarker'].get('minimumAlpha'), 0, 100)
    hp = data['health']
    if hp.get('visibility') not in ('always', 'key', 'never') or hp.get('mode') not in ('value', 'percent', 'bar'):
        raise ValueError('Invalid minimap health mode')
    numeric(hp.get('width'), 10, 100)
    numeric(hp.get('height'), 1, 10)
    numeric(hp.get('fontSize'), 8, 24)
    numeric(data['mapSize'].get('fontSize'), 8, 24)
    if not isinstance(data['mapSize'].get('format'), (str, text_type)) or len(data['mapSize']['format']) > 128:
        raise ValueError('Invalid map size format')
    stroke(data['lines'])
    numeric(data['lines'].get('length'), 50, 1500)
    extra = data.get('extraCircles')
    if not isinstance(extra, list) or len(extra) > 8:
        raise ValueError('Expected up to eight extra circles')
    for item in extra:
        if not isinstance(item, dict):
            raise ValueError('Invalid extra circle')
        stroke(item)
        numeric(item.get('radius'), 1, 1500)
        numeric(item.get('alpha'), 0, 100)
        color(item.get('color'))
        if item.get('vehicleClass') not in ('all', 'lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG'):
            raise ValueError('Invalid circle vehicle class')


def numeric(value, lo, hi):
    if type(value) not in (int, float) or not lo <= value <= hi:
        raise ValueError('Minimap number outside %s..%s' % (lo, hi))


