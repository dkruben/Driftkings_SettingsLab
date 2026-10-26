# -*- coding: utf-8 -*-
"""Prepare a validated runtime payload without rewriting editable JSON sections."""
import copy

from driftkings.core.vehicle_markers.colors import normalize as normalize_colors
from driftkings.core.vehicle_markers.colors import palette
from driftkings.core.vehicle_markers.damage import normalize as normalize_damage
from driftkings.core.vehicle_markers.fields import normalize
from driftkings.core.vehicle_markers.healthbar import normalize as normalize_healthbar
from driftkings.core.vehicle_markers.icons import normalize as normalize_icons
from driftkings.core.vehicle_markers.layouts import leaf, migrate, MODES, STATES, style_tree, TEAMS, validate_tree
from driftkings.core.vehicle_markers.presentation import validate
from driftkings.core.vehicle_markers.references import resolve
from driftkings.core.vehicle_markers.xvm import adapt, STATE_KEYS

DEFAULTS = {'enabled': False, 'debug': False, 'colorRating': 0, 'markers': {'enabled': False}, 'targetGameVersion': '2.4.1'}


def prepare(data):
    if STATE_KEYS[0] in data:
        data = adapt(data)
    result = copy.deepcopy(DEFAULTS)
    result.update(migrate(resolve(data)))
    if not isinstance(result.get('def', {}), dict):
        raise ValueError('Marker templates must be an object')
    result.setdefault('turretMarkers', {'highVulnerability': '*', 'lowVulnerability': "'", 'unknown': '?'})
    if not isinstance(result['turretMarkers'], dict) or set(result['turretMarkers']) - set(('highVulnerability', 'lowVulnerability', 'unknown')):
        raise ValueError('Invalid turret marker strings')
    defaults = {'highVulnerability': '*', 'lowVulnerability': "'", 'unknown': '?'}
    defaults.update(result['turretMarkers'])
    result['turretMarkers'] = defaults
    from driftkings.core.vehicle_markers.fields import string_types
    if any(not isinstance(value, string_types) or len(value) > 32 for value in result['turretMarkers'].values()):
        raise ValueError('Invalid turret marker string')
    if type(result['enabled']) is not bool or type(result['debug']) is not bool:
        raise ValueError('enabled/debug must be boolean')
    result.setdefault('ratingType', 'wn8')
    if result['ratingType'] not in ('wn8', 'wnx', 'eff'):
        raise ValueError('Invalid marker rating type')
    from driftkings.common.utils.color_rating_data import color_tables
    if type(result['colorRating']) is not int or not 0 <= result['colorRating'] < len(color_tables):
        raise ValueError('Invalid marker colorRating')
    shared = palette(result['colorRating'])
    markers = result['markers']
    fields = result['customFields']
    for block in (markers, fields):
        if not isinstance(block, dict) or set(block) - set(('enabled',) + TEAMS) or type(block.get('enabled', False)) is not bool:
            raise ValueError('Invalid scoped marker layout')
        for team in TEAMS:
            validate_tree(block.get(team, {}))
    result['colors'] = normalize_colors(result.get('colors', {}), shared['colors'])
    result['customFields']['colors'] = result['colors']
    def damage_style(options):
        damage = copy.deepcopy(options)
        if not isinstance(damage, dict) or not isinstance(damage.get('colors', {}), dict):
            raise ValueError('Invalid marker damage colors')
        damage_colors = copy.deepcopy(shared['damageColors'])
        damage_colors.update(damage.get('colors', {}))
        damage['colors'] = damage_colors
        return normalize_damage(damage)
    result['damageText'], damage_scopes = style_tree(result['damageText'], damage_style)
    result['customFields']['damageText'] = result['damageText']
    result['healthBar'], bar_scopes = style_tree(result['healthBar'], normalize_healthbar)
    result['customFields']['healthBar'] = result['healthBar']
    result['icons'], icon_scopes = style_tree(result['icons'], normalize_icons)
    result['customFields']['icons'] = result['icons']
    profiles = {}
    for team in TEAMS:
        profiles[team] = {}
        for state in STATES:
            profiles[team][state] = {}
            for mode in MODES:
                native = leaf(markers, team, state, mode, {})
                validate({'enabled': True, 'ally': {'normal': native}})
                raw_fields = leaf(fields, team, state, mode)
                normalized_fields = None if raw_fields is None else normalize(
                    {'enabled': True, 'ally': {'normal': raw_fields}})['ally']['normal']
                if normalized_fields is not None:
                    fields[team][state][mode] = normalized_fields
                profile = {'native': copy.deepcopy(native),
                           'enabled': fields.get('enabled', False), 'fields': normalized_fields,
                           'damageText': damage_scopes[team][state][mode],
                           'healthBar': bar_scopes[team][state][mode], 'icons': icon_scopes[team][state][mode]}
                profiles[team][state][mode] = profile
                active_damage = any(style['enabled'] for style in profile['damageText']['sources'].values())
                if (profile['enabled'] or active_damage or any(profile[name]['enabled'] for name in ('healthBar', 'damageText', 'icons'))) and not markers['enabled']:
                    raise ValueError('Custom styles require markers.enabled=true')
    result['customFields']['turretMarkers'] = result['turretMarkers']
    result['customFields']['profiles'] = profiles
    result['customFields']['schemaVersion'] = 2
    return result
