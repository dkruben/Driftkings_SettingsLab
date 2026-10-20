# -*- coding: utf-8 -*-
"""
Vehicle information and statistics module for Driftkings.
Handles loading, processing and calculation of various tank statistics.
"""
import json
import os
import threading

import ResMgr
import nations
from items import vehicles

from Driftkings.common import callback, logError
from Driftkings.core import xvm_scales
from Driftkings.core.cache import cache_directory
from Driftkings.core.safe_download import download_json
from Driftkings.stats import __CORE_NAME__

_FLAVOR = 'wg'
HOST = 'https://static.modxvm.com/'
URL_WN8 = HOST + 'wn8-data-exp/json/%s/wn8exp.json' % _FLAVOR
URL_XTE = HOST + 'xte.json'
URL_XTDB = HOST + 'xtdb.json'
URL_XVM_SCALE = HOST + 'xvmscales-%s.json' % _FLAVOR
VEHICLE_TYPE_XML_PATH = 'scripts/item_defs/vehicles/'
VEHICLE_CLASS_TAGS = frozenset(('lightTank', 'mediumTank', 'heavyTank', 'SPG', 'AT-SPG'))


UNKNOWN_VEHICLE_DATA = {
    'vehCD': 0,
    'key': 'unknown',
    'nation': '',
    'level': 0,
    'vClass': '',
    'localizedName': 'unknown',
    'localizedShortName': 'unknown',
    'localizedFullName': 'unknown',
    'premium': False,
    'special': False,
    'tierLo': 0,
    'tierHi': 0,
    'shortName': 'unknown',
    'isReserved': False
}


