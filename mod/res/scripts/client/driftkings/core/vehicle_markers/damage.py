# -*- coding: utf-8 -*-
"""Floating damage defaults and independent author overrides inside each context."""
import copy

from driftkings.core.vehicle_markers.colors import color
from driftkings.core.vehicle_markers.fields import DEFAULTS
from driftkings.core.vehicle_markers.fields import normalize as normalize_fields
from driftkings.core.vehicle_markers.fields import number, template
from driftkings.core.vehicle_markers.layouts import merge

SOURCES = ('player', 'squad', 'other')
EVENT_MACROS = ('dmg', 'c:dmg', 'dmg-ratio', 'dmg-kind', 'dmg-source', 'blownUp', 'l10n:blownUp')

DEFAULTS_DAMAGE = {'enabled': False, 'duration': 2, 'rise': 40, 'maxCount': 4,
                  'blowupMessage': "<font size='18' color='{{c:dmg}}'><b>{{l10n:blownUp}}\n-{{dmg}}</b></font>",
                  'format': "<font size='18' color='{{c:dmg}}'><b>-{{dmg}}</b></font>",
                  'x': -100, 'y': -95, 'width': 200, 'height': 30,
                  'colors': {'player': '#FFDD66', 'squad': '#FFAA44', 'other': '#FFFFFF'}}


def style(options):
    allowed = set(DEFAULTS) | set(('duration', 'rise', 'maxCount', 'colors', 'blowupMessage'))
    if not isinstance(options, dict) or set(options) - allowed:
        raise ValueError('Invalid damageText options')
    result = copy.deepcopy(DEFAULTS_DAMAGE)
    result.update(options)
    number(result['duration'], .1, 10)
    number(result['rise'], 0, 300)
    if type(result['maxCount']) is not int or not 1 <= result['maxCount'] <= 12:
        raise ValueError('damageText.maxCount must be an integer from 1 to 12')
    colors = options.get('colors', {})
    if not isinstance(colors, dict) or set(colors) - set(DEFAULTS_DAMAGE['colors']):
        raise ValueError('Invalid damageText colors')
    result['colors'] = copy.deepcopy(DEFAULTS_DAMAGE['colors'])
    result['colors'].update(colors)
    for value in result['colors'].values(): color(value)
    style = dict((key, result[key]) for key in DEFAULTS if key in result)
    normalized = normalize_fields({'enabled': True, 'ally': {'normal': [style]}}, EVENT_MACROS)
    template(result['blowupMessage'], EVENT_MACROS)
    result.update(normalized['ally']['normal'][0])
    return result


def normalize(options):
    if not isinstance(options, dict):
        raise ValueError('Invalid damageText options')
    base = dict((key, value) for key, value in options.items() if key != 'sources')
    sources = options.get('sources', {})
    if not isinstance(sources, dict) or set(sources) - set(SOURCES):
        raise ValueError('Invalid damage authors')
    result = style(base)
    result['sources'] = {}
    for source in SOURCES:
        override = sources.get(source, {})
        if not isinstance(override, dict):
            raise ValueError('Invalid damage author style')
        result['sources'][source] = style(merge(base, override))
    return result
