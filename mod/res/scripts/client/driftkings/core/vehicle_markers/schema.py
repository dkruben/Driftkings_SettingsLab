# -*- coding: utf-8 -*-
"""structured marker files (markers.json + four state files) and their runtime layout.

markers.json wires each team/state/mode to a block of a state file; each state
file holds its own "def" templates. Geometry uses fixed boxes: text fields are 140x100 boxes anchored at x by
their alignment, damage text 200x100 boxes and vehicle distance 100x100 boxes.
"""
import copy
import re

from driftkings._constants import VEHICLE_MARKERS
from driftkings.common.utils.compat import string_types
from driftkings.core.vehicle_markers.layouts import MODES, STATES, TEAMS
from driftkings.core.vehicle_markers.references import resolve

STATE_KEYS = VEHICLE_MARKERS.STATE_KEYS
FILES = VEHICLE_MARKERS.FILES
WIRING = re.compile(r'^\$\{(markers(?:Alive|Dead)(?:Normal|Extended))\.json:(ally|enemy)\}$')
GENERAL = {'debug': False, 'colorRating': 0, 'ratingType': 'wn8',
           'turretMarkers': {'highVulnerability': '*', 'lowVulnerability': "'"}, 'colors': {}}
TEXT_STYLE = ('font', 'size', 'color', 'bold', 'italic')
SHADOW = ('enabled', 'distance', 'angle', 'color', 'alpha', 'blur', 'strength')
FIELD_SIZE = (140, 100)
DAMAGE_SIZE = (200, 100)
DISTANCE_SIZE = (100, 100)


def join(documents):
    """File contents by name -> settings dictionary; markers.enabled becomes the section switch."""
    markers = copy.deepcopy(documents.get('markers.json', {}).get('markers', {}))
    result = {'enabled': markers.pop('enabled', True), 'markers': markers}
    for key in STATE_KEYS:
        result[key] = copy.deepcopy(documents.get(key + '.json', {}))
    return result


def split(data):
    markers = dict(enabled=data['enabled'], **copy.deepcopy(data['markers']))
    return [('markers.json', {'markers': markers})] + [(key + '.json', copy.deepcopy(data[key])) for key in STATE_KEYS]


def block(data, documents, team, state, mode):
    """The resolved marker block shown for one team/state/mode."""
    value = data['markers'].get(team, {}).get(state, {}).get(mode)
    if isinstance(value, dict):
        return resolve(value)
    match = WIRING.match(value) if isinstance(value, string_types) else None
    if match is None:
        raise ValueError('Invalid marker wiring: %s.%s.%s' % (team, state, mode))
    key, part = match.groups()
    if key not in documents:
        document = data.get(key)
        if not isinstance(document, dict):
            raise ValueError('Missing marker state file: ' + key)
        documents[key] = resolve(document)
    if not isinstance(documents[key].get(part), dict):
        raise ValueError('Missing marker block: %s:%s' % (key, part))
    return documents[key][part]


def anchored(x, y, align, valign, size):
    width, height = size
    if align == 'right':
        x -= width
    elif align == 'center':
        x -= width / 2.0
    if valign == 'bottom':
        y -= height
    elif valign == 'center':
        y -= height / 2.0
    return x, y


def style(options, keys):
    return dict((key, options[key]) for key in keys if key in options)


def get(options, key, default=None):
    """The schema treats a null option as unset, exactly like a missing one."""
    value = options.get(key)
    return default if value is None else value


def part(options, key):
    """A nested option block; null or a non-object means "not set"."""
    value = options.get(key)
    return value if isinstance(value, dict) else {}


def text_field(options, size=FIELD_SIZE, default_format=''):
    width, height = get(options, 'width', size[0]), get(options, 'height', size[1])
    align = get(options, 'align', 'center')
    x, y = anchored(get(options, 'x', 0), get(options, 'y', 0), align, options.get('valign'), (width, height))
    text = part(options, 'textFormat')
    fmt = get(options, 'format', default_format)
    textFormat = style(text, TEXT_STYLE)
    result = {'name': get(options, 'name', ''), 'enabled': get(options, 'enabled', True), 'format': fmt,
              'x': x, 'y': y, 'width': width, 'height': height, 'alpha': get(options, 'alpha', 100),
              'align': align, 'textFormat': textFormat}
    if isinstance(options.get('shadow'), dict):
        result['shadow'] = style(options['shadow'], SHADOW)
    return result


def distance_field(options):
    field = text_field(options, DISTANCE_SIZE, "{{alive&&distance?{{distance}}m|}}")
    field['name'] = 'Vehicle distance'
    return field


def damage_text(options):
    field = text_field(options, DAMAGE_SIZE, get(options, 'damageMessage', '{{dmg}}'))
    field['format'] = get(options, 'damageMessage', '{{dmg}}')
    field['textFormat'].setdefault('color', None)
    if field['textFormat']['color'] is None:
        field['textFormat']['color'] = '{{c:dmg}}'
    field.update(duration=get(options, 'speed', 2), rise=get(options, 'maxRange', 40), maxCount=4,
                 blowupMessage=get(options, 'blowupMessage', '{{i18n:blownUp}}\n{{dmg}}'))
    field.pop('name')
    return field


