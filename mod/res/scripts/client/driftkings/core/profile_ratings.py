# -*- coding: utf-8 -*-
"""Account WN8 from random-battle dossier totals and weighted expectations."""
import math
from collections import namedtuple

from driftkings._constants import WN8_EXPECTED_FIELDS

# Same fields as the client's VehiclesDossiersCut: readers use .battlesCount or record[0].
VehicleCut = namedtuple('VehicleCut', ('battlesCount', 'wins', 'xp'))


def pure_random_stats(dossier, vehicle_id=None, vehicle_dossier=None):
    """Client a15x15 includes legacy clan/company counters; API random does not.

    Read cached dossiers only. Never invent per-vehicle weights when another
    player's vehicle dossiers have not been received by the client.
    """
    base = dossier.getRandomStats()
    excluded = [getattr(dossier, method)() for method in ('getClanStats', 'getCompanyStats')
                if hasattr(dossier, method)]
    if not any(stats.getBattlesCount() for stats in excluded):
        return base
    methods = ('getBattlesCount', 'getWinsCount', 'getDamageDealt', 'getFragsCount',
               'getSpottedEnemiesCount', 'getCapturePoints', 'getDroppedCapturePoints')
    values = {}
    for method in methods:
        value = getattr(base, method)() - sum(getattr(stats, method)() for stats in excluded)
        if value < 0:
            return None
        values[method] = value
    count = values['getBattlesCount']
    if not count:
        return None
    if vehicle_id is not None:
        vehicles = {vehicle_id: VehicleCut(count, values['getWinsCount'], 0)}
    else:
        if vehicle_dossier is None:
            from gui.shared.personality import ServicesLocator
            player_id = dossier.getPlayerDBID()
            vehicle_dossier = lambda ident: ServicesLocator.itemsCache.items.getVehicleDossier(ident, player_id)
        vehicles = {}
        for ident, record in base.getVehicles().items():
            if not record[0]:
                continue
            item = vehicle_dossier(ident)
            if item is None:
                return None
            stats = pure_random_stats(item, ident)
            if stats is not None and stats.getBattlesCount():
                vehicles[ident] = VehicleCut(stats.getBattlesCount(), stats.getWinsCount(), 0)
        if sum(record[0] for record in vehicles.values()) != count:
            return None

    class RandomStats(object):
        def __getattr__(self, name):
            if name in values:
                return lambda: values[name]
            return getattr(base, name)

        def getVehicles(self):
            return vehicles

        def getAvgDamage(self):
            return float(values['getDamageDealt']) / count

        def getAvgFrags(self):
            return float(values['getFragsCount']) / count

        def getAvgEnemiesSpotted(self):
            return float(values['getSpottedEnemiesCount']) / count

        def getWinsEfficiency(self):
            return float(values['getWinsCount']) / count

    return RandomStats()


def parse_thresholds(text, maximum):
    values = [float(item.strip()) for item in text.split(',')]
    if (len(values) != 5 or any(math.isnan(value) or math.isinf(value) or value <= 0 or value > maximum for value in values)
            or any(a >= b for a, b in zip(values, values[1:]))):
        raise ValueError('Use five increasing comma-separated limits between 0 and %s.' % maximum)
    return values


def vehicle_wn8(stats, vehicle_id, expected):
    """Use the same WN8 formula and validation for a single vehicle dossier."""
    if stats is None:
        return None
    class VehicleStats(object):
        def getVehicles(self):
            return {vehicle_id: (stats.getBattlesCount(),)}

        def __getattr__(self, name):
            return getattr(stats, name)

    return account_wn8(VehicleStats(), expected)


def account_wn8(stats, expected):
    if stats is None:
        return None
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
        values = [data.get(key) for key in WN8_EXPECTED_FIELDS]
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
