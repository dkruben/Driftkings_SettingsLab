# -*- coding: utf-8 -*-
"""Independent team/state/mode layouts and lossless conversion of the first schema."""
import copy

from driftkings._constants import VEHICLE_MARKERS

TEAMS = VEHICLE_MARKERS.TEAMS
STATES = VEHICLE_MARKERS.STATES
MODES = VEHICLE_MARKERS.MODES


def merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def migrate(data):
    if not isinstance(data, dict):
        raise ValueError('Expected vehicle marker settings object')
    result = copy.deepcopy(data)
    version = result.get('schemaVersion', 1)
    if type(version) is not int or version not in (1, 2):
        raise ValueError('Unsupported vehicle marker schema')
    if version == 2:
        return result
    for key in ('markers', 'customFields'):
        source = result.get(key, {'enabled': False})
        if not isinstance(source, dict):
            raise ValueError('Invalid marker layout: ' + key)
        converted = dict((name, copy.deepcopy(value)) for name, value in source.items()
                         if name not in TEAMS + ('dead',))
        for team in TEAMS:
            old = source.get(team, {})
            converted[team] = copy.deepcopy(old) if isinstance(old, dict) and ('alive' in old or 'dead' in old) else {
                'alive': copy.deepcopy(old), 'dead': copy.deepcopy(source.get('dead', {}))}
        result[key] = converted
    for key in ('healthBar', 'damageText', 'icons'):
        source = result.setdefault(key, {})
        if not isinstance(source, dict):
            raise ValueError('Invalid marker style: ' + key)
        for team in TEAMS:
            source.setdefault(team, dict((state, dict((mode, {}) for mode in MODES)) for state in STATES))
    result['schemaVersion'] = 2
    return result


def validate_tree(value):
    if not isinstance(value, dict) or set(value) - set(STATES):
        raise ValueError('Expected alive/dead marker states')
    for state in value.values():
        if not isinstance(state, dict) or set(state) - set(MODES):
            raise ValueError('Expected normal/extended marker modes')


def leaf(value, team, state, mode, default=None):
    return value.get(team, {}).get(state, {}).get(mode, default)


def style_tree(value, normalize):
    """Root properties are shared defaults; scoped overrides never affect siblings."""
    if not isinstance(value, dict):
        raise ValueError('Invalid scoped marker style')
    base = dict((key, item) for key, item in value.items() if key not in TEAMS)
    normalized = normalize(base)
    scopes = {}
    for team in TEAMS:
        validate_tree(value.get(team, {}))
        scopes[team] = {}
        for state in STATES:
            scopes[team][state] = {}
            for mode in MODES:
                override = leaf(value, team, state, mode, {})
                if not isinstance(override, dict):
                    raise ValueError('Expected a marker style object')
                scopes[team][state][mode] = normalize(merge(base, override))
    return normalized, scopes
