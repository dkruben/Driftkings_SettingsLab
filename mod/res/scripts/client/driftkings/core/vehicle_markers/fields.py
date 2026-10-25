# -*- coding: utf-8 -*-
"""Validate and normalize the deliberately small custom Flash field schema."""
import copy
import math
import re

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)

SHADOW = {'enabled': True, 'distance': 0, 'angle': 0, 'color': '0x000000',
          'alpha': 80, 'blur': 3, 'strength': 2}
DEFAULTS = {'enabled': True, 'format': '{{vehicle}}', 'x': -100, 'y': -65,
            'width': 200, 'height': 25, 'alpha': 100, 'align': 'center', 'shadow': SHADOW}
MACROS = set(('vehicle', 'name', 'hp', 'maxHp', 'hpPercent', 'level', 'c:team', 'c:hp'))


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
                template = field['format']
                if not isinstance(template, string_types) or len(template) > 2048:
                    raise ValueError('Invalid field HTML format')
                if set(re.findall(r'\{\{(.*?)\}\}', template)) - (MACROS | set(extra_macros)):
                    raise ValueError('Unsupported field macro')
                for key in ('x', 'y'): number(field[key], -1000, 1000)
                for key in ('width', 'height'): number(field[key], 1, 1000)
                number(field['alpha'], 0, 100)
                shadow = values.get('shadow', {})
                if not isinstance(shadow, dict) or set(shadow) - set(SHADOW):
                    raise ValueError('Invalid field shadow')
                field['shadow'] = copy.deepcopy(SHADOW)
                field['shadow'].update(shadow)
                shadow = field['shadow']
                if type(shadow['enabled']) is not bool:
                    raise ValueError('Invalid shadow enabled')
                if not isinstance(shadow['color'], string_types) or not re.match(r'^(?:0x|#)[0-9a-fA-F]{6}\Z', shadow['color']):
                    raise ValueError('Invalid shadow color')
                for key, low, high in (('distance', 0, 100), ('angle', -360, 360),
                                       ('alpha', 0, 100), ('blur', 0, 100), ('strength', 0, 100)):
                    number(shadow[key], low, high)
                result[group][mode].append(field)
    return result
