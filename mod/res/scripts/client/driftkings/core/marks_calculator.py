# -*- coding: utf-8 -*-
"""Only arithmetic proven identical in the existing Battle/Hangar paths."""
import math

from driftkings._constants import BattleCurve, MARK_LEVELS
from driftkings._constants import MARK_THRESHOLDS as THRESHOLDS
from driftkings._constants import MARKS_MIN_TIER, MarksStatistics
from driftkings.common.utils.numbers import finite_number


def valid_calibration(values):
    if not isinstance(values, list) or len(values) not in (4, 6):
        return False
    return all(type(value) in (int, float) and not math.isnan(value) and
               not math.isinf(value) for value in values) and (
        0 <= values[0] <= 100 and 0 <= values[2] <= 100 and values[1] >= 0 and values[3] > 0)


def replay_calibration(cache, owner, name, base_percent, base_damage, today):
    """Replays carry no dossier: prefer the owner's cache, then any account's, then the configured base.

    Returns (values, approximate). Borrowed values are copies so the owner's cache is never touched.
    """
    if valid_calibration((cache.get(owner) or {}).get(name)):
        return cache[owner][name], False
    borrowed = [values for account, vehicles in cache.items() if account != owner and isinstance(vehicles, dict)
                for values in [vehicles.get(name)] if valid_calibration(values) and values[1] != values[3]]
    if borrowed:
        values = list(max(borrowed, key=lambda item: item[5] if len(item) == 6 else 0))
        return values + [today, today][len(values) - 4:], True
    percent, damage = finite_number(base_percent, None), finite_number(base_damage, None)
    if percent is not None and damage is not None and 0 < percent <= 100 and damage > 0:
        return [0, 0, float(percent), float(damage), today, today], True
    return None, False


def ceil_damage(value):
    return int(math.ceil(value))


def ceil_damage_tens(value):
    return int(math.ceil(math.ceil(value / 10.0)) * 10)


def combined_damage(damage, *assists):
    return damage + max(assists)


def battle_target(percent, calibration, limit=30000):
    """The existing battle loop, evaluated at an excellence milestone."""
    p0, d0, p1, d1 = calibration[:4]
    if d1 == d0 or p1 <= p0 or percent is None:
        return None
    damage = 0
    ema = (1 - EMA_WEIGHT) * d1
    start = p0 + (ema - d0) / (d1 - d0) * (p1 - p0)
    while start <= percent < 100.001 and 0 <= start <= 100 and damage < limit:
        damage += 1
        ema = EMA_WEIGHT * damage + (1 - EMA_WEIGHT) * d1
        start = p0 + (ema - d0) / (d1 - d0) * (p1 - p0)
    return damage if damage < limit and start > percent else None


EMA_WEIGHT = 0.0198019801980198022206547392443098942749202251434326171875


def battle_estimate(damage, moving_average, calibration):
    p0, d0, p1, d1 = calibration[:4]
    ema = EMA_WEIGHT * damage + (1 - EMA_WEIGHT) * moving_average
    result = p0 + (ema - d0) / (d1 - d0) * (p1 - p0)
    return round(min(100.0, result), 2) if result > 0.0 else 0.0


def battle_curve(calibration, percent, moving_average, half_steps=False):
    """Preserve the old integer-damage stepping and half-percent boundaries."""
    p0, d0, p1, d1 = calibration[:4]
    stats = statistics(percent, moving_average)
    limit = min(30000, stats[-1] * 5)
    damage = 0
    ema = (1 - EMA_WEIGHT) * d1
    start = p0 + (ema - d0) / (d1 - d0) * (p1 - p0)
    levels, damages = [start], [damage]
    next_percent = float(int(p1 + 1))
    targets = [(p1, 100.001)]
    if half_steps and next_percent - p1 >= 0.5:
        targets.append((next_percent - 0.5, 100))
    for offset in range(6):
        targets.append((next_percent + offset, 100.001))
        if half_steps:
            targets.append((next_percent + offset + 0.5, 100.001))
    for target, bound in targets:
        while start <= target < bound and 0 <= start <= 100 and damage < limit:
            damage += 1
            ema = EMA_WEIGHT * damage + (1 - EMA_WEIGHT) * d1
            start = p0 + (ema - d0) / (d1 - d0) * (p1 - p0)
        levels.append(target)
        damages.append(damage)
    return BattleCurve(levels, damages, stats, damages[1], damages[1] < limit, damage >= min(30000, damage * 5))


def threshold_damage(ema, start, end, d, p):
    while start <= end < 100.001 and ema < 30000:
        ema += 0.1
        start = ema / d * p
    return ema


def statistics(p, d):
    pC = math.floor(p) + 1
    dC = threshold_damage(d, p, pC, d, p)
    p20 = threshold_damage(0, 0.0, 20.0, d, p)
    p40 = threshold_damage(0, 0.0, 40.0, d, p)
    p55 = threshold_damage(0, 0.0, 55.0, d, p)
    p65 = threshold_damage(0, 0.0, 65.0, d, p)
    p85 = threshold_damage(0, 0.0, 85.0, d, p)
    p95 = threshold_damage(0, 0.0, 95.0, d, p)
    p100 = threshold_damage(0, 0.0, 100.0, d, p)
    data = [0, p20, p40, p55, p65, p85, p95, p100]
    idx = next(x for x in MARK_LEVELS if x >= p)
    limit1 = dC
    limit2 = data[MARK_LEVELS.index(idx)]
    check = MARK_LEVELS.index(idx)
    delta = limit2 - limit1
    for value in range(len(data)):
        if data[value] == limit1 or data[value] == limit2:
            continue
        if value > check:
            data[value] = ceil_damage_tens(data[value] + delta)
    if pC == 101:
        pC = 100
        dC = data[7]
    return MarksStatistics(pC, dC, data[1], data[2], data[3], data[4], data[5], data[6], data[7])



def safe_number(value, default=0.0):
    return finite_number(value, default)


def hangar_goal(percent, moving_average, tier, selection=0, earned_marks=0):
    percent = max(0.0, min(100.0, safe_number(percent)))
    earned_marks = max(0, min(3, int(safe_number(earned_marks))))
    selection = max(0, min(3, int(safe_number(selection))))
    # Awarded marks are retained even if the current percentage later falls.
    progress_marks = max(earned_marks, sum(percent >= limit for limit in THRESHOLDS))
    mark = selection or min(3, progress_marks + 1)
    threshold = THRESHOLDS[mark - 1]
    eligible = safe_number(tier) >= MARKS_MIN_TIER
    achieved = eligible and (earned_marks >= mark or percent >= threshold)
    estimate = None
    average = safe_number(moving_average)
    if eligible and percent > 0 and average > 0:
        # Local proportional approximation, NOT a server threshold or a forecast
        # of the damage needed in the next single battle.
        estimate = int(math.ceil(average * threshold / percent / 10.0) * 10)
    return {'eligible': eligible, 'mark': mark, 'threshold': threshold,
            'achieved': achieved, 'gap': max(0.0, threshold - percent),
            'estimate': estimate, 'percent': percent}
