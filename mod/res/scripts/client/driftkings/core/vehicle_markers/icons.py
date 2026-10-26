# -*- coding: utf-8 -*-
"""Native marker class/level/contour icon presentation; no asset replacement."""
import copy
import re

from driftkings.core.vehicle_markers.fields import number, string_types

INDICATORS = ('actionMarker', 'hoverMarker', 'vehicleStatusMarker', 'damageIndicator', 'damageIndicatorText', 'hitExplosion')
KEYS = ('class', 'level', 'vehicle') + INDICATORS

STYLE = {'enabled': True, 'x': None, 'y': None, 'scale': 1, 'alpha': 100, 'deadAlpha': 40}
# XVM-only options, per icon: the class icon container position and speaker, contour tint, hover glow.
EXTRA = {'class': {'containerX': None, 'containerY': None, 'showSpeaker': False},
         'vehicle': {'tint': {'color': '{{c:system}}', 'amount': 0}},
         'hoverMarker': {'glow': {'enabled': True, 'x': None, 'y': None, 'alpha': 100}}}


def normalize(options):
    if not isinstance(options, dict) or set(options) - set(('enabled',) + KEYS):
        raise ValueError('Invalid icons options')
    enabled = options.get('enabled', False)
    if type(enabled) is not bool:
        raise ValueError('icons.enabled must be boolean')
    result = {'enabled': enabled}
    for key in KEYS:
        values = options.get(key, {})
        extra = EXTRA.get(key, {})
        if not isinstance(values, dict) or set(values) - set(STYLE) - set(extra):
            raise ValueError('Invalid icon style: ' + key)
        style = copy.deepcopy(STYLE)
        style.update(copy.deepcopy(extra))
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
        for axis in ('containerX', 'containerY'):
            if style.get(axis) is not None: number(style[axis], -500, 500)
        if 'showSpeaker' in style and type(style['showSpeaker']) is not bool:
            raise ValueError('showSpeaker must be boolean')
        if 'tint' in style:
            tint = dict(EXTRA['vehicle']['tint'], **style['tint']) if isinstance(style['tint'], dict) else None
            if tint is None or set(tint) - set(EXTRA['vehicle']['tint']):
                raise ValueError('Invalid contour tint')
            number(tint['amount'], 0, 100)
            if not isinstance(tint['color'], string_types) or not ('{{' in tint['color'] or re.match(r'^(?:0x|#)[0-9a-fA-F]{6}$', tint['color'])):
                raise ValueError('Invalid contour tint colour')
            style['tint'] = tint
        if 'glow' in style:
            glow = dict(EXTRA['hoverMarker']['glow'], **style['glow']) if isinstance(style['glow'], dict) else None
            if glow is None or set(glow) - set(EXTRA['hoverMarker']['glow']) or type(glow['enabled']) is not bool:
                raise ValueError('Invalid hover glow')
            for axis in ('x', 'y'):
                if glow[axis] is not None: number(glow[axis], -500, 500)
            number(glow['alpha'], 0, 100)
            style['glow'] = glow
        result[key] = style
    return result
