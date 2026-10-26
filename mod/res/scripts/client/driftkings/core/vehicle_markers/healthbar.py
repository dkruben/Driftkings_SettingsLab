# -*- coding: utf-8 -*-
"""Custom health bar configuration; disabled defaults preserve the native bar."""
import copy

from driftkings.core.vehicle_markers.colors import color
from driftkings.core.vehicle_markers.fields import normalize as normalize_fields
from driftkings.core.vehicle_markers.fields import number, string_types

DEFAULTS = {'enabled': False, 'x': -35, 'y': -22, 'width': 70, 'height': 8,
            'alpha': 100, 'color': '{{c:team}}', 'showOnDead': False,
            'fill': {'alpha': 100},
            'gradient': {'enabled': False, 'color': '{{c:hp}}', 'angle': 0},
            'background': {'color': '#181818', 'alpha': 80},
            'border': {'color': '#000000', 'alpha': 100, 'width': 1},
            'damage': {'enabled': False, 'color': '#FFDD66', 'alpha': 65, 'delay': .25, 'duration': .75},
            'shadow': {'enabled': True, 'distance': 0, 'angle': 0, 'color': '0x000000',
                       'alpha': 70, 'blur': 2, 'strength': 2}}


def normalize(options):
    if not isinstance(options, dict) or set(options) - set(DEFAULTS):
        raise ValueError('Invalid healthBar options')
    result = copy.deepcopy(DEFAULTS)
    result.update(options)
    for key in ('enabled', 'showOnDead'):
        if type(result[key]) is not bool:
            raise ValueError('healthBar switches must be boolean')
    for key in ('x', 'y'): number(result[key], -1000, 1000)
    number(result['width'], 4, 500)
    number(result['height'], 2, 100)
    number(result['alpha'], 0, 100)
    if not isinstance(result['color'], string_types):
        raise ValueError('Invalid bar colour')
    if result['color'] not in ('{{c:hp}}', '{{c:team}}'): color(result['color'])
    for name in ('fill', 'gradient', 'background', 'border'):
        values = options.get(name, {})
        if not isinstance(values, dict) or set(values) - set(DEFAULTS[name]):
            raise ValueError('Invalid healthBar ' + name)
        result[name] = copy.deepcopy(DEFAULTS[name])
        result[name].update(values)
        if 'color' in result[name] and not (name == 'gradient' and result[name]['color'] in ('{{c:hp}}', '{{c:team}}')):
            color(result[name]['color'])
        if 'alpha' in result[name]: number(result[name]['alpha'], 0, 100)
    if type(result['gradient']['enabled']) is not bool:
        raise ValueError('Gradient enabled must be boolean')
    number(result['gradient']['angle'], -360, 360)
    number(result['border']['width'], 0, 10)
    if result['border']['width'] * 2 >= min(result['width'], result['height']):
        raise ValueError('Bar border leaves no interior')
    damage = options.get('damage', {})
    if not isinstance(damage, dict) or set(damage) - set(DEFAULTS['damage']):
        raise ValueError('Invalid healthBar damage trail')
    result['damage'] = copy.deepcopy(DEFAULTS['damage'])
    result['damage'].update(damage)
    damage = result['damage']
    if type(damage['enabled']) is not bool:
        raise ValueError('Trail enabled must be boolean')
    if damage['color'] != '{{c:dmg}}': color(damage['color'])
    number(damage['alpha'], 0, 100)
    number(damage['delay'], 0, 5)
    number(damage['duration'], .1, 5)
    # Reuse the field shadow validation and defaults without copying its text style.
    shadow = options.get('shadow', {})
    if not isinstance(shadow, dict):
        raise ValueError('Invalid healthBar shadow')
    merged_shadow = copy.deepcopy(DEFAULTS['shadow'])
    merged_shadow.update(shadow)
    field = normalize_fields({'enabled': True, 'ally': {'normal': [
        {'shadow': merged_shadow}]}})['ally']['normal'][0]
    result['shadow'] = field['shadow']
    return result
