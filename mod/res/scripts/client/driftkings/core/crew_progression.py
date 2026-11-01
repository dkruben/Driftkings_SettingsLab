# -*- coding: utf-8 -*-
"""Crew progression arithmetic, independent of game imports and presentation."""
import math

from driftkings.common.utils.numbers import nonnegative_number as nonnegative


def progression(remaining_xp, average_xp, completed=False):
    """Estimate against native historical XP; never fabricate a minimum battle.

    The average is not a measurement of this tankman's effective crew XP.
    Accelerated training, reserves and vehicle bonuses can change the outcome.
    Native skill costs already account for free skills and available free XP.
    """
    result = {'state': 'unavailable', 'remainingXP': None,
              'averageXP': nonnegative(average_xp), 'estimatedBattles': None}
    if completed:
        result.update(state='complete', remainingXP=0, estimatedBattles=0)
        return result
    remaining = nonnegative(remaining_xp)
    if remaining is None:
        return result
    result['remainingXP'] = int(math.ceil(remaining))
    if remaining == 0:
        result.update(state='ready', estimatedBattles=0)
    else:
        result['state'] = 'training'
        average = result['averageXP']
        if average is not None and average > 0:
            estimate = remaining / average
            if not math.isinf(estimate):
                result['estimatedBattles'] = int(math.ceil(estimate))
    return result
