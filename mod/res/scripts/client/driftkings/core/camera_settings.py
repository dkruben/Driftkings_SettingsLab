# -*- coding: utf-8 -*-
"""Mode-specific camera options, independent of the client."""
import math

from driftkings._constants import THIRD_PERSON_ZOOM


def validate(values):
    for mode in THIRD_PERSON_ZOOM.MODES:
        options = values[mode]
        for key in ('min', 'max', 'scrollSensitivity'):
            value = options[key]
            if type(value) not in (int, float) or math.isnan(value) or math.isinf(value):
                raise ValueError('Invalid camera value: ' + mode + '.' + key)
        if not 1 <= options['min'] <= options['max'] <= 450:
            raise ValueError('Invalid camera distance range: ' + mode)
        if not 1 <= options['scrollSensitivity'] <= 100:
            raise ValueError('Invalid camera scroll sensitivity: ' + mode)
        if mode in ('arcade', 'postmortem'):
            value = options['startDist']
            if type(value) not in (int, float) or not options['min'] <= value <= options['max']:
                raise ValueError('Start distance must be inside the camera range: ' + mode)
        elif type(options['useClientDefaults']) is not bool:
            raise ValueError('Invalid native camera switch: ' + mode)
    return values


def options(values, mode):
    if not values['enabled']:
        return None
    result = values[mode]
    return None if result.get('useClientDefaults', False) else result
