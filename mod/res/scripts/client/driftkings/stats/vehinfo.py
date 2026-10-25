# -*- coding: utf-8 -*-
"""
Vehicle information and statistics module for Driftkings.
Handles loading, processing and calculation of various tank statistics.
"""
from contextlib import closing
import json
import math
import os
import threading
import time
import urllib2

from driftkings.logger import get_logger

try:
    from Queue import Empty, Queue
except ImportError:
    from queue import Queue, Empty

from items import vehicles
import nations
import ResMgr

from driftkings.common.utils.filesystem import atomicWrite, recoverFile
from driftkings.core.cache import cache_directory
from driftkings.core.callbacks import callback
from driftkings.core.wnx import parse_reference_page
from driftkings.core.wnx import set_reference as set_wnx_reference
from driftkings.core.wnx import valid_reference as valid_wnx

LOG = get_logger('Driftkings.Stats')
try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)


def finite_number(value):
    try:
        return not isinstance(value, bool) and isinstance(value, integer_types + (float,)) and not (math.isnan(value) or math.isinf(value))
    except OverflowError:
        return False


def valid_scale(values):
    return (isinstance(values, (list, tuple)) and bool(values) and
            all(finite_number(value) for value in values) and
            all(left <= right for left, right in zip(values, values[1:])))


def _scale_documents(document, field=None):
    entries = [value for key, value in document.items() if key.startswith('x')] if field is None else [
        value for key, value in document.items() if key.isdigit()]
    if field is None:
        return bool(entries) and all(valid_scale(value) for value in entries)
    return bool(entries) and all(isinstance(value, dict) and valid_scale(value.get(field)) for value in entries)


def valid_xvm_scales(document):
    return isinstance(document, dict) and _scale_documents(document)


def valid_wn8(document):
    if not isinstance(document, dict) or not isinstance(document.get('data'), list) or not document['data']:
        return False
    seen = set()
    for record in document['data']:
        if not isinstance(record, dict):
            return False
        ident = record.get('IDNum')
        if isinstance(ident, bool) or not isinstance(ident, integer_types) or ident <= 0 or ident in seen:
            return False
        seen.add(ident)
        if not all(finite_number(record.get(key)) and record[key] > 0 for key in (
                'expDamage', 'expSpot', 'expWinRate', 'expDef', 'expFrag')):
            return False
    return True


def valid_scaled_vehicles(document):
    return isinstance(document, dict) and _scale_documents(document, 'x')


_FLAVOR = 'wg'
HOST = 'https://static.modxvm.com/'
URL_WN8 = HOST + 'wn8-data-exp/json/%s/wn8exp.json' % _FLAVOR
URL_XTE = HOST + 'xte.json'
URL_XTDB = HOST + 'xtdb.json'
URL_XVM_SCALE = HOST + 'xvmscales-%s.json' % _FLAVOR
URL_WNX = 'https://tomato.gg/wnx'
MAX_DOWNLOAD = 16 * 1024 * 1024
READ_CHUNK = 64 * 1024
SOCKET_TIMEOUT = 10
DOWNLOAD_DEADLINE = 30.0
UPDATE_INTERVAL = 24 * 60 * 60
RETRY_INTERVAL = 30 * 60
HANGAR_CHECK_INTERVAL = 30.0
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

XVM_SCALE_TO_SUP_CACHE = [str(i) for i in range(1, 101)]


