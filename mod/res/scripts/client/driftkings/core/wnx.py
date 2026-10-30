# -*- coding: utf-8 -*-
"""WNX formula and expected values supplied by the statistics cache."""
import math
import re

from driftkings.common.utils.numbers import nonnegative_number as number

_expected = {}


def valid_reference(document):
    data = document.get('data') if isinstance(document, dict) else None
    if not isinstance(data, dict) or not data:
        return False
    for ident, expected in data.items():
        if not str(ident).isdigit() or int(ident) <= 0 or not isinstance(expected, dict):
            return False
        values = [number(expected.get(key)) for key in ('damage', 'frags', 'spots', 'assist')]
        if None in values or min(values[:3]) <= 0:
            return False
    return True


def parse_reference_page(body, minimum=500):
    """Extract only numeric expected-value records from the public page, never execute JS."""
    text = body.decode('utf-8-sig')
    records = {}
    for block in re.findall(r'\{tank_id:\d+,[^{}]*?expected_assistance:[^{}]*?\}', text):
        values = {}
        for dest, key in (('id', 'tank_id'), ('damage', 'expected_damage'), ('frags', 'expected_frags'),
                          ('spots', 'expected_spots'), ('assist', 'expected_assistance')):
            match = re.search(r'\b' + key + r':(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)', block, re.I)
            if match is None:
                break
            values[dest] = float(match.group(1))
        if len(values) == 5:
            ident = str(int(values.pop('id')))
            if ident in records and records[ident] != values:
                raise ValueError('Conflicting WNX records')
            records[ident] = values
    document = {'source': 'https://tomato.gg/wnx', 'data': records}
    if len(records) < minimum or not valid_reference(document):
        raise ValueError('Incomplete or changed WNX reference page')
    return document


def set_reference(document):
    global _expected
    if not valid_reference(document):
        raise ValueError('Invalid WNX expected values')
    _expected = document['data']


def calculate(damage, frags, spots, assistance, expected, overall=False):
    """Single-vehicle calculator rounding matches Tomato.gg; totals use its overall rounding."""
    if not isinstance(expected, dict):
        return None
    actual = [number(value) for value in (damage, frags, spots, assistance)]
    exp = [number(expected.get(key)) for key in ('damage', 'frags', 'spots', 'assist')]
    if None in actual or None in exp or exp[0] <= 0 or exp[1] <= 0 or exp[2] <= 0:
        return None
    try:
        ratio = (actual[0] + .67 * actual[3]) / (exp[0] + .67 * exp[3])
        d = max(0.0, min(ratio - .22, (ratio - .22) / .78))
        f = max(0.0, min(d + .4, (actual[1] / exp[1] - .12) / .88))
        s = max(0.0, min(d + .2, (actual[2] / exp[2] - .38) / .62))
        raw = 750 * d + 200 * f + 50 * s
        scaled = raw * (raw / 1000.0) ** .45
        result = math.floor(scaled * 1.65 + .5) if overall else math.floor(scaled + .5) * 1.65
        return result if not math.isnan(result) and not math.isinf(result) else None
    except (OverflowError, ZeroDivisionError, ValueError):
        return None


def calculate_overall(records):
    """Aggregate matched per-tank totals and battle-weighted expectations before calculating."""
    actual, exp = [0.0] * 4, [0.0] * 4
    for record in records:
        battles = number(record.get('battles'))
        expected = record.get('expected')
        if not battles or not isinstance(expected, dict):
            continue
        values = [number(record.get(key)) for key in ('damage', 'frags', 'spots', 'assistance')]
        targets = [number(expected.get(key)) for key in ('damage', 'frags', 'spots', 'assist')]
        if None in values or None in targets or min(targets[:3]) <= 0:
            continue
        for index in range(4):
            actual[index] += values[index]
            exp[index] += battles * targets[index]
    return calculate(*(actual + [dict(zip(('damage', 'frags', 'spots', 'assist'), exp)), True]))


def get_expected(vehicle_id):
    return _expected.get(str(vehicle_id))


def account_from_tanks(tanks, battles):
    """Use random-only counters and require complete weights and assistance coverage."""
    records, count = [], 0
    for tank in tanks:
        stats = tank.get('statistics', {})
        played = number(stats.get('battles'))
        if not played:
            continue
        expected = get_expected(tank.get('tank_id'))
        required = [number(stats.get(key)) for key in ('damage_dealt', 'frags', 'spotted',
                    'radio_assisted_damage', 'track_assisted_damage', 'stun_assisted_damage')]
        if expected is None or None in required:
            return None
        records.append({'battles': played, 'expected': expected, 'damage': required[0],
                        'frags': required[1], 'spots': required[2], 'assistance': sum(required[3:])})
        count += played
    return calculate_overall(records) if count and count == number(battles) else None
