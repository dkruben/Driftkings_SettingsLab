# -*- coding: utf-8 -*-
from driftkings.stats.vehinfo import calculateXTDB, calculateXTE, calculateRatingScale, getVehicleInfoData


class _Stat(object):
    def __init__(self):
        self.resp = None

    @staticmethod
    def _fix_common(value):
        for original, renamed in (('_id', 'player_id'), ('nm', 'name_db'), ('cid', 'clan_id'),
                                  ('b', 'battles'), ('w', 'wins'), ('e', 'eff'), ('lvl', 'avglvl')):
            if original in value:
                value[renamed] = value.pop(original)
        for key in ('ver', 'st', 'dt', 'cr', 'up', 'rnd', 'lang'):
            value.pop(key, None)
        if not isinstance(value.get('v'), dict):
            value['v'] = {}
        for key in ('eff', 'wn8', 'wgr', 'wtr'):
            rating = value.get(key)
            if rating is None or rating <= 0:
                value[key] = None

    def _fix_common2(self, stat, orig_name):
        if orig_name is not None:
            stat['name'] = orig_name
        if 'battles' in stat and 'wins' in stat and stat['battles'] > 0:
            self._calculateGWR(stat)
            self._calculateRatingScale(stat)
            if 'v' in stat:
                vData = stat['v']
                if 'id' in vData:
                    self._calculateVehicleValues(stat, vData)
                    self._calculateXTDB(vData)
                    self._calculateXTE(vData)
                    self._calculateVXWTR(vData)
            if 'vehicles' in stat:
                for vehicleID, vData in stat['vehicles'].items():
                    if not isinstance(vData, dict):
                        continue
                    try:
                        vData['id'] = int(vehicleID)
                    except (TypeError, ValueError, OverflowError):
                        continue
                    self._calculateVehicleValues(stat, vData)
                    self._calculateXTDB(vData)
                    self._calculateXTE(vData)
                    self._calculateVXWTR(vData)

    # Global Win Rate (GWR)
    @staticmethod
    def _calculateGWR(stat):
        stat['winrate'] = float(stat['wins']) / float(stat['battles']) * 100.0

    # Rating scale
    @staticmethod
    def _calculateRatingScale(stat):
        if stat.get('wtr') is not None and stat['wtr'] > 0:
            stat['xwtr'] = calculateRatingScale('wtr', stat['wtr'])
        if stat.get('wn8') is not None and stat['wn8'] > 0:
            stat['xwn8'] = calculateRatingScale('wn8', stat['wn8'])
        if stat.get('eff') is not None and stat['eff'] > 0:
            stat['xeff'] = calculateRatingScale('eff', stat['eff'])
        if stat.get('wgr') is not None and stat['wgr'] > 0:
            stat['xwgr'] = calculateRatingScale('wgr', stat['wgr'])
        if stat.get('winrate') is not None and stat['winrate'] > 0:
            stat['xwr'] = calculateRatingScale('win', stat['winrate'])

    # calculate Vehicle values
    @staticmethod
    def _calculateVehicleValues(stat, value):
        vehicleID = value['id']
        vData = getVehicleInfoData(vehicleID)
        if vData is None:
            return

        # tank rating
        if 'b' not in value or 'w' not in value or value['b'] <= 0:
            value['winrate'] = stat['winrate']
        else:
            Tr = float(value['w']) / float(value['b']) * 100.0
            if value['b'] > 100:
                value['winrate'] = Tr
            else:
                Or = float(stat['winrate'])
                Tb = float(value['b']) / 100.0
                Tl = float(min(vData['level'], 4)) / 4.0
                value['winrate'] = Or - (Or - Tr) * Tb * Tl

        if 'b' not in value or value['b'] <= 0:
            return

        vb = float(value['b'])
        if 'dmg' in value and value['dmg'] > 0:
            value['db'] = float(value['dmg']) / vb
            hp_top = vData.get('hpTop', 0)
            if hp_top:
                value['dv'] = value['db'] / hp_top
        if 'frg' in value and value['frg'] > 0:
            value['fb'] = float(value['frg']) / vb
        if 'spo' in value and value['spo'] > 0:
            value['sb'] = float(value['spo']) / vb

    # calculate xTDB
    @staticmethod
    def _calculateXTDB(value):
        if 'db' not in value or value['db'] < 0:
            return
        value['xtdb'] = calculateXTDB(value['id'], float(value['db']))

    # calculate xTE
    @staticmethod
    def _calculateXTE(value):
        if 'db' not in value or value['db'] < 0:
            return
        if 'fb' not in value or value['fb'] < 0:
            return
        value['xte'] = calculateXTE(value['id'], float(value['db']), float(value['fb']))

    # calculate per-vehicle xWTR
    @staticmethod
    def _calculateVXWTR(value):
        if value.get('wtr') is not None and value['wtr'] > 0:
            value['xwtr'] = calculateRatingScale('wtr', value['wtr'])


rating_stats = _Stat()