def health_bar(options, dead):
    border = part(options, 'border')
    damage = part(options, 'damage')
    lcolor = options.get('lcolor')
    enabled = get(options, 'enabled', True)
    return {'enabled': enabled, 'showOnDead': bool(dead and enabled),
            'x': get(options, 'x', -36), 'y': get(options, 'y', -33),
            'width': get(options, 'width', 70), 'height': get(options, 'height', 12), 'alpha': get(options, 'alpha', 100),
            'color': get(options, 'color', '{{c:team}}'),
            'fill': {'alpha': get(part(options, 'fill'), 'alpha', 100)},
            'gradient': {'enabled': lcolor is not None, 'color': get(options, 'lcolor', '{{c:hp}}'), 'angle': 0},
            # The layout draws the substrate and the frame with the same colour and opacity.
            'background': {'color': get(border, 'color', '#000000'), 'alpha': get(border, 'alpha', 35)},
            'border': {'color': get(border, 'color', '#000000'), 'alpha': get(border, 'alpha', 35),
                       'width': get(border, 'size', 1)},
            'damage': {'enabled': True, 'color': get(damage, 'color', '{{c:dmg}}'), 'alpha': get(damage, 'alpha', 80),
                       'delay': 0, 'duration': get(damage, 'fade', 1)},
            'shadow': {'enabled': False}}


def author(options, key):
    """Damage text of one author; a block that is not set falls back to the general damageText."""
    return options[key] if isinstance(options.get(key), dict) else part(options, 'damageText')


def position(options, defaults=None):
    result = {'enabled': get(options, 'enabled', True), 'x': options.get('x'), 'y': options.get('y'),
              'scale': 1, 'alpha': get(options, 'alpha', 100), 'deadAlpha': 100}
    result.update(defaults or {})
    return result


def icons(options):
    vehicle = part(options, 'vehicleIcon')
    contour = part(options, 'contourIcon')
    hover = part(options, 'hoverMarker')
    indicator = part(options, 'damageIndicator')
    x, y = get(indicator, 'x', 53), get(indicator, 'y', -27)
    return {'enabled': True,
            # The layout moves the icon container (marker.marker), plus its offset; it ignores maxScale.
            'class': {'enabled': get(vehicle, 'enabled', True), 'x': None, 'y': None, 'scale': 1,
                      'alpha': get(vehicle, 'alpha', 100), 'deadAlpha': 100,
                      'containerX': get(vehicle, 'x', 0) + get(vehicle, 'offsetX', 0),
                      'containerY': get(vehicle, 'y', -16) + get(vehicle, 'offsetY', 0),
                      'showSpeaker': bool(vehicle.get('showSpeaker', False))},
            'level': position(part(options, 'levelIcon') if options.get('levelIcon') is not None else {'enabled': False}),
            'vehicle': position(contour, {'enabled': get(contour, 'enabled', False),
                                          'tint': {'color': contour.get('color') or '{{c:system}}',
                                                   'amount': get(contour, 'amount', 0)}}),
            'actionMarker': position(part(options, 'actionMarker')),
            'hoverMarker': position(hover, {'glow': copy.deepcopy(hover['glow'] if isinstance(hover.get('glow'), dict) else {'enabled': True})}),
            'vehicleStatusMarker': position(part(options, 'vehicleStatusMarker')),
            'damageIndicator': position(indicator),
            'hitExplosion': position(indicator),
            'damageIndicatorText': position(indicator, {'enabled': bool(get(indicator, 'enabled', True) and get(indicator, 'showText', True)),
                                                        'x': x + 14, 'y': y - 14})}


def adapt(data):
    """Marker settings -> the internal schema consumed by validation, Python presentation and Flash."""
    markers = data['markers']
    enabled = data['enabled']
    result = copy.deepcopy(GENERAL)
    result.update(dict((key, copy.deepcopy(markers[key])) for key in GENERAL if key in markers))
    result.update(enabled=enabled, schemaVersion=2, markers={'enabled': enabled},
                  customFields={'enabled': enabled}, healthBar={'enabled': enabled},
                  damageText={'enabled': enabled}, icons={'enabled': enabled})
    documents = {}
    for team in TEAMS:
        for name in ('markers', 'customFields', 'healthBar', 'damageText', 'icons'):
            result[name][team] = dict((state, {}) for state in STATES)
        for state in STATES:
            for mode in MODES:
                options = block(data, documents, team, state, mode)
                level = part(options, 'levelIcon')
                contour = part(options, 'contourIcon')
                result['markers'][team][state][mode] = {
                    'vehicleName': False, 'playerName': False, 'hp': 'hidden', 'healthBar': False,
                    'vehicleIcon': bool(contour.get('enabled', False)), 'levelIcon': bool(level.get('enabled', False)),
                    'damage': True}
                if not enabled:
                    continue
                fields = [text_field(item) for item in (options.get('textFields') or []) if isinstance(item, dict)]
                distance = part(options, 'vehicleDist')
                if distance.get('enabled'):
                    fields.append(distance_field(distance))
                result['customFields'][team][state][mode] = fields
                result['healthBar'][team][state][mode] = health_bar(part(options, 'healthBar'), state == 'dead')
                other = damage_text(part(options, 'damageText'))
                result['damageText'][team][state][mode] = dict(other, sources={
                    'player': damage_text(author(options, 'damageTextPlayer')),
                    'squad': damage_text(author(options, 'damageTextSquadman')),
                    'other': {}})
                result['icons'][team][state][mode] = icons(options)
    return result


def legacy_general(documents):
    """Keep the general switches of the earlier seven-file layout; its layouts are replaced."""
    general = documents.get('general.json', {})
    markers = {'enabled': bool(general.get('enabled', True))}
    for key in ('debug', 'colorRating', 'ratingType'):
        if key in general:
            markers[key] = general[key]
    turret = general.get('turretMarkers')
    if isinstance(turret, dict):
        markers['turretMarkers'] = dict((key, turret[key]) for key in ('highVulnerability', 'lowVulnerability') if key in turret)
    colors = documents.get('colors.json', {}).get('colors')
    if isinstance(colors, dict):
        markers['colors'] = colors
    return markers
