# -*- coding: utf-8 -*-
"""Validate and normalize the deliberately small custom Flash field schema."""
import copy
import math
import re

from driftkings.core.vehicle_markers.expressions import validate as validate_expression
from driftkings.common.utils.compat import string_types

SHADOW = {'enabled': True, 'distance': 0, 'angle': 0, 'color': '0x000000',
          'alpha': 80, 'blur': 3, 'strength': 2}
TEXT_FORMAT = {'font': '$FieldFont', 'size': 13, 'color': None, 'bold': False, 'italic': False}
DEFAULTS = {'name': '', 'textFormat': TEXT_FORMAT, 'enabled': True, 'format': '{{vehicle}}', 'x': -100, 'y': -65,
            'width': 200, 'height': 25, 'alpha': 100, 'align': 'center', 'shadow': SHADOW}
MACROS = set(('vehicle', 'name', 'hp', 'maxHp', 'hpPercent', 'level', 'c:team', 'c:hp'))
MACROS.update(('r', 'xr', 'wn8', 'wnx', 'eff', 'xwn8', 'xeff', 'wgr', 'winrate', 'battles', 'kb',
               'xvm-stat', 'a:r', 'nick', 'clan', 'hp-max', 'hp-ratio', 'c:system'))
MACROS.update('c:' + key for key in ('r', 'xr', 'wn8', 'wnx', 'eff', 'xwn8', 'xeff', 'wgr', 'winrate', 'battles', 'kb'))
MACROS.update(('turret', 'stock-turret', 'turret-vulnerability', 'distance', 'dist', 'alive', 'dead', 'ally', 'enemy', 'player', 'squad', 'anonym', 'vtype'))
# XVM battle macros: {{battletype}} is empty in random battles, {{position}} is the team list order.
MACROS.update(('battletype', 'position'))


def template(value, extra_macros=()):
    if not isinstance(value, string_types) or len(value) > 2048:
        raise ValueError('Invalid field HTML format')
    validate_expression(value, MACROS | set(extra_macros))


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or math.isnan(value) or math.isinf(value) or not low <= value <= high:
        raise ValueError('Field numeric value outside range')


def normalize(options, extra_macros=()):
    if not isinstance(options, dict) or type(options.get('enabled', False)) is not bool:
        raise ValueError('customFields.enabled must be boolean')
    if set(options) - set(('enabled', 'ally', 'enemy', 'dead')):
        raise ValueError('Unknown custom field group')
    result = {'enabled': options.get('enabled', False)}
    for group in ('ally', 'enemy', 'dead'):
        modes = options.get(group, {})
        if not isinstance(modes, dict) or set(modes) - set(('normal', 'extended')):
            raise ValueError('Invalid custom field modes')
        result[group] = {}
        for mode, fields in modes.items():
            if not isinstance(fields, list) or len(fields) > 12:
                raise ValueError('Expected up to 12 custom fields per mode')
            result[group][mode] = []
            for values in fields:
                if not isinstance(values, dict) or set(values) - set(DEFAULTS):
                    raise ValueError('Unknown custom field property')
                field = copy.deepcopy(DEFAULTS)
                field.update(values)
                if type(field['enabled']) is not bool or field['align'] not in ('left', 'center', 'right'):
                    raise ValueError('Invalid custom field visibility/alignment')
                template(field['format'], extra_macros)
                if not isinstance(field['name'], string_types) or len(field['name']) > 128:
                    raise ValueError('Invalid field name')
                style = values.get('textFormat', {})
                if not isinstance(style, dict) or set(style) - set(TEXT_FORMAT):
                    raise ValueError('Invalid textFormat')
                field['textFormat'] = dict(TEXT_FORMAT, **style)
                style = field['textFormat']
                if not isinstance(style['font'], string_types) or not 1 <= len(style['font']) <= 128:
                    raise ValueError('Invalid field font')
                number(style['size'], 1, 100)
                if type(style['bold']) is not bool or type(style['italic']) is not bool:
                    raise ValueError('Invalid field font style')
                if style['color'] is not None:
                    if not isinstance(style['color'], string_types):
                        raise ValueError('Invalid font color')
                    if '{{' in style['color']:
                        template(style['color'], extra_macros)
                    elif not re.match(r'^(?:0x|#)[0-9a-fA-F]{6}\Z', style['color']):
                        raise ValueError('Invalid font color')
                for key in ('x', 'y'): number(field[key], -1000, 1000)
                for key in ('width', 'height'): number(field[key], 1, 1000)
                if isinstance(field['alpha'], string_types):
                    if '{{' not in field['alpha']:
                        raise ValueError('Expected opacity number or macro')
                    template(field['alpha'], extra_macros)
                else:
                    number(field['alpha'], 0, 100)
                shadow = values.get('shadow', {})
                if not isinstance(shadow, dict) or set(shadow) - set(SHADOW):
                    raise ValueError('Invalid field shadow')
                field['shadow'] = copy.deepcopy(SHADOW)
                field['shadow'].update(shadow)
                shadow = field['shadow']
                if type(shadow['enabled']) is not bool:
                    raise ValueError('Invalid shadow enabled')
                if not isinstance(shadow['color'], string_types):
                    raise ValueError('Invalid shadow color')
                if '{{' in shadow['color']:
                    template(shadow['color'], extra_macros)
                elif not re.match(r'^(?:0x|#)[0-9a-fA-F]{6}\Z', shadow['color']):
                    raise ValueError('Invalid shadow color')
                for key, low, high in (('distance', 0, 100), ('angle', -360, 360),
                                       ('alpha', 0, 100), ('blur', 0, 100), ('strength', 0, 100)):
                    number(shadow[key], low, high)
                result[group][mode].append(field)
    return result