class ScaleValues(object):

    def __init__(self):
        self.NAME = 'stats'
        self.modsGroup = 'driftkings'
        self.vehicleInfoData = None
        self.wn8_data = {}
        self.wn8_revision = 0
        self.xte_data = {}
        self.xvmScale_data = {}
        self.xtdb_data = {}
        self.config_path = cache_directory('stats')
        self.settings = {'onlineUpdateData': True, 'showExpectedTankValuesMessage': True}
        self._updates = Queue()
        self._downloading = False
        self._refreshState = {}
        self._invalidCaches = set()
        self._downloadSources = None
        self.init()
        self._initialize_callbacks()

    def _initialize_callbacks(self):
        # Local cache first (fast, on the client thread); network refresh runs in a worker.
        callback(0, self._loadAll)

    def init(self):
        res = [dict(UNKNOWN_VEHICLE_DATA)]
        try:
            for nation in nations.NAMES:
                nationID = nations.INDICES[nation]
                vehicle_list = vehicles.g_list.getList(nationID)

                for descr in vehicle_list.values():
                    if descr.name.endswith('training'):
                        continue
                    try:
                        data = self.createVehicleData(descr, nation)
                        res.append(data)
                    except Exception:
                        LOG.exception('Error creating vehicle data for %s', descr.name)
                ResMgr.purge(os.path.join(VEHICLE_TYPE_XML_PATH, nation, 'components', 'guns.xml'), True)
        except Exception:
            LOG.exception('Failed to initialize vehicle data')
        finally:
            self.vehicleInfoData = dict((item['vehCD'], item) for item in res)

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

    @staticmethod
    def XvmScaleToSup(x=None):
        if x is None:
            return None
        if not finite_number(x):
            return None
        return XVM_SCALE_TO_SUP_CACHE[min(100, max(1, int(x))) - 1] if x > 0 else 0.0

    @staticmethod
    def download(url, deadline=DOWNLOAD_DEADLINE):
        """Bounded body read: size cap and total deadline, independent of per-read socket timeouts."""
        limit = time.time() + deadline
        chunks, total = [], 0
        with closing(urllib2.urlopen(url, timeout=SOCKET_TIMEOUT)) as response:
            while True:
                if time.time() > limit:
                    raise IOError('download deadline exceeded')
                chunk = response.read(READ_CHUNK)
                if time.time() > limit:
                    raise IOError('download deadline exceeded')
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD:
                    raise IOError('download exceeds %d bytes' % MAX_DOWNLOAD)
                chunks.append(chunk)
        return b''.join(chunks)

    @staticmethod
    def loadJsonData(url, local_path, validate=None):
        """Keep the last valid cache if a download or publication fails. Safe to call off the client thread."""
        try:
            data = ScaleValues.download(url)
            if url == URL_WNX:
                document = parse_reference_page(data)
                data = json.dumps(document).encode('utf-8')
            else:
                document = json.loads(data.decode('utf-8-sig'))
            if not isinstance(document, dict) or not document:
                raise ValueError('Expected a non-empty JSON object')
            if validate is not None and not validate(document):
                raise ValueError('Unexpected document structure')
            atomicWrite(local_path, data)
            return True
        except (IOError, OSError, ValueError) as error:
            LOG.warning('Could not update statistics cache %s from %s: %s', local_path, url, error)
            return False
        except Exception:
            # httplib.HTTPException (IncompleteRead, BadStatusLine...) is not an IOError in Python 2.7.
            LOG.exception('Unexpected failure updating statistics cache %s from %s', local_path, url)
            return False

    def _readCache(self, filename):
        path = os.path.join(self.config_path, filename)
        try:
            recoverFile(path)
            with open(path, 'rb') as stream:
                data = json.loads(stream.read().decode('utf-8-sig'))
            if not isinstance(data, dict):
                raise ValueError('Expected a JSON object')
            validate = next((validate for name, url, validate in self.SOURCES if name == filename), None)
            if validate is not None and not validate(data):
                raise ValueError('Unexpected cached document structure')
            return data
        except (IOError, OSError, ValueError):
            if any(name == filename for name, url, validate in self.SOURCES):
                self._invalidCaches.add(filename)
            LOG.exception('Could not load statistics cache %s', path)
            return {}

    def _downloadAll(self):
        """Worker thread body: refresh every cache file, return the names that changed."""
        updated = []
        for filename, url, validate in self._downloadSources or self.SOURCES:
            success = self.loadJsonData(url, os.path.join(self.config_path, filename), validate)
            self._updates.put((filename, success, time.time()))
            if success:
                updated.append(filename)
        return updated

    def _runDownloads(self):
        try:
            self._downloadAll()
        except Exception:
            LOG.exception('Statistics download worker failed')
        finally:
            self._downloading = False

    def _startDownloads(self):
        if (self._downloading or not self._updates.empty() or not self._inHangar()
                or not self.settings.get('onlineUpdateData', True)):
            return
        now = time.time()
        due = []
        for source in self.SOURCES:
            name = source[0]
            state = self._refreshState.get(name, {})
            success = state.get('success', 0)
            retry = state.get('retry', 0)
            if retry > now and retry <= now + RETRY_INTERVAL:
                continue
            if (name in self._invalidCaches or not os.path.isfile(os.path.join(self.config_path, name))
                    or success <= 0 or success > now or now - success >= UPDATE_INTERVAL):
                due.append(source)
        if not due:
            return
        # Recheck the client state before every table, rather than downloading
        # all tables after a single hangar check. Workers never access game objects.
        self._downloadSources = due[:1]
        self._downloading = True
        worker = threading.Thread(target=self._runDownloads, name='Driftkings.StatsDownload')
        worker.daemon = True
        try:
            worker.start()
        except Exception:
            self._downloading = False
            self._refreshState.setdefault(due[0][0], {})['retry'] = time.time() + RETRY_INTERVAL
            self._saveRefreshState()
            LOG.exception('Could not start statistics download worker')
            return
        callback(0.5, self._pollDownloads)

    def _pollDownloads(self):
        """Client thread: apply files published by the worker, never touching the network."""
        if not self._inHangar():
            callback(HANGAR_CHECK_INTERVAL, self._pollDownloads)
            return
        while True:
            try:
                filename, success, finished = self._updates.get_nowait()
            except Empty:
                break
            state = self._refreshState.setdefault(filename, {})
            if success:
                state.update(success=finished, retry=0)
                self.APPLY[filename](self)
                self._invalidCaches.discard(filename)
            else:
                state['retry'] = finished + RETRY_INTERVAL
            self._saveRefreshState()
        if self._downloading or not self._updates.empty():
            callback(0.5, self._pollDownloads)

    def _loadAll(self):
        self._loadRefreshState()
        for filename, url, validate in self.SOURCES:
            self.APPLY[filename](self)
        self._checkUpdates()

    @staticmethod
    def _inHangar():
        try:
            import BigWorld
            from gui.shared.personality import ServicesLocator
            player = BigWorld.player()
            return (player is not None and bool(getattr(player, 'databaseID', None))
                    and getattr(player, 'arena', None) is None and ServicesLocator.itemsCache.isSynced())
        except Exception:
            return False

    def _checkUpdates(self):
        self._startDownloads()
        callback(HANGAR_CHECK_INTERVAL, self._checkUpdates)

    def _loadRefreshState(self):
        data = self._readCache('refresh-state.json')
        self._refreshState = {}
        for filename, url, validate in self.SOURCES:
            entry = data.get(filename)
            if isinstance(entry, dict) and all(
                    finite_number(entry.get(key, 0)) and entry.get(key, 0) >= 0 for key in ('success', 'retry')):
                self._refreshState[filename] = entry

    def _saveRefreshState(self):
        try:
            atomicWrite(os.path.join(self.config_path, 'refresh-state.json'),
                        json.dumps(self._refreshState).encode('utf-8'))
        except (IOError, OSError):
            LOG.exception('Could not save statistics refresh times')

    def _loadXvmScaleData(self):
        data = self._readCache('xvmScales.json')
        if data:
            self.xvmScale_data = data

    def _loadWn8Data(self):
        data = self._readCache('wn8exp.json')
        if not data:
            return
        self.wn8_data = data
        # A replacement table must not retain expectations for removed vehicles.
        for vehicle in self.getVehicleInfoDataArray():
            for key in ('wn8expDamage', 'wn8expSpot', 'wn8expWinRate', 'wn8expDef', 'wn8expFrag'):
                vehicle.pop(key, None)
        records = self.wn8_data.get('data', [])
        if not isinstance(records, list):
            LOG.warning('Ignored invalid WN8 records')
            return
        for record in records:
            try:
                vinfo = self.getVehicleInfoData(int(record['IDNum']))
                values = dict((name, float(record[key])) for name, key in (
                    ('wn8expDamage', 'expDamage'), ('wn8expSpot', 'expSpot'),
                    ('wn8expWinRate', 'expWinRate'), ('wn8expDef', 'expDef'), ('wn8expFrag', 'expFrag')))
                if not all(finite_number(value) for value in values.values()):
                    raise ValueError('Non-finite WN8 expected value')
                if vinfo is not None:
                    vinfo.update(values)
            except (KeyError, ValueError, TypeError, OverflowError):
                LOG.exception('Ignored invalid WN8 vehicle record')
        self.wn8_revision += 1

    def _loadXteData(self):
        data = self._readCache('xte.json')
        if not data:
            return
        self.xte_data = data
        for vehicle in self.getVehicleInfoDataArray():
            for key in ('avgdmg', 'topdmg', 'avgfrg', 'topfrg'):
                vehicle.pop(key, None)
        for key, values in self.xte_data.items():
            try:
                vinfo = self.getVehicleInfoData(int(key))
                expected = dict((name, float(values.get(field, 0))) for name, field in (
                    ('avgdmg', 'ad'), ('topdmg', 'td'), ('avgfrg', 'af'), ('topfrg', 'tf')))
                if not all(finite_number(value) for value in expected.values()):
                    raise ValueError('Non-finite XTE expected value')
                if vinfo is not None:
                    vinfo.update(expected)
            except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
                LOG.exception('Ignored invalid XTE vehicle record %s', key)

    def _loadXtdbData(self):
        data = self._readCache('xtdb.json')
        if data:
            self.xtdb_data = data

    def _loadWnxData(self):
        document = self._readCache('wnxexp.json')
        if document:
            set_wnx_reference(document)

    SOURCES = (('xvmScales.json', URL_XVM_SCALE, valid_xvm_scales),
               ('wn8exp.json', URL_WN8, valid_wn8),
               ('xte.json', URL_XTE, valid_scaled_vehicles),
               ('xtdb.json', URL_XTDB, valid_scaled_vehicles),
               ('wnxexp.json', URL_WNX, valid_wnx))
    APPLY = {'xvmScales.json': _loadXvmScaleData, 'wn8exp.json': _loadWn8Data,
             'xte.json': _loadXteData, 'xtdb.json': _loadXtdbData, 'wnxexp.json': _loadWnxData}

    def getVehicleInfoData(self, vehCD):
        if not isinstance(vehCD, integer_types):
            return None
        return self.vehicleInfoData.get(vehCD) if self.vehicleInfoData is not None else None

    def getVehicleInfoDataArray(self):
        return list(self.vehicleInfoData.values()) if self.vehicleInfoData is not None else []

    def resetReserve(self):
        if self.vehicleInfoData is not None:
            for vinfo in self.vehicleInfoData.values():
                vinfo['isReserved'] = False

    def updateReserve(self, vehCD, isReserved):
        if self.vehicleInfoData is not None and vehCD in self.vehicleInfoData:
            self.vehicleInfoData[vehCD]['isReserved'] = isReserved

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
        data = self.getXvmScaleData(rating)
        if not valid_scale(data) or not finite_number(value):
            return -1
        for i, v in enumerate(data):
            if v > value:
                return i
        return 100

    def calculateXTE(self, vehCD, dmg_per_battle, frg_per_battle):
        data = self.getXteData(vehCD)
        if (not isinstance(data, dict) or not valid_scale(data.get('x')) or
                not all(finite_number(data.get(key)) for key in ('td', 'ad', 'tf', 'af')) or
                not finite_number(dmg_per_battle) or not finite_number(frg_per_battle)):
            return -1
        if data['td'] <= data['ad'] or data['tf'] <= data['af'] or data['ad'] <= 0 or data['af'] <= 0:
            return -1
        CD = 3.0  # Damage coefficient
        CF = 1.0  # Frag coefficient
        avgD = float(data['ad'])  # Average damage
        topD = float(data['td'])  # Top damage
        avgF = float(data['af'])  # Average frags
        topF = float(data['tf'])  # Top frags
        dD = dmg_per_battle - avgD
        dF = frg_per_battle - avgF
        minD = avgD * 0.4
        minF = avgF * 0.4
        if dmg_per_battle >= avgD:
            d = 1 + dD / (topD - avgD)
        else:
            d = 1 + dD / (avgD - minD)

        if frg_per_battle >= avgF:
            f = 1 + dF / (topF - avgF)
        else:
            f = 1 + dF / (avgF - minF)
        d = max(0, d)
        f = max(0, f)
        t = (d * CD + f * CF) / (CD + CF) * 1000.0
        for i, v in enumerate(data['x']):
            if v > t:
                return i
        return 100

    def calculateXTDB(self, vehCD, dmg_per_battle):
        data = self.getXtdbData(vehCD)
        if not isinstance(data, dict) or not valid_scale(data.get('x')) or not finite_number(dmg_per_battle):
            return -1
        for i, v in enumerate(data['x']):
            if v > dmg_per_battle:
                return i
        return 100

    def getXtdbDataArray(self, vehCD):
        data = self.getXtdbData(vehCD)
        return data['x'] if isinstance(data, dict) and valid_scale(data.get('x')) else []


try:
    scaleValuesInstance = ScaleValues()
    getVehicleInfoData = scaleValuesInstance.getVehicleInfoData
    calculateXvmScale = scaleValuesInstance.calculateXvmScale
    calculateXTDB = scaleValuesInstance.calculateXTDB
    calculateXTE = scaleValuesInstance.calculateXTE
except ImportError:
    LOG.exception('Statistics scale could not be imported')
