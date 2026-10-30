# -*- coding: utf-8 -*-
"""Presentation only: receives calculated MoE values, never acquires game data."""
from driftkings._constants import MARK_THRESHOLDS
from driftkings.common.utils.numbers import finite_number as finite
from driftkings.locale_support import language_code

ANCHORS = {'alignX': ('left', 'center', 'right'), 'alignY': ('top', 'center', 'bottom')}


def number_locale(language):
    """Number presentation for the same supported language as the panel labels."""
    code = language_code(language)
    if code in ('de', 'es', 'it', 'tr', 'vi'):
        decimal, group = ',', '.'
    elif code in ('cs', 'fr', 'hu', 'pl', 'pt', 'ru', 'uk'):
        decimal, group = ',', u'\u00a0'
    else:
        decimal, group = '.', ','
    return {'decimalSeparator': decimal, 'groupSeparator': group}


def moved_panel(panel, args):
    """Apply a dragged position; the anchor travels with it so a resolution change keeps the panel by its edge."""
    if not isinstance(args, dict):
        return None
    x, y = finite(args.get('x')), finite(args.get('y'))
    if x is None or y is None:
        return None
    panel = dict(panel)
    panel.update(x=max(-7680, min(7680, x)), y=max(-4320, min(4320, y)))
    for key, choices in ANCHORS.items():
        if args.get(key) in choices:
            panel[key] = args[key]
    return panel


def delta_model(value):
    value = finite(value)
    if value is None:
        return {'text': u'\u2014', 'direction': 'unknown'}
    value = round(value, 2)
    direction = 'positive' if value > 0 else 'negative' if value < 0 else 'zero'
    # Warhelios has no triangle glyphs: the sign and the direction colour carry the trend.
    return {'text': '%+.2f%%' % value if value else '0.00%', 'direction': direction}


def milestone_model(percent, earned=0):
    """Progress inside the next excellence interval, never percent/100."""
    percent = finite(percent)
    if percent is None:
        return {'nextMilestone': None, 'progress': 0, 'gap': None, 'completed': False}
    percent = max(0.0, min(100.0, percent))
    thresholds = MARK_THRESHOLDS
    achieved = max(int(finite(earned, 0)), sum(percent >= value for value in thresholds))
    if achieved >= 3:
        return {'nextMilestone': None, 'progress': 1, 'gap': 0, 'completed': True}
    low = (0, 65, 85)[achieved]
    high = thresholds[achieved]
    return {'nextMilestone': high, 'progress': max(0.0, min(1.0, (percent - low) / (high - low))),
            'gap': max(0.0, high - percent), 'completed': False}


def compact_model(vehicle_id, current, estimated, damage, assists, targets, earned=0, valid=True, approximate=False):
    """All numeric values are supplied by the calculation engine, not JS."""
    current, estimated = finite(current), finite(estimated)
    valid = bool(valid and current is not None and estimated is not None)
    result = {
        'state': 'data' if valid else 'unavailable', 'vehicleId': vehicle_id,
        'currentMark': current, 'estimatedMark': estimated if valid else None,
        'marksAchieved': max(0, min(3, int(finite(earned, 0)))),
        'directDamage': finite(damage, 0), 'assistance': list(assists),
        'combinedDamage': finite(damage, 0) + max(assists),
        'trend': delta_model(estimated - current if valid else None),
        'approximate': bool(approximate and valid)
    }
    result.update(milestone_model(estimated if valid else None, earned))
    target = targets.get(result['nextMilestone']) if valid else None
    result['targetDamage'] = target
    result['damageNeeded'] = max(0, target - result['combinedDamage']) if target is not None else None
    return result
