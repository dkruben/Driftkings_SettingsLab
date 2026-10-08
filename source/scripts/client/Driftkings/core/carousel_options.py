# -*- coding: utf-8 -*-
"""Supported options for the EU Gameface carousel integration."""
import copy

SORT_KEYS = ('nation', 'type', 'level', 'premium', 'battles', 'winRate', 'markOfMastery', 'damageRating', 'marksOnGun', 'battlePassPoints', 'wn8', 'avgDamage')
STAT_SORT_KEYS = ('battles', 'winRate', 'markOfMastery', 'damageRating', 'marksOnGun', 'wn8', 'avgDamage')


def defaults():
    from Driftkings.settings.settings_data import defaults as component_defaults
    data = component_defaults('CarouselStats')['carousel']
    return dict((key, value) for key, value in data.items() if key not in ('normal', 'small', 'rows', 'cellType'))


def from_carousel(carousel):
    return dict((key, copy.deepcopy(carousel.get(key, value))) for key, value in defaults().items())
