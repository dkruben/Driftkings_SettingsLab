# -*- coding: utf-8 -*-
"""XVM-style marker files (markers.json + four state files) and their runtime layout.

markers.json wires each team/state/mode to a block of a state file, as XVM's
markers.xc does; each state file holds its own "def" templates. XMQP is not
supported. Geometry follows XVM: text fields are 140x100 boxes anchored at x by
their alignment, damage text 200x100 boxes and vehicle distance 100x100 boxes.
"""
import copy
import re

from driftkings.core.vehicle_markers.layouts import MODES, STATES, TEAMS
from driftkings.core.vehicle_markers.references import resolve

STATE_KEYS = ('markersAliveNormal', 'markersAliveExtended', 'markersDeadNormal', 'markersDeadExtended')
FILES = ('markers.json',) + tuple(key + '.json' for key in STATE_KEYS)
WIRING = re.compile(r'^\$\{(markers(?:Alive|Dead)(?:Normal|Extended))\.json:(ally|enemy)\}$')
GENERAL = {'debug': False, 'colorRating': 0, 'ratingType': 'wn8',
           'turretMarkers': {'highVulnerability': '*', 'lowVulnerability': "'"}, 'colors': {}}
# Glyphs of XVM's private icon font drawn with the client font.
XVM_GLYPHS = {'&#x115;': u'■'}
TEXT_STYLE = ('font', 'size', 'color', 'bold', 'italic')
SHADOW = ('enabled', 'distance', 'angle', 'color', 'alpha', 'blur', 'strength')
FIELD_SIZE = (140, 100)
DAMAGE_SIZE = (200, 100)
DISTANCE_SIZE = (100, 100)

try:
    STRING = basestring
except NameError:
    STRING = str


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
    """The resolved XVM block shown for one team/state/mode."""
    value = data['markers'].get(team, {}).get(state, {}).get(mode)
    if isinstance(value, dict):
        return resolve(value)
    match = WIRING.match(value) if isinstance(value, STRING) else None
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


def text_field(options, size=FIELD_SIZE, default_format=''):
    width, height = options.get('width', size[0]), options.get('height', size[1])
    align = options.get('align', 'center')
    x, y = anchored(options.get('x', 0), options.get('y', 0), align, options.get('valign'), (width, height))
    text = options.get('textFormat') or {}
    fmt = options.get('format', default_format)
    textFormat = style(text, TEXT_STYLE)
    if textFormat.get('font') == 'xvm':
        for glyph, replacement in XVM_GLYPHS.items():
            fmt = fmt.replace(glyph, replacement)
        textFormat['font'] = '$FieldFont'
    result = {'name': options.get('name', ''), 'enabled': options.get('enabled', True), 'format': fmt,
              'x': x, 'y': y, 'width': width, 'height': height, 'alpha': options.get('alpha', 100),
              'align': align, 'textFormat': textFormat}
    if 'shadow' in options:
        result['shadow'] = style(options['shadow'], SHADOW)
    return result


def distance_field(options):
    field = text_field(options, DISTANCE_SIZE, "{{alive&&distance?{{distance}}m|}}")
    field['name'] = 'Vehicle distance'
    return field


def damage_text(options):
    field = text_field(options, DAMAGE_SIZE, options.get('damageMessage', '{{dmg}}'))
    field['format'] = options.get('damageMessage', '{{dmg}}')
    field['textFormat'].setdefault('color', None)
    if field['textFormat']['color'] is None:
        field['textFormat']['color'] = '{{c:dmg}}'
    field.update(duration=options.get('speed', 2), rise=options.get('maxRange', 40), maxCount=4,
                 blowupMessage=options.get('blowupMessage', '{{i18n:blownUp}}\n{{dmg}}'))
    field.pop('name')
    return field


def hex_color(value, fallback):
    """XVM writes 0xRRGGBB; the health bar validates #RRGGBB. Macros pass unchanged."""
    if value is None:
        return fallback
    if isinstance(value, STRING) and re.match(r'^0x[0-9A-Fa-f]{6}$', value):
        return '#' + value[2:].upper()
    return value


