# -*- coding: utf-8 -*-
"""Native marker class/level/contour icon presentation; no asset replacement."""
import copy

from driftkings.core.vehicle_markers.fields import number

INDICATORS = ('actionMarker', 'hoverMarker', 'vehicleStatusMarker', 'damageIndicator', 'damageIndicatorText', 'hitExplosion')
KEYS = ('class', 'level', 'vehicle') + INDICATORS

STYLE = {'enabled': True, 'x': None, 'y': None, 'scale': 1, 'alpha': 100, 'deadAlpha': 40}


def normalize(options):
    if not isinstance(options, dict) or set(options) - set(('enabled',) + KEYS):
        raise ValueError('Invalid icons options')
    enabled = options.get('enabled', False)
    if type(enabled) is not bool:
        raise ValueError('icons.enabled must be boolean')
    result = {'enabled': enabled}
    for key in KEYS:
        values = options.get(key, {})
        if not isinstance(values, dict) or set(values) - set(STYLE):
            raise ValueError('Invalid icon style: ' + key)
        style = copy.deepcopy(STYLE)
        if key == 'vehicle':
            style.update(enabled=False, x=-55, y=-18)
        if key in INDICATORS: style['deadAlpha'] = 100
        style.update(values)
        if type(style['enabled']) is not bool:
            raise ValueError('Icon enabled must be boolean')
        for axis in ('x', 'y'):
            if style[axis] is not None: number(style[axis], -500, 500)
        number(style['scale'], .25, 3)
        number(style['alpha'], 0, 100)
        number(style['deadAlpha'], 0, 100)
        result[key] = style
    return result
