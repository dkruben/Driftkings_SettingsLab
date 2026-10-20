# -*- coding: utf-8 -*-
"""Pure XVM scale maths (0-100 ranks); no game-engine imports, so it is testable off-client.

Every function returns -1 when the reference data is missing or malformed.
"""

TOP = 100
DAMAGE_WEIGHT = 3.0
FRAG_WEIGHT = 1.0
FLOOR_RATIO = 0.4


def rank(thresholds, value):
    """Index of the first threshold greater than value, or TOP; -1 without usable thresholds."""
    if not isinstance(thresholds, (list, tuple)):
        return -1
    try:
        for index, limit in enumerate(thresholds):
            if limit > value:
                return index
    except TypeError:
        return -1
    return TOP


def _component(value, average, top):
    if value >= average:
        return 1 + (value - average) / (top - average)
    return 1 + (value - average) / (average - average * FLOOR_RATIO)


def xte(data, damage_per_battle, frags_per_battle):
    """Expected-tank-efficiency rank from the vehicle reference record {ad, td, af, tf, x}."""
    try:
        avg_d, top_d = float(data['ad']), float(data['td'])
        avg_f, top_f = float(data['af']), float(data['tf'])
        if top_d == avg_d or top_f == avg_f:
            return -1
        d = max(0, _component(damage_per_battle, avg_d, top_d))
        f = max(0, _component(frags_per_battle, avg_f, top_f))
        score = (d * DAMAGE_WEIGHT + f * FRAG_WEIGHT) / (DAMAGE_WEIGHT + FRAG_WEIGHT) * 1000.0
        return rank(data['x'], score)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return -1


def xtdb(data, damage_per_battle):
    """Expected-tank-damage-per-battle rank from the vehicle reference record {x}."""
    try:
        return rank(data['x'], damage_per_battle)
    except (KeyError, TypeError):
        return -1