def health_bar(options, dead):
    border = options.get('border', {})
    damage = options.get('damage', {})
    lcolor = options.get('lcolor')
    return {'enabled': options.get('enabled', True), 'showOnDead': bool(dead and options.get('enabled', True)),
            'x': options.get('x', -36), 'y': options.get('y', -33),
            'width': options.get('width', 70), 'height': options.get('height', 12), 'alpha': options.get('alpha', 100),
            'color': hex_color(options.get('color'), '{{c:team}}'),
            'fill': {'alpha': options.get('fill', {}).get('alpha', 100)},
            'gradient': {'enabled': lcolor is not None, 'color': hex_color(lcolor, '{{c:hp}}'), 'angle': 0},
            # XVM draws the substrate and the frame with the same colour and opacity.
            'background': {'color': hex_color(border.get('color'), '#000000'), 'alpha': border.get('alpha', 35)},
            'border': {'color': hex_color(border.get('color'), '#000000'), 'alpha': border.get('alpha', 35),
                       'width': border.get('size', 1)},
            'damage': {'enabled': True, 'color': hex_color(damage.get('color'), '{{c:dmg}}'), 'alpha': damage.get('alpha', 80),
                       'delay': 0, 'duration': damage.get('fade', 1)},
            'shadow': {'enabled': False}}


def position(options, defaults=None):
    result = {'enabled': options.get('enabled', True), 'x': options.get('x'), 'y': options.get('y'),
              'scale': 1, 'alpha': options.get('alpha', 100), 'deadAlpha': 100}
    result.update(defaults or {})
    return result


def icons(options):
    vehicle = options.get('vehicleIcon', {})
    contour = options.get('contourIcon', {})
    hover = options.get('hoverMarker', {})
    indicator = options.get('damageIndicator', {})
    x, y = indicator.get('x', 53), indicator.get('y', -27)
    return {'enabled': True,
            # XVM moves the icon container (marker.marker), plus its offset; it ignores maxScale.
            'class': {'enabled': vehicle.get('enabled', True), 'x': None, 'y': None, 'scale': 1,
                      'alpha': vehicle.get('alpha', 100), 'deadAlpha': 100,
                      'containerX': vehicle.get('x', 0) + vehicle.get('offsetX', 0),
                      'containerY': vehicle.get('y', -16) + vehicle.get('offsetY', 0),
                      'showSpeaker': bool(vehicle.get('showSpeaker', False))},
            'level': position(options.get('levelIcon', {'enabled': False})),
            'vehicle': position(contour, {'enabled': contour.get('enabled', False),
                                          'tint': {'color': contour.get('color') or '{{c:system}}',
                                                   'amount': contour.get('amount', 0)}}),
            'actionMarker': position(options.get('actionMarker', {})),
            'hoverMarker': position(hover, {'glow': copy.deepcopy(hover.get('glow', {'enabled': True}))}),
            'vehicleStatusMarker': position(options.get('vehicleStatusMarker', {})),
            'damageIndicator': position(indicator),
            'hitExplosion': position(indicator),
            'damageIndicatorText': position(indicator, {'enabled': bool(indicator.get('enabled', True) and indicator.get('showText', True)),
                                                        'x': x + 14, 'y': y - 14})}


def adapt(data):
    """XVM settings -> the internal schema consumed by validation, Python presentation and Flash."""
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
                level = options.get('levelIcon', {})
                contour = options.get('contourIcon', {})
                result['markers'][team][state][mode] = {
                    'vehicleName': False, 'playerName': False, 'hp': 'hidden', 'healthBar': False,
                    'vehicleIcon': bool(contour.get('enabled', False)), 'levelIcon': bool(level.get('enabled', False)),
                    'damage': True}
                if not enabled:
                    continue
                fields = [text_field(item) for item in options.get('textFields', []) if isinstance(item, dict)]
                distance = options.get('vehicleDist', {})
                if distance.get('enabled'):
                    fields.append(distance_field(distance))
                result['customFields'][team][state][mode] = fields
                result['healthBar'][team][state][mode] = health_bar(options.get('healthBar', {}), state == 'dead')
                other = damage_text(options.get('damageText', {}))
                result['damageText'][team][state][mode] = dict(other, sources={
                    'player': damage_text(options.get('damageTextPlayer', options.get('damageText', {}))),
                    'squad': damage_text(options.get('damageTextSquadman', options.get('damageText', {}))),
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
