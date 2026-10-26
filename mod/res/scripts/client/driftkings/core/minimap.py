# -*- coding: utf-8 -*-
"""Minimap presentation policy; no game dependencies."""
import re

try:
    text_type = unicode
except NameError:
    text_type = str

CIRCLES = ('draw', 'maxView', 'proximity', 'view')
# Distance that marks an enemy as nearby: own view range, shell range or a fixed value.
NEARBY_RANGES = ('view', 'shell', 'distance')
ARTILLERY_AIMS = tuple('gui/maps/driftkings/minimap/minimapaim_%d.png' % i for i in range(7))


def artillery_aim_choices(current):
    paths = list(ARTILLERY_AIMS)
    if current not in paths:
        paths.append(current)
    return paths


MACRO = re.compile(r'\{\{(vehicle|name|level|type|state|hp|maxHp|hpPercent|lostSeconds)(?:%\.(\d{1,2})s)?\}\}')


def defaults():
    from driftkings.settings.settings_data import defaults as component_defaults
    data = component_defaults('MinimapPlugins')
    return dict((key, data[key]) for key in ('labels', 'circles', 'lines', 'presentation', 'artilleryAim'))


def visible(mode, native):
    return native if mode == 'client' else mode == 'on'


def vehicle_group(gui_label, enemy):
    """Minimap group from the native GUI properties (ally, teamKiller, squadman, enemy)."""
    label = (gui_label or '').lower()
    if 'squad' in label:
        return 'squad'
    if enemy:
        return 'enemy'
    return 'teamKiller' if 'teamkiller' in label else 'ally'


def team_color(group, state):
    """Shared team scheme colour; lost vehicles keep their alive colour (the icon is desaturated)."""
    from driftkings.common.utils.color_rating_data import system_colors
    key = {'squad': 'squadman'}.get(group, group) + ('_dead' if state == 'dead' else '_alive')
    return system_colors.get(key, system_colors['ally_alive'])


def vehicle_names(icon_name, short_name):
    """Names an extra circle may use for one vehicle: 'germany-G04_PzVI_Tiger_I', 'G04_PzVI_Tiger_I' or 'Tiger I'."""
    icon = (icon_name or '').replace(':', '-').lower()
    names = [icon, icon.partition('-')[2], (short_name or '').lower()]
    return [name for name in names if name]


LOST_STYLES = ('tint', 'grey')


def lost_color(group, lost):
    """Dull team colour for last positions: enemies red, allies green, squadmates amber."""
    return str(lost.get({'enemy': 'enemyColor', 'squad': 'squadColor'}.get(group, 'allyColor')))


def marker_color(group, state, lost):
    """Label colour: the team scheme, or the dull team colour for tinted last positions."""
    if state == 'lost' and lost.get('style') == 'tint':
        return lost_color(group, lost)
    return team_color(group, state)


def shell_range(descriptor, shell_cd):
    """Maximum shot distance in metres of the selected shell, falling back to the active shot."""
    gun = getattr(descriptor, 'gun', None)
    for shot in getattr(gun, 'shots', None) or ():
        if getattr(getattr(shot, 'shell', None), 'compactDescr', None) == shell_cd:
            return getattr(shot, 'maxDistance', None)
    return getattr(getattr(descriptor, 'shot', None), 'maxDistance', None)


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
    if not re.match(r'^#[a-fA-F0-9]{6}\Z', str(value)):
        raise ValueError('Invalid minimap color')


def stroke(value):
    numeric(value.get('thickness'), 0.5, 5)
    numeric(value.get('dash'), 0, 100)
    numeric(value.get('gap'), 1, 100)


def migrate_map_size(data):
    """Convert legacy caption styling before merging the new defaults."""
    size = data.get('mapSize')
    if not isinstance(size, dict):
        return data
    if 'color' in size or 'fontSize' in size:
        template = size.get('format', '{{width}} x {{height}} m')
        size['format'] = '<font size="%s" color="#%s">%s</font>' % (
            size.pop('fontSize', 11), str(size.pop('color', 'FFFFFF')).lstrip('#'), template)
    for old, new in (('x', 'offsetX'), ('y', 'offsetY')):
        if old in size:
            size.setdefault(new, size.pop(old))
    return data


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
    shell = data['circles'].get('shell')
    if not isinstance(shell, dict) or shell.get('mode') not in ('on', 'off'):
        raise ValueError('Invalid minimap circle: shell')
    numeric(shell.get('alpha'), 0, 100)
    stroke(shell)
    color(shell.get('color'))
    if type(data['lines'].get('hull')) is not bool:
        raise ValueError('Invalid minimap switch: lines.hull')
    numeric(data['lines'].get('marks'), 0, 500)
    for key in ('directionColor', 'sectorColor', 'hullColor'):
        if not re.match(r'^#[a-fA-F0-9]{6}$', str(data['lines'].get(key, ''))):
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
    for key in ('allyColor', 'enemyColor', 'squadColor', 'teamKillerColor', 'deadColor'):
        color(labels.get(key))
    if type(labels.get('teamColors')) is not bool:
        raise ValueError('Invalid minimap switch: labels.teamColors')
    numeric(data['icons'].get('deadAlpha'), 0, 100)
    for key in ('deadScale', 'lostScale'):
        numeric(data['icons'].get(key), .5, 3)
    for key in ('triangleAlpha', 'directionAlpha'):
        numeric(data['lines'].get(key), 0, 100)
    nearby = data.get('nearby')
    if not isinstance(nearby, dict) or type(nearby.get('enabled')) is not bool or nearby.get('range') not in NEARBY_RANGES:
        raise ValueError('Invalid minimap section: nearby')
    numeric(nearby.get('distance'), 50, 1500)
    numeric(nearby.get('alpha'), 0, 100)
    color(nearby.get('color'))
    numeric(data['lostMarker'].get('desaturate'), 0, 100)
    if type(data['lostMarker'].get('icon')) is not bool:
        raise ValueError('Invalid minimap switch: lostMarker.icon')
    if data['lostMarker'].get('style') not in LOST_STYLES:
        raise ValueError('Invalid lost marker style')
    for key in ('allyColor', 'enemyColor', 'squadColor'):
        color(data['lostMarker'].get(key))
    color(data['icons'].get('selfColor'))
    numeric(labels.get('compactLength'), 4, 40)
    for section in ('labels', 'health'):
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
    size = data['mapSize']
    for key in ('offsetX', 'offsetY'):
        numeric(size.get(key), -300, 300)
    numeric(size.get('alpha'), 0, 100)
    for key in ('width', 'height'):
        numeric(size.get(key), 1, 1000)
    shadow = size.get('shadow')
    if not isinstance(shadow, dict) or type(shadow.get('enabled')) is not bool:
        raise ValueError('Invalid map size shadow')
    for key, low, high in (('distance', 0, 100), ('angle', -360, 360), ('alpha', 0, 100),
                           ('blur', 0, 100), ('strength', 0, 100)):
        numeric(shadow.get(key), low, high)
    shadow_color = shadow.get('color')
    color(shadow_color)
    if not isinstance(data['mapSize'].get('format'), (str, text_type)) or len(data['mapSize']['format']) > 1024:
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
        vehicle = item.get('vehicle', '')
        if not isinstance(vehicle, (str, text_type)) or len(vehicle) > 64:
            raise ValueError('Invalid circle vehicle name')


def numeric(value, lo, hi):
    if type(value) not in (int, float) or not lo <= value <= hi:
        raise ValueError('Minimap number outside %s..%s' % (lo, hi))
