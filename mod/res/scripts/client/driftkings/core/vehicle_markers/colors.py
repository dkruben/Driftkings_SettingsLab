# -*- coding: utf-8 -*-
"""JSON colour scale validation for the Flash marker fields."""
import copy
import re

from driftkings.core.vehicle_markers.fields import number, string_types

DEFAULTS = {'colorBlind': {'enabled': True, 'team': {'enemy': '#C48CFF', 'teamKiller': '#66CCFF'}},
            'team': {'allyDead': '#B8FFC1', 'enemyDead': '#E29188', 'squadDead': '#CA7000', 'teamKillerDead': '#097783', 'ally': '#99CC66', 'enemy': '#FF7777', 'squad': '#FFCC66',
                     'teamKiller': '#66CCFF', 'dead': '#AAAAAA', 'unknown': '#CCCCCC'},
            'hp': [{'value': 25, 'color': '#FF5555'}, {'value': 50, 'color': '#FFAA44'},
                   {'value': 75, 'color': '#FFDD66'}, {'value': 100, 'color': '#99CC66'}]}


def color(value):
    if not isinstance(value, string_types) or not re.match(r'^#[0-9A-Fa-f]{6}\Z', value):
        raise ValueError('Marker colours must use #RRGGBB')


def palette(index=0):
    """Use the same resolved resources as every other colorRating consumer."""
    from driftkings.common.utils.colorratting import getRatingColors
    source = getRatingColors(index)
    system = source['system']
    missing = source['colorRating']['nocolor']
    return {'colors': {'team': {'allyDead': system['ally_dead'], 'enemyDead': system['enemy_dead'], 'squadDead': system['squadman_dead'], 'teamKillerDead': system['teamKiller_dead'], 'ally': system['ally_alive'], 'enemy': system['enemy_alive'],
                               'squad': system['squadman_alive'], 'teamKiller': system['teamKiller_alive'],
                               'dead': missing, 'unknown': missing},
                       'hp': copy.deepcopy(source['hp_ratio'])},
            'damageColors': {'player': source['damage']['player_enemy_hit'],
                             'squad': source['damage']['squadman_enemy_hit'],
                             'other': source['damage']['unknown_enemy_hit']}}


def normalize(options, base=None):
    if not isinstance(options, dict) or set(options) - set(DEFAULTS):
        raise ValueError('Invalid marker colours')
    result = copy.deepcopy(DEFAULTS)
    if base is not None:
        result.update(copy.deepcopy(base))
    teams = options.get('team', {})
    if not isinstance(teams, dict) or set(teams) - set(DEFAULTS['team']):
        raise ValueError('Invalid team colour keys')
    result['team'].update(teams)
    for value in result['team'].values(): color(value)
    blind = options.get('colorBlind', {})
    if not isinstance(blind, dict) or set(blind) - set(('enabled', 'team')):
        raise ValueError('Invalid colorBlind palette')
    blind_enabled = blind.get('enabled', DEFAULTS['colorBlind']['enabled'])
    if type(blind_enabled) is not bool:
        raise ValueError('colorBlind.enabled must be boolean')
    overrides = blind.get('team', DEFAULTS['colorBlind']['team'])
    if not isinstance(overrides, dict) or set(overrides) - set(DEFAULTS['team']):
        raise ValueError('Invalid colorBlind team keys')
    blind_team = copy.deepcopy(result['team'])
    blind_team.update(overrides)
    if 'enemy' in overrides and 'enemyDead' not in overrides:
        blind_team['enemyDead'] = overrides['enemy']
    for value in blind_team.values(): color(value)
    result['colorBlind'] = {'enabled': blind_enabled, 'team': blind_team}
    bands = options.get('hp', result['hp'])
    if not isinstance(bands, list) or not 1 <= len(bands) <= 20:
        raise ValueError('Expected 1 to 20 HP colour bands')
    previous = -1
    for band in bands:
        if not isinstance(band, dict) or set(band) != set(('value', 'color')):
            raise ValueError('Invalid HP colour band')
        number(band['value'], 0, 1e30)
        if band['value'] <= previous:
            raise ValueError('HP colour limits must be strictly increasing')
        previous = band['value']
        color(band['color'])
    if previous < 100:
        raise ValueError('Last HP colour limit must cover 100 percent')
    result['hp'] = copy.deepcopy(bands)
    return result
