# -*- coding: utf-8 -*-
"""Account WN8 from random-battle dossier totals and weighted expectations."""
import math


def parse_thresholds(text, maximum):
    values = [float(item.strip()) for item in text.split(',')]
    if (len(values) != 5 or any(math.isnan(value) or math.isinf(value) or value <= 0 or value > maximum for value in values)
            or any(a >= b for a, b in zip(values, values[1:]))):
        raise ValueError('Use five increasing comma-separated limits between 0 and %s.' % maximum)
    return values


def vehicle_wn8(stats, vehicle_id, expected):
    """Use the same WN8 formula and validation for a single vehicle dossier."""
    class VehicleStats(object):
        def getVehicles(self):
            return {vehicle_id: (stats.getBattlesCount(),)}

        def __getattr__(self, name):
            return getattr(stats, name)

    return account_wn8(VehicleStats(), expected)


def account_wn8(stats, expected):
    battles = stats.getBattlesCount()
    if not battles:
        return None
    sums = [0.0] * 5
    covered = 0
    for vehicle_id, record in stats.getVehicles().items():
        count = record[0]
        if not count:
            continue
        data = expected(vehicle_id) or {}
        values = [data.get(key) for key in ('wn8expDamage', 'wn8expFrag', 'wn8expSpot', 'wn8expDef', 'wn8expWinRate')]
        if any(value is None or value <= 0 or math.isnan(float(value)) or math.isinf(float(value)) for value in values):
            return None
        for index, value in enumerate(values):
            sums[index] += count * value
        covered += count
    # Do not mix totals from vehicles absent from the expected-value table.
    if covered != battles:
        return None
    wins = stats.getWinsEfficiency()
    defence = stats.getDroppedCapturePoints()
    if wins is None or defence is None:
        return None
    actual = (stats.getAvgDamage(), stats.getAvgFrags(), stats.getAvgEnemiesSpotted(),
              float(defence) / battles, wins * 100)
    if any(value is None for value in actual):
        return None
    rd, rf, rs, rb, rw = [value * battles / total for value, total in zip(actual, sums)]
    damage = max(0, (rd - .22) / .78)
    frags = max(0, min(damage + .2, (rf - .12) / .88))
    spots = max(0, min(damage + .1, (rs - .38) / .62))
    defence = max(0, min(damage + .1, (rb - .10) / .90))
    wins = max(0, (rw - .71) / .29)
    return int(round(980 * damage + 210 * damage * frags + 155 * frags * spots + 75 * defence * frags + 145 * min(1.8, wins)))
