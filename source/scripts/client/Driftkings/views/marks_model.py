# -*- coding: utf-8 -*-
"""Presentation only: receives calculated MoE values, never acquires game data."""
import math

TOKENS = {'background': 0x121518, 'border': 0xFFFFFF, 'text': 0xE8E4DA,
          'muted': 0x969BA3, 'positive': 0x67C56A, 'negative': 0xE05454,
          'accent': 0xD98219, 'backgroundAlpha': 0.75, 'borderAlpha': 0.10}


def finite(value, default=None):
    try:
        value = float(value)
        return default if math.isnan(value) or math.isinf(value) else value
    except (ValueError, TypeError, OverflowError):
        return default


def delta_model(value):
    value = finite(value)
    if value is None:
        return {'text': u'\u2014', 'direction': 'unknown'}
    value = round(value, 2)
    direction = 'positive' if value > 0 else 'negative' if value < 0 else 'zero'
    symbol = u'\u25b2' if value > 0 else u'\u25bc' if value < 0 else u'\u2014'
    return {'text': symbol + ' ' + ('%+.2f%%' % value if value else '0.00%'), 'direction': direction}


def battle_model(current, estimated, damage, assist, combined, target, target_percent,
                 earned_marks, targets, unknown=False, labels=None):
    labels = labels or {}
    current, estimated = finite(current), finite(estimated)
    valid = not unknown and current is not None and estimated is not None
    percent = max(0.0, min(100.0, estimated)) if valid else None
    target = finite(target)
    target = None if target is None or target >= 30000 else target
    marks = max(0, min(3, int(finite(earned_marks, 0))))
    result = {'percent': '%.2f%%' % percent if percent is not None else '--',
              'currentPercent': '%.2f%%' % current if current is not None else '--',
              'progress': percent / 100.0 if percent is not None else 0,
              'delta': delta_model(estimated - current if valid else None),
              'marks': u'\u2605' * marks + u'\u2606' * (3-marks),
              'damage': '%.0f' % finite(damage, 0), 'assist': '%.0f' % finite(assist, 0),
              'combined': '%.0f' % finite(combined, 0), 'target': '%.0f' % target if target is not None else '--',
              'targetState': 'unknown' if target is None or finite(combined) is None else 'below' if combined < target else 'reached' if combined == target else 'above',
              'targetPercent': target_percent, 'targets': [], 'tokens': dict(TOKENS), 'labels': dict(labels)}
    for threshold, value in zip((65,85,95), targets):
        value = finite(value)
        result['targets'].append({'percent': threshold, 'text': '%.0f' % value if value is not None and value < 30000 else '--'})
    return result