class ScaleValues(object):

    def __init__(self):
        self.NAME = 'stats'
        self.modsGroup = 'Driftkings'
        self.vehicleInfoData = None
        self.wn8_data = {}
        self.xte_data = {}
        self.xvmScale_data = {}
        self.xtdb_data = {}
        self.config_path = cache_directory('stats')
        self.settings = {'onlineUpdateData': True}
        self._download = None
        self.init()
        # Cached files load immediately and offline; refreshing them never blocks the client thread.
        self._loadAll()
        if self.settings.get('onlineUpdateData', True):
            self._startDownload()

    def _loadAll(self):
        self._loadXvmScaleData()
        self._loadWn8Data()
        self._loadXteData()
        self._loadXtdbData()

    def _startDownload(self):
        sources = ((URL_XVM_SCALE, 'xvmScales.json'), (URL_WN8, 'wn8exp.json'),
                   (URL_XTE, 'xte.json'), (URL_XTDB, 'xtdb.json'))
        refreshed = []

        def worker():
            for url, name in sources:
                if download_json(url, os.path.join(self.config_path, name)):
                    refreshed.append(name)

        self._download = (threading.Thread(target=worker, name='Driftkings.Stats.Download'), refreshed)
        self._download[0].daemon = True
        self._download[0].start()
        callback(1.0, self._pollDownload)

    def _pollDownload(self):
        thread, refreshed = self._download
        if thread.is_alive():
            callback(1.0, self._pollDownload)
            return
        self._download = None
        if refreshed:
            self._loadAll()

    def init(self):
        res = [UNKNOWN_VEHICLE_DATA]
        try:
            for nation in nations.NAMES:
                nationID = nations.INDICES[nation]
                vehicle_list = vehicles.g_list.getList(nationID)

                for ids, descr in vehicle_list.items():
                    if descr.name.endswith('training'):
                        continue
                    try:
                        data = self.createVehicleData(descr, nation)
                        res.append(data)
                    except Exception as e:
                        logError(__CORE_NAME__, 'Error creating vehicle data for {}: {}', descr.name, e)
                ResMgr.purge(os.path.join(VEHICLE_TYPE_XML_PATH, nation, 'components', 'guns.xml'), True)
            self.vehicleInfoData = {x['vehCD']: x for x in res}
        except Exception as e:
            logError(__CORE_NAME__, 'Failed to initialize vehicle data: {}', e)
            self.vehicleInfoData = {UNKNOWN_VEHICLE_DATA['vehCD']: UNKNOWN_VEHICLE_DATA}

    @staticmethod
    def createVehicleData(descr, nation):
        vClass = next(iter(VEHICLE_CLASS_TAGS & descr.tags), '')
        return {
            'vehCD': descr.compactDescr,
            'key': descr.name,
            'nation': nation,
            'level': descr.level,
            'vClass': vClass,
            'localizedName': descr.shortUserString,
            'localizedShortName': descr.shortUserString,
            'localizedFullName': descr.userString,
            'premium': 'premium' in descr.tags and 'special' not in descr.tags,
            'special': 'special' in descr.tags,
            'isReserved': False
        }

    def _loadXvmScaleData(self):
        xvmScales_path = os.path.join(self.config_path, 'xvmScales.json')
        try:
            with open(xvmScales_path, 'r') as xvm_scale:
                self.xvmScale_data = json.load(xvm_scale)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading XVM scale data: {}', e)
            self.xvmScale_data = {}

    def _loadWn8Data(self):
        wn8_cache = os.path.join(self.config_path, 'wn8exp.json')
        try:
            with open(wn8_cache) as origExpectedValuesJson:
                origExpectedValues = json.load(origExpectedValuesJson)
                self.wn8_data = origExpectedValues
                for x in origExpectedValues.get('data', []):
                    try:
                        vehCD = int(x['IDNum'])
                        vinfo = self.getVehicleInfoData(vehCD)
                        if vinfo is not None:
                            vinfo.update({'wn8expDamage': float(x['expDamage']), 'wn8expSpot': float(x['expSpot']), 'wn8expWinRate': float(x['expWinRate']), 'wn8expDef': float(x['expDef']), 'wn8expFrag': float(x['expFrag'])})
                    except (KeyError, ValueError) as e:
                        logError(__CORE_NAME__, 'Error processing WN8 data for vehicle: {}', e)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading WN8 data: {}', e)

    def _loadXteData(self):
        xte_path = os.path.join(self.config_path, 'xte.json')
        try:
            with open(xte_path) as xte_scale:
                self.xte_data = json.load(xte_scale)
                for key, values in self.xte_data.items():
                    try:
                        vinfo = self.getVehicleInfoData(int(key))
                        if vinfo is not None:
                            vinfo.update({'avgdmg': float(values.get('ad', 0)), 'topdmg': float(values.get('td', 0)), 'avgfrg': float(values.get('af', 0)), 'topfrg': float(values.get('tf', 0))})
                    except (ValueError, KeyError) as e:
                        logError(__CORE_NAME__, 'Error processing XTE data for vehicle {}: {}', key, e)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading XTE data: {}', e)
            self.xte_data = {}

    def _loadXtdbData(self):
        xtdb_path = os.path.join(self.config_path, 'xtdb.json')
        try:
            with open(xtdb_path) as xtdb_scale:
                self.xtdb_data = json.load(xtdb_scale)
        except (IOError, ValueError) as e:
            logError(__CORE_NAME__, 'Error loading XTDB data: {}', e)
            self.xtdb_data = {}

    def getVehicleInfoData(self, vehCD):
        if not isinstance(vehCD, (int, long)):
            return None
        return self.vehicleInfoData.get(vehCD) if self.vehicleInfoData is not None else None

    def getVehicleInfoDataArray(self):
        return list(self.vehicleInfoData.values()) if self.vehicleInfoData is not None else []

    def getXvmScaleData(self, rating):
        if self.xvmScale_data is None:
            return None
        return self.xvmScale_data.get('x{}'.format(rating))

    def getXteData(self, vehCD):
        if self.xte_data is None:
            return None
        return self.xte_data.get(str(vehCD))

    def getXtdbData(self, vehCD):
        if self.xtdb_data is None:
            return None
        return self.xtdb_data.get(str(vehCD))

    def calculateXvmScale(self, rating, value):
        return xvm_scales.rank(self.getXvmScaleData(rating), value)

    def calculateXTE(self, vehCD, dmg_per_battle, frg_per_battle):
        return xvm_scales.xte(self.getXteData(vehCD), dmg_per_battle, frg_per_battle)

    def calculateXTDB(self, vehCD, dmg_per_battle):
        return xvm_scales.xtdb(self.getXtdbData(vehCD), dmg_per_battle)


try:
    scaleValuesInstance = ScaleValues()
except Exception as error:
    # A failure here must not take every component that imports Driftkings.stats down with it.
    logError(__CORE_NAME__, 'Scale data unavailable: {}', error)
    scaleValuesInstance = ScaleValues.__new__(ScaleValues)
    scaleValuesInstance.vehicleInfoData = {UNKNOWN_VEHICLE_DATA['vehCD']: UNKNOWN_VEHICLE_DATA}
    scaleValuesInstance.xvmScale_data = scaleValuesInstance.xte_data = scaleValuesInstance.xtdb_data = {}
getVehicleInfoData = scaleValuesInstance.getVehicleInfoData
calculateXvmScale = scaleValuesInstance.calculateXvmScale
calculateXTDB = scaleValuesInstance.calculateXTDB
calculateXTE = scaleValuesInstance.calculateXTE
