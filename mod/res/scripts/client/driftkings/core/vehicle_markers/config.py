# -*- coding: utf-8 -*-
"""Prepare a validated runtime payload without rewriting editable JSON sections."""
import copy

from driftkings.core.vehicle_markers.colors import normalize as normalize_colors
from driftkings.core.vehicle_markers.colors import palette
from driftkings.core.vehicle_markers.damage import normalize as normalize_damage
from driftkings.core.vehicle_markers.fields import normalize
from driftkings.core.vehicle_markers.healthbar import normalize as normalize_healthbar
from driftkings.core.vehicle_markers.icons import normalize as normalize_icons
from driftkings.core.vehicle_markers.presentation import validate

DEFAULTS = {'enabled': False, 'debug': False, 'colorRating': 0, 'markers': {'enabled': False}, 'targetGameVersion': '2.4.1'}


def prepare(data):
    result = copy.deepcopy(DEFAULTS)
    result.update(data)
    if type(result['enabled']) is not bool or type(result['debug']) is not bool:
        raise ValueError('enabled/debug must be boolean')
    from driftkings.common.utils.color_rating_data import color_tables
    if type(result['colorRating']) is not int or not 0 <= result['colorRating'] < len(color_tables):
        raise ValueError('Invalid marker colorRating')
    shared = palette(result['colorRating'])
    validate(result.get('markers'))
    result['customFields'] = normalize(result.get('customFields', {'enabled': False}))
    result['colors'] = normalize_colors(result.get('colors', {}), shared['colors'])
    result['customFields']['colors'] = result['colors']
    damage = copy.deepcopy(result.get('damageText', {}))
    if not isinstance(damage, dict) or not isinstance(damage.get('colors', {}), dict):
        raise ValueError('Invalid marker damage colors')
    damage_colors = copy.deepcopy(shared['damageColors'])
    damage_colors.update(damage.get('colors', {}))
    damage['colors'] = damage_colors
    result['damageText'] = normalize_damage(damage)
    result['customFields']['damageText'] = result['damageText']
    result['healthBar'] = normalize_healthbar(result.get('healthBar', {}))
    result['customFields']['healthBar'] = result['healthBar']
    result['icons'] = normalize_icons(result.get('icons', {}))
    result['customFields']['icons'] = result['icons']
    if (result['icons']['enabled'] or result['customFields']['enabled'] or result['damageText']['enabled'] or result['healthBar']['enabled']) and not result['markers']['enabled']:
        raise ValueError('Custom fields require markers.enabled=true')
    return result
