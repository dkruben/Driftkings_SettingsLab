# -*- coding: utf-8 -*-
"""Feed the existing statistics cache to native marker names; no parallel HTTP worker."""
from driftkings.common.utils.colorratting import getStatisticColor
from driftkings.common.utils.numbers import nonnegative_number as numeric

METRICS = ('wn8', 'wnx', 'eff', 'xwn8', 'xeff', 'wgr', 'winrate', 'battles')


def values(info, rating='wn8', scale=0, minimum=1, anonymized=False):
    info = info or {}
    available = not anonymized and (numeric(info.get('battles')) or 0) >= max(1, minimum)
    result = {}
    for metric in METRICS:
        value = numeric(info.get(metric)) if available else None
        result[metric] = value
        result['c:' + metric] = getStatisticColor(metric, value, scale)
    result['r'] = result[rating]
    result['xr'] = result.get({'wn8': 'xwn8', 'eff': 'xeff'}.get(rating, ''))
    result['c:r'] = result['c:xr'] = result['c:' + rating]
    result['stat-available'] = available and result['r'] is not None
    result['a:r'] = 100 if result['stat-available'] else 0
    result['kb'] = result['battles'] / 1000.0 if result['battles'] is not None else None
    result['c:kb'] = result['c:battles']
    return result
