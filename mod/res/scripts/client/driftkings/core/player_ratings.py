# -*- coding: utf-8 -*-
from contextlib import closing
import json
import math
from Queue import Empty, Queue
import re
import string
import threading
import time
import urllib
import urllib2
from xml.sax.saxutils import escape

from gui.battle_control.arena_info.interfaces import IArenaVehiclesController
from gui.battle_control.arena_info.settings import ARENA_LISTENER_SCOPE
from gui.battle_control.battle_constants import BATTLE_CTRL_ID
from gui.shared.gui_items.Vehicle import getVehicleClassTag
from gui.shared.personality import ServicesLocator
from helpers import dependency
from messenger import g_settings
from skeletons.gui.battle_session import IBattleSessionProvider

from driftkings._constants import GLOBAL, TEAM_PANELS
from driftkings.common.utils.colorratting import getStatisticColor
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.stats.vehinfo import calculateRatingScale, getVehicleInfoData, scaleValuesInstance

LOG = get_logger('driftkings.core.player_ratings')

MISSING = u'\u2014'
# Accounts with no usable answer (closed profiles, API errors) are retried at this pace.
RETRY_SECONDS = 60
# Requests that failed (timeout, API error) are retried soon: the loading screen is short.
FAILED_RETRY_SECONDS = 5
# Upper bound on cached accounts; each one holds the full vehicle list.
CACHE_LIMIT = 300
MAX_STATS_RESPONSE = 16 * 1024 * 1024
STATS_DEADLINE = 30.0
NUMERIC = ('wn8', 'wnx', 'winrate', 'battles', 'kb', 'wgr', 'eff', 'xwn8', 'xeff',
           't_battles', 't_winrate', 'spg_battles', 'spg_percent', 'mark_of_mastery', 'tdv')


def tank_damage_ratio(stats, maxHP):
    battles, damage = stats.get('battles', 0), stats.get('damage_dealt')
    if not battles or battles < 0 or not maxHP or maxHP < 0 or damage is None:
        return MISSING
    return damage / float(battles * maxHP)


class RatingFormatter(string.Formatter):
    def get_field(self, name, args, kwargs):
        # Only data macros; do not traverse Python attributes or indices.
        return kwargs.get(name, MISSING), name

    def format_field(self, value, spec):
        if isinstance(value, dict):
            return value.get(spec, 'AAAAAA')
        if value == MISSING:
            return MISSING
        return super(RatingFormatter, self).format_field(value, spec)


def format_rating(template, info, vehicle, available, scale=0):
    values = dict(info or {})
    name = vehicle.get('name', values.get('name', ''))
    clan = vehicle.get('clanAbbrev', '')
    values.update(name=name, short_nick=name, clan='[%s]' % clan if clan else '')
    values['nick'] = name + values['clan']
    values['team'] = vehicle.get('team', values.get('team', 0))
    values['isAlive'] = vehicle.get('isAlive', values.get('isAlive', False))
    values['alive'] = values['isAlive']
    vtype = vehicle.get('vehicleType')
    descriptor = getattr(vtype, 'type', None)
    values.setdefault('level', getattr(vtype, 'level', MISSING))
    values.setdefault('tank_id', getattr(descriptor, 'compactDescr', MISSING))
    values.setdefault('vehicle', getattr(descriptor, 'shortUserString', ''))
    for key in NUMERIC:
        if not available:
            values[key] = MISSING
        else:
            values.setdefault(key, MISSING)
    colors = {}
    for key, value in values.items():
        if key.startswith('c_'):
            colors[key[2:]] = str(value).lstrip('#')
    for metric in ('wn8', 'wnx', 'winrate', 'battles', 'eff', 'wgr', 'xwn8', 'xeff', 't_battles', 't_winrate', 'tdv'):
        source = {'t_battles': 'battles', 't_winrate': 'winrate'}.get(metric, metric)
        colors[metric] = getStatisticColor(source, values[metric], scale).lstrip('#') if available and values[metric] != MISSING else 'AAAAAA'
    colors['tBattles'] = colors['t_battles']
    colors['kb'] = colors['battles']
    rating = (info or {}).get('_rating', 'wn8')
    if rating not in ('wn8', 'wnx', 'eff', 'wgr', 'winrate', 'xwn8', 'xeff'):
        rating = 'wn8'
    values['r'] = values.get(rating, MISSING)
    colors['r'] = colors.get(rating, 'AAAAAA')
    colors['xr'] = colors['r']
    colors['system'] = values.get('_systemColor', '96FF00' if values.get('ally') else 'F50800')
    colors['spotted'] = {'lost': 'D9D9D9', 'spotted': 'FFBB00', 'dead': 'FFFFFF'}.get(values.get('spotted'), '000000')
    values['stat-available'] = available
    values['anonym'] = bool(vehicle.get('isAnonymized', False))
    values['r_size'] = {'xwn8': 2, 'xeff': 2, 'winrate': 2, 'wgr': 5}.get(rating, 4)
    values['c'] = colors
    aliases = {'t-battles': 't_battles', 't-winrate': 't_winrate', 'vehicle-short': 'vehicle', 'hp-max': 'hp_max'}
    escaped = dict((key, escape(value) if isinstance(value, (str, type(u''))) else value)
                   for key, value in values.items())

    def partition_top(text, separator):
        depth, index = 0, 0
        while index < len(text):
            pair = text[index:index + 2]
            if pair == '{{':
                depth += 1
                index += 2
                continue
            if pair == '}}':
                depth -= 1
                index += 2
                continue
            if not depth and text[index] == separator:
                return text[:index], True, text[index + 1:]
            index += 1
        return text, False, ''

    def condition(text):
        comparison = re.match(r'^([\w:-]+)(>=|<=|!=|==|>|<|=)(.+)$', text)
        if comparison:
            key, operator, expected = comparison.groups()
            value = values.get(aliases.get(key, key), MISSING)
            if value == MISSING or value is None:
                return False
            try:
                left, right = float(value), float(expected)
            except (ValueError, TypeError):
                left, right = type(u'')(value), expected
            return {'>': lambda: left > right, '<': lambda: left < right,
                    '>=': lambda: left >= right, '<=': lambda: left <= right,
                    '=': lambda: left == right, '==': lambda: left == right,
                    '!=': lambda: left != right}[operator]()
        value = values.get(aliases.get(text, text), MISSING)
        return value not in (MISSING, None, False, '', 0, 'false', '0')

    def evaluate(expression, depth):
        test, conditional, branches = partition_top(expression, '?')
        if conditional:
            yes, _, no = partition_top(branches, '|')
            return expand(yes if condition(test) else no, depth + 1)
        body, sep, fallback = partition_top(expression, '|')
        fallback = expand(fallback, depth + 1) if sep else MISSING
        body = expand(body, depth + 1)
        body, suffix_sep, suffix = body.partition('~')
        macro, percent, spec = body.partition('%')
        macro = aliases.get(macro, macro)
        if macro.startswith('c:'):
            key = aliases.get(macro[2:], macro[2:])
            return '#' + colors.get(key, 'AAAAAA')
        value = values.get(macro, MISSING)
        if macro == 'hp-ratio' or macro.startswith('hp-ratio:'):
            try:
                width = float(macro.partition(':')[2] or 100)
                hp, maximum = float(values['hp']), float(values['hp_max'])
                value = int(math.ceil(max(0, min(1000, width)) * max(0, min(1, hp / maximum)))) if maximum > 0 else 0
            except (KeyError, TypeError, ValueError, OverflowError):
                value = MISSING
        if macro == 'kb' and available and values.get('battles', MISSING) != MISSING:
            value = values['battles'] / 1000.0
        if value is None or value == MISSING:
            return fallback
        try:
            if percent:
                if not re.match(r'^-?[0-9]{0,3}(?:\.[0-9]{1,3})?[sdf]$', spec):
                    return fallback
                result = ('%' + spec) % value
                if spec.endswith('s'):
                    if suffix_sep and len(result) < len(value):
                        result += suffix
                elif suffix_sep:
                    result += suffix
            else:
                result = type(u'')(value) + (suffix if suffix_sep else '')
            return escape(result)
        except (TypeError, ValueError, OverflowError):
            return fallback

    def legacy(match):
        try:
            return RatingFormatter().vformat(match.group(0), (), escaped)
        except (ValueError, TypeError):
            return MISSING

    def expand(text, depth=0):
        if depth > 24:
            return MISSING
        result, cursor = [], 0
        while cursor < len(text):
            start = text.find('{{', cursor)
            if start < 0:
                result.append(re.sub(r'\{[^{}]*\}', legacy, text[cursor:]))
                break
            result.append(re.sub(r'\{[^{}]*\}', legacy, text[cursor:start]))
            end, nesting = start + 2, 1
            while end < len(text) and nesting:
                if text[end:end + 2] == '{{':
                    nesting += 1
                    end += 2
                elif text[end:end + 2] == '}}':
                    nesting -= 1
                    end += 2
                else:
                    end += 1
            if nesting:
                result.append(text[start:])
                break
            result.append(evaluate(text[start + 2:end - 2], depth))
            cursor = end
        return u''.join(result)

    template = re.sub(r'\{c_([A-Za-z0-9_]+)\}', r'{c:\1}', template)
    return expand(template)



class Events(object):
    SUPPORTED_REGIONS = ('eu', 'com', 'asia')
    _apiErrors = set()

    @staticmethod
    def read_response(url, timeout):
        deadline = time.time() + STATS_DEADLINE
        chunks, total = [], 0
        with closing(urllib2.urlopen(url, timeout=min(timeout, STATS_DEADLINE))) as response:
            while True:
                if time.time() >= deadline:
                    raise IOError('Statistics response deadline exceeded')
                chunk = response.read(min(65536, MAX_STATS_RESPONSE - total + 1))
                if time.time() >= deadline:
                    raise IOError('Statistics response deadline exceeded')
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_STATS_RESPONSE:
                    raise IOError('Statistics response exceeds size limit')
                chunks.append(chunk)
        return b''.join(chunks)

    @staticmethod
    def request(region, request, **kwargs):
        if region not in Events.SUPPORTED_REGIONS:
            LOG.warning(('Unsupported region for stats request: {}').format(region))
            return None
        kwargs['application_id'] = 'e4063b2b8eb85a484dfff9bb84822256'
        api = 'api.worldoftanks.%s' % region
        url = 'https://%s/%s/?%s' % (api, request, urllib.urlencode(kwargs))
        try:
            response = json.loads(Events.read_response(url, settings_service.getComponentDict(config)[TEAM_PANELS.PERFORMANCE]['requestTimeout']).decode('utf-8-sig'))
            if response.get('status') == 'error':
                error = response.get('error') or {}
                signature = (region, request, error.get('code'), error.get('message'))
                if signature not in Events._apiErrors:
                    Events._apiErrors.add(signature)
                    LOG.warning(('Stats API rejected {}/{}: {} ({})').format(region, request, error.get('message'), error.get('code')))
                return None
            return response.get('data')
        except Exception as error:
            LOG.warning(('Stats request failed: {}').format(error))
            return None

    @staticmethod
    def userRegion(databaseID):
        databaseID = int(databaseID)
        if 500000000 <= databaseID < 1000000000:
            return 'eu'
        elif 1000000000 <= databaseID < 2000000000:
            return 'com'
        elif databaseID >= 2000000000:
            return 'asia'
        return 'eu'


class CalculatorRating(object):
    _wn8Cache = {}
    _wn8Revision = None

    @staticmethod
    def _expectedFromVehicleData(vehicleData):
        if vehicleData is None:
            return None
        if not all(vehicleData.get(key) is not None for key in ('wn8expDamage', 'wn8expFrag', 'wn8expSpot', 'wn8expDef', 'wn8expWinRate')):
            return None
        try:
            expected = {
                'expDamage': float(vehicleData['wn8expDamage']),
                'expFrag': float(vehicleData['wn8expFrag']),
                'expSpot': float(vehicleData['wn8expSpot']),
                'expDef': float(vehicleData['wn8expDef']),
                'expWinRate': float(vehicleData['wn8expWinRate'])
            }
        except (TypeError, ValueError, OverflowError):
            return None
        if not all(value > 0 and not math.isnan(value) and not math.isinf(value) for value in expected.values()):
            return None
        return expected

    @staticmethod
    def eff(avgDmg, avgDef, avgCap, avgSpot, avgTier, avgFrag):
        if avgTier <= 0:
            avgTier = 1
        return int(round(avgDmg * (10.0 / (avgTier + 2)) * (0.23 + 2.0 * avgTier / 100) + avgFrag * 250 + avgSpot * 150 + math.log(avgCap + 1, 1.732) * 150 + avgDef * 150))

    @staticmethod
    def xeff(eff):
        if not eff:
            return 0
        value = calculateRatingScale('eff', eff)
        return value if value >= 0 else 0

    @staticmethod
    def xwn8(wn8):
        if not wn8:
            return 0
        value = calculateRatingScale('wn8', wn8)
        return value if value >= 0 else 0

    @staticmethod
    def getExpectedWn8(tankId):
        revision = getattr(scaleValuesInstance, 'wn8_revision', None)
        if revision != CalculatorRating._wn8Revision:
            CalculatorRating._wn8Cache.clear()
            CalculatorRating._wn8Revision = revision
        expected = CalculatorRating._wn8Cache.get(tankId)
        if expected is not None:
            return expected
        vehicleData = getVehicleInfoData(tankId)
        if vehicleData is None:
            return None
        expected = CalculatorRating._expectedFromVehicleData(vehicleData)
        if expected is not None:
            CalculatorRating._wn8Cache[tankId] = expected
            return expected

        values = [{}, {}, 0, 0]
        level = vehicleData.get('level', 0)
        level = 10 if level < 1 or level > 10 else level
        target_class_tag = vehicleData.get('vClass', '')
        for vData in scaleValuesInstance.getVehicleInfoDataArray():
            tank_level = vData.get('level', 0)
            if tank_level == level:
                expected = CalculatorRating._expectedFromVehicleData(vData)
                if expected is None:
                    continue
                values[2] += 1
                tank_class_tag = vData.get('vClass', '')
                if tank_class_tag == target_class_tag:
                    values[3] += 1
                for key in expected:
                    values[0][key] = values[0].get(key, 0) + expected.get(key, 0)
                    if tank_class_tag == target_class_tag:
                        values[1][key] = values[1].get(key, 0) + expected.get(key, 0)
        if values[3] > 0:
            for key in values[1]:
                values[1][key] /= values[3]
            CalculatorRating._wn8Cache[tankId] = values[1].copy()
            return CalculatorRating._wn8Cache[tankId]
        if values[2] > 0:
            for key in values[0]:
                values[0][key] /= values[2]
            CalculatorRating._wn8Cache[tankId] = values[0].copy()
            return CalculatorRating._wn8Cache[tankId]
        return None


class ArenaStatsListener(IArenaVehiclesController):
    """Native arena listener: the vehicle list and late joiners trigger statistics requests."""

    def __init__(self, stats):
        super(ArenaStatsListener, self).__init__()
        self.stats = stats

    def getControllerID(self):
        return BATTLE_CTRL_ID.MOD

    def getCtrlScope(self):
        return ARENA_LISTENER_SCOPE.VEHICLES

    def startControl(self, *args):
        pass

    def stopControl(self):
        pass

    def invalidateArenaInfo(self):
        self.stats.loadStats()

    def invalidateVehiclesInfo(self, arenaDP):
        self.stats.loadStats()

    def addVehicleInfo(self, vo, arenaDP):
        self.stats.loadStats()


class Statistics(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.playersInfo = {}
        self._consumers = set()
        self.statsCache = {}
        self.cacheTimestamp = {}
        self._pending = set()
        self._attempts = {}
        self._received = set()
        self._workers = 0
        self._retry = None
        self._responses = Queue()
        self._generation = 0
        self._detailRequested = set()
        self._poll = None
        self._localAccount = None
        self._localStats = None
        self._appliedCache = {}
        self._listener = ArenaStatsListener(self)
        self._attached = False
        self._listening = False

    def captureOwnStats(self, *args, **kwargs):
        settings = settings_service.getComponentDict(config)
        # Called on the main thread after hangar synchronization. No server requests.
        if not self.enabled():
            return
        player = getPlayer()
        dbID = getattr(player, 'databaseID', None)
        cache = ServicesLocator.itemsCache
        if not dbID or getattr(player, 'arena', None) is not None or not cache.isSynced():
            return
        if self._localAccount != str(dbID):
            self._localAccount, self._localStats = str(dbID), None
        try:
            items = cache.items
            from driftkings.core.profile_ratings import pure_random_stats
            stats = pure_random_stats(items.getAccountDossier())
            if stats is None:
                raise ValueError('Incomplete random-only vehicle dossiers')
            values = dict((key, getattr(stats, method)()) for key, method in (
                ('battles', 'getBattlesCount'), ('wins', 'getWinsCount'),
                ('damage_dealt', 'getDamageDealt'), ('frags', 'getFragsCount'),
                ('spotted', 'getSpottedEnemiesCount'), ('capture_points', 'getCapturePoints'),
                ('dropped_capture_points', 'getDroppedCapturePoints')))
            tanks = [{'tank_id': tankID,
                      'statistics': {'battles': cut.battlesCount, 'wins': cut.wins},
                      'mark_of_mastery': stats.getMarkOfMasteryForVehicle(tankID)}
                     for tankID, cut in stats.getVehicles().items()]
            for tank in tanks:
                if not hasattr(items, 'getVehicleDossier'):
                    continue
                dossier = items.getVehicleDossier(tank['tank_id'])
                if dossier is None:
                    continue
                random = dossier.getRandomStats()
                # Legacy clan/company counters must never enter the random-only WNX weights.
                if random.getBattlesCount() != tank['statistics']['battles']:
                    continue
                for key, method in (('damage_dealt', 'getDamageDealt'), ('frags', 'getFragsCount'),
                                    ('spotted', 'getSpottedEnemiesCount'),
                                    ('radio_assisted_damage', 'getDamageAssistedRadio'),
                                    ('track_assisted_damage', 'getDamageAssistedTrack'),
                                    ('stun_assisted_damage', 'getDamageAssistedStun')):
                    if hasattr(random, method):
                        tank['statistics'][key] = getattr(random, method)()
            # Vehicle dossiers already cached by the client; never fetch them here.
            if 'tdv' in json.dumps(settings):
                damage = {}
                for tankID, dossier in items.getVehicleDossiersIterator():
                    block = dossier['a15x15']
                    damage[tankID] = {'battles': block['battlesCount'], 'damage_dealt': block['damageDealt']}
                for tank in tanks:
                    if tank['tank_id'] in damage:
                        tank['damageStats'] = damage[tank['tank_id']]
            info = {'statistics': {'random': values}, 'global_rating': items.stats.globalRating,
                    'client_language': 'en'}
            self._localStats = {'info': info, 'tanks': tanks}
        except Exception as error:
            self._localStats = None
            LOG.warning(('Local statistics unavailable, using API: {}').format(error))

    def loadPlayerStats(self, databaseIDs, generation, tankIDs=None):
        try:
            self._loadPlayerStats(databaseIDs, generation, tankIDs)
        finally:
            # Completion marker: the main thread polls only while workers run.
            self._responses.put((generation, None, None, None))

    def _loadPlayerStats(self, databaseIDs, generation, tankIDs=None):
        try:
            info, tanks = self.fetchPlayerStats(databaseIDs)
        except Exception as error:
            LOG.warning(('Could not fetch player statistics: {}').format(error))
            info, tanks = {}, {}
        self._responses.put((generation, databaseIDs, info, tanks))
        for dbID, tankID in (tankIDs or {}).items():
            if generation != self._generation:
                break
            if dbID not in info or not info[dbID] or not tanks.get(dbID):
                continue
            if any(tank.get('tank_id') == tankID and 'damageStats' in tank for tank in tanks[dbID]):
                continue
            detail = g_event.request(g_event.userRegion(int(dbID)), 'wot/tanks/stats',
                                     account_id=dbID, tank_id=tankID,
                                     extra='random', fields='tank_id,random.damage_dealt,random.battles')
            entries = detail.get(dbID) if isinstance(detail, dict) else None
            for entry in entries or []:
                if entry.get('tank_id') != tankID:
                    continue
                updated = [dict(tank) for tank in tanks[dbID]]
                for tank in updated:
                    if tank.get('tank_id') == tankID:
                        tank['damageStats'] = entry.get('random', {})
                self._responses.put((generation, [], {dbID: info[dbID]}, {dbID: updated}))

    def fetchPlayerStats(self, databaseIDs):
        regions = {}
        for databaseID in databaseIDs:
            regions.setdefault(g_event.userRegion(int(databaseID)), []).append(databaseID)
        dataInfo, dataTanks = {}, {}
        for region in regions:
            accountFields = ['client_language', 'global_rating', 'statistics.random.battles', 'statistics.random.wins', 'statistics.random.damage_dealt', 'statistics.random.frags', 'statistics.random.spotted', 'statistics.random.capture_points', 'statistics.random.dropped_capture_points']
            tankFields = ['random.battles', 'mark_of_mastery', 'random.wins', 'random.damage_dealt', 'tank_id']
            tankFields += ['random.' + key for key in ('frags', 'spotted', 'radio_assisted_damage',
                                                      'track_assisted_damage', 'stun_assisted_damage')]
            regionAccounts = ','.join(regions[region])
            infoResponse = g_event.request(region, 'wot/account/info', account_id=regionAccounts, extra='statistics.random', fields=','.join(accountFields))
            if infoResponse:
                dataInfo.update(infoResponse)
            # tanks/stats accepts one account per request. Keep its random
            # counts paired with the account's random totals, never all-mode data.
            for databaseID in regions[region]:
                tanks_response = g_event.request(region, 'wot/tanks/stats', account_id=databaseID,
                                                 extra='random', fields=','.join(tankFields))
                if tanks_response and databaseID in tanks_response:
                    entries = tanks_response[databaseID]
                    dataTanks[databaseID] = None if entries is None else [
                        {'tank_id': entry['tank_id'], 'mark_of_mastery': entry.get('mark_of_mastery', 0),
                         'statistics': entry['random'], 'damageStats': entry['random']}
                        for entry in entries if entry.get('random') is not None]
        return dataInfo, dataTanks

    def applyPlayerStats(self, dataInfo, dataTanks, updateCache=True):
        if updateCache and settings_service.getComponentDict(config)[TEAM_PANELS.PERFORMANCE]['cacheEnabled']:
            currentTime = time.time()
            for dbID in dataInfo:
                if dataInfo[dbID] is not None and dataTanks.get(dbID) is not None:
                    self.statsCache[dbID] = {'info': dataInfo[dbID], 'tanks': dataTanks.get(dbID, None)}
                    self.cacheTimestamp[dbID] = currentTime
        hasStats = bool(dataInfo and dataTanks)
        pColorScheme = g_settings.getColorScheme('battle/player')
        for vehicleID, value in getPlayer().arena.vehicles.items():
            dbID = str(value['accountDBID'])
            if dbID not in dataInfo and dbID in self.playersInfo:
                continue
            try:
                self.applyPlayer(vehicleID, value, dbID, dataInfo, dataTanks, hasStats, pColorScheme)
            except Exception as error:
                self.playersInfo.pop(dbID, None)
                LOG.warning(('Could not apply statistics for {}: {}').format(dbID, error))

    def applyPlayer(self, vehicleID, value, dbID, dataInfo, dataTanks, hasStats, pColorScheme):
        settings = settings_service.getComponentDict(config)
        playerInfo = self.playersInfo[dbID] = {}
        team = self.sessionProvider.getCtx().getPlayerGuiProps(vehicleID, value['team']).name().replace('ally', 'teammate')
        playerInfo['name'] = value['name']
        playerInfo['team'] = value['team']
        playerInfo['isAlive'] = value['isAlive']
        playerInfo['level'] = value['vehicleType'].level if hasattr(value['vehicleType'], 'level') else 0
        playerInfo['tank_id'] = value['vehicleType'].type.compactDescr if hasattr(value['vehicleType'], 'type') else 0
        playerInfo['type'] = getVehicleClassTag(value['vehicleType'].type.tags) if hasattr(value['vehicleType'], 'type') else ''
        playerInfo['vehicle'] = value['vehicleType'].type.shortUserString if hasattr(value['vehicleType'], 'type') else ''
        playerInfo['clan'] = '[%s]' % value['clanAbbrev'] if value['clanAbbrev'] else ''
        playerInfo['deadPlayerName'] = ''
        playerInfo['deadPlayerVehicle'] = ''
        playerInfo['c_team'] = '#' + pColorScheme.getHexStr(team)
        playerInfo['t_battles'] = 0
        playerInfo['t_winrate'] = 0
        playerInfo['wn8'] = 0
        playerInfo['wnx'] = None
        playerInfo['eff'] = 0
        playerInfo['xwn8'] = 0
        playerInfo['xeff'] = 0
        playerInfo['spg_battles'] = 0
        playerInfo['mark_of_mastery'] = 0
        playerInfo['wgr'] = 0
        playerInfo['battles'] = 0
        playerInfo['winrate'] = 0
        playerInfo['kb'] = 0
        playerInfo['spg_percent'] = 0
        playerInfo['lang'] = 'en'
        playerInfo['nick'] = playerInfo['name'] + playerInfo['clan']
        playerInfo['short_nick'] = playerInfo['name']
        playerInfo['c_wn8'] = self.getColor('wn8', playerInfo['wn8'])
        playerInfo['c_battles'] = self.getColor('battles', playerInfo['battles'])
        playerInfo['c_winrate'] = self.getColor('winrate', playerInfo['winrate'])
        playerInfo['c_tBattles'] = self.getColor('t_battles', playerInfo['t_battles'])
        cachedData = self.statsCache.get(dbID, None) if settings[TEAM_PANELS.PERFORMANCE]['cacheEnabled'] else None
        if cachedData and dbID not in dataInfo:
            cacheAge = time.time() - self.cacheTimestamp.get(dbID, 0)
            if cacheAge < settings[TEAM_PANELS.PERFORMANCE]['cacheExpiry']:
                dataInfo[dbID] = cachedData['info']
                if dbID not in dataTanks and cachedData['tanks'] is not None:
                    dataTanks[dbID] = cachedData['tanks']
        if hasStats and dbID in dataInfo and dbID in dataTanks and dataInfo[dbID] is not None and dataTanks[dbID] is not None:
            battles = dataInfo[dbID]['statistics']['random']['battles']
            if battles > 0 and battles >= settings[TEAM_PANELS.PERFORMANCE]['minBattlesToShow']:
                wins = dataInfo[dbID]['statistics']['random']['wins']
                avgDmg = dataInfo[dbID]['statistics']['random']['damage_dealt'] / float(battles)
                avgFrags = dataInfo[dbID]['statistics']['random']['frags'] / float(battles)
                avgSpot = dataInfo[dbID]['statistics']['random']['spotted'] / float(battles)
                avgCap = dataInfo[dbID]['statistics']['random']['capture_points'] / float(battles)
                avgDef = dataInfo[dbID]['statistics']['random']['dropped_capture_points'] / float(battles)
                winrate = wins * 100.0 / float(battles)
                playerInfo['wgr'] = dataInfo[dbID]['global_rating']
                playerInfo['battles'] = battles
                playerInfo['winrate'] = int(round(winrate, 0))
                playerInfo['kb'] = "{0}k".format(int(round(battles / 1000.0))) if battles >= 1000 else str(battles)
                playerInfo['lang'] = dataInfo[dbID]['client_language']
                for tank in dataTanks[dbID]:
                    if tank['tank_id'] == playerInfo['tank_id'] and tank['statistics']['battles'] != 0:
                        playerInfo['t_battles'] = tank['statistics']['battles']
                        damageStats = tank.get('damageStats', {})
                        maxHP = getattr(value.get('vehicleType'), 'maxHealth', 0)
                        playerInfo['tdv'] = tank_damage_ratio(damageStats, maxHP)
                        playerInfo['mark_of_mastery'] = tank['mark_of_mastery']
                        if playerInfo['type'] == 'SPG':
                            playerInfo['spg_battles'] += tank['statistics']['battles']
                        playerInfo['t_winrate'] = int(round(tank['statistics']['wins'] * 100.0 / tank['statistics']['battles'], 0))
                playerInfo['wn8'] = self.wn8(dataTanks[dbID], winrate, avgDmg, avgFrags, avgSpot, avgDef)
                from driftkings.core.wnx import account_from_tanks
                playerInfo['wnx'] = account_from_tanks(dataTanks[dbID], battles)
                playerInfo['xwn8'] = g_calRating.xwn8(playerInfo['wn8'])
                playerInfo['eff'] = g_calRating.eff(avgDmg, avgDef, avgCap, avgSpot, playerInfo['level'], avgFrags)
                playerInfo['xeff'] = g_calRating.xeff(playerInfo['eff'])
                playerInfo['c_wn8'] = self.getColor('wn8', playerInfo['wn8'])
                playerInfo['c_winrate'] = self.getColor('winrate',  playerInfo['winrate'])
                playerInfo['c_battles'] = self.getColor('battles', playerInfo['battles'])
                playerInfo['c_tBattles'] = self.getColor('t_battles', playerInfo['t_battles'])

    def getPlayersInfo(self, accountDBID):
        return self.playersInfo.get(str(accountDBID), None)

    @staticmethod
    def wn8(dossier, winrate, avgDmg, avgFrags, avgSpot, avgDef):
        eFrags = eDmg = eSpot = eDef = eWinrate = eBattles = 0
        for tank in dossier:
            tankID = tank['tank_id']
            expVal = g_calRating.getExpectedWn8(tankID)
            if expVal is not None:
                battles = tank['statistics']['battles']
                eFrags += battles * expVal['expFrag']
                eDmg += battles * expVal['expDamage']
                eSpot += battles * expVal['expSpot']
                eDef += battles * expVal['expDef']
                eWinrate += battles * expVal['expWinRate']
                eBattles += battles
        if eBattles == 0:
            return 0
        rWin = max((winrate * eBattles / eWinrate - 0.71) / 0.29000000000000004, 0)
        rDmg = max((avgDmg * eBattles / eDmg - 0.22) / 0.78, 0)
        rFrag = max(min(rDmg + 0.2, (avgFrags * eBattles / eFrags - 0.12) / 0.88), 0)
        rSpot = max(min(rDmg + 0.1, (avgSpot * eBattles / eSpot - 0.38) / 0.62), 0)
        rDef = max(min(rDmg + 0.1, (avgDef * eBattles / eDef - 0.1) / 0.9), 0)
        return int(round(980 * rDmg + 210 * rDmg * rFrag + 155 * rFrag * rSpot + 75 * rDef * rFrag + 145 * min(1.8, rWin)))

    @staticmethod
    def getColor(rating, value):
        # Player-panel templates already provide the leading '#'.
        return getStatisticColor(rating, value, settings_service.getComponentDict(config).get(TEAM_PANELS.COLOR_SCALE, 0)).lstrip('#')

    def pollStats(self):
        self._poll = None
        while True:
            try:
                generation, ids, info, tanks = self._responses.get_nowait()
            except Empty:
                break
            if generation != self._generation:
                continue
            if ids is None:
                self._workers = max(0, self._workers - 1)
                continue
            self._pending.difference_update(ids)
            self._received.update(dbID for dbID in info if info[dbID] is not None and tanks.get(dbID) is not None)
            failed = [dbID for dbID in ids if dbID not in self._received and info.get(dbID, MISSING) is not None]
            if failed:
                # No answer at all (or info without tanks): not a closed profile.
                retry = time.time() - RETRY_SECONDS + FAILED_RETRY_SECONDS
                self._attempts.update((dbID, retry) for dbID in failed)
                if self._retry is None:
                    self._retry = callback(FAILED_RETRY_SECONDS, self.retryStats)
            try:
                self.applyPlayerStats(info, tanks)
            except Exception as error:
                LOG.warning(('Could not apply player statistics: {}').format(error))
        if self._workers and getattr(getPlayer(), 'arena', None) is not None:
            self._poll = callback(0.2, self.pollStats)

    def loadStats(self):
        player = getPlayer()
        arena = getattr(player, 'arena', None)
        if arena is None or not self.enabled():
            return
        ids = sorted(set(str(pl.get('accountDBID', 0)) for pl in arena.vehicles.values()
                         if pl.get('accountDBID', 0) > 0))
        cachedInfo, cachedTanks, missing = {}, {}, []
        wantsDamage = 'tdv' in json.dumps(settings_service.getComponentDict(config))
        currentTanks = {}
        signatures = {}
        for vehicleID, vehicle in arena.vehicles.items():
            dbID = str(vehicle.get('accountDBID', 0))
            descriptor = getattr(vehicle.get('vehicleType'), 'type', None)
            tankID = getattr(descriptor, 'compactDescr', 0)
            signatures.setdefault(dbID, []).append((vehicleID, tankID))
            if wantsDamage and tankID:
                currentTanks[dbID] = tankID
        for dbID in ids:
            local = self._localStats if dbID == self._localAccount else None
            cached = local or (self.statsCache.get(dbID) if settings_service.getComponentDict(config)[TEAM_PANELS.PERFORMANCE]['cacheEnabled'] else None)
            if cached and (local or time.time() - self.cacheTimestamp.get(dbID, 0) < settings_service.getComponentDict(config)[TEAM_PANELS.PERFORMANCE]['cacheExpiry']):
                signature = tuple(sorted(signatures.get(dbID, [])))
                stamp = (id(cached), signature, settings_service.getComponentDict(config).get(TEAM_PANELS.COLOR_SCALE, 0))
                if self._appliedCache.get(dbID) != stamp:
                    cachedInfo[dbID], cachedTanks[dbID] = cached['info'], cached['tanks']
                    self._appliedCache[dbID] = stamp
                if not local and dbID in currentTanks and (dbID, currentTanks[dbID]) not in self._detailRequested and dbID not in self._pending:
                    missing.append(dbID)
            elif (dbID not in self._pending and dbID not in self._received
                  and time.time() - self._attempts.get(dbID, 0) >= RETRY_SECONDS):
                # Without the cache, an account answered once this battle is not
                # fetched again; accounts without data wait before a retry.
                missing.append(dbID)
        if cachedInfo:
            self.applyPlayerStats(cachedInfo, cachedTanks, updateCache=False)
        for offset in range(0, len(missing), 100):
            batch = missing[offset:offset + 100]
            self._pending.update(batch)
            now = time.time()
            self._attempts.update((dbID, now) for dbID in batch)
            tankIDs = dict((dbID, currentTanks[dbID]) for dbID in batch if dbID in currentTanks)
            self._detailRequested.update(tankIDs.items())
            worker = threading.Thread(target=self.loadPlayerStats, args=(batch, self._generation, tankIDs))
            worker.setDaemon(True)
            self._workers += 1
            worker.start()
        if self._workers and self._poll is None:
            self._poll = callback(0.2, self.pollStats)

    def retryStats(self):
        self._retry = None
        self.loadStats()

    def pruneCache(self):
        performance = settings_service.getComponentDict(config)[TEAM_PANELS.PERFORMANCE]
        if not performance['cacheEnabled']:
            self.statsCache.clear(); self.cacheTimestamp.clear()
            return
        oldest = time.time() - performance['cacheExpiry']
        for dbID in [dbID for dbID, stamp in self.cacheTimestamp.items() if stamp < oldest]:
            self.statsCache.pop(dbID, None); self.cacheTimestamp.pop(dbID, None)
        if len(self.statsCache) > CACHE_LIMIT:
            keep = set(sorted(self.cacheTimestamp, key=self.cacheTimestamp.get, reverse=True)[:CACHE_LIMIT])
            for dbID in [dbID for dbID in self.statsCache if dbID not in keep]:
                self.statsCache.pop(dbID, None); self.cacheTimestamp.pop(dbID, None)

    def reset(self):
        self._generation += 1
        if self._poll is not None:
            cancelCallback(self._poll)
            self._poll = None
        self._pending.clear()
        self._detailRequested.clear()
        self._attempts.clear()
        self._received.clear()
        self._workers = 0
        if self._retry is not None:
            cancelCallback(self._retry)
            self._retry = None
        self.playersInfo = {}
        self._appliedCache.clear()
        try:
            self.pruneCache()
        except Exception as error:
            LOG.warning(('Could not prune statistics cache: {}').format(error))

    def attachArena(self):
        # The session's arena listeners call back with the vehicle list and with
        # late joiners during loading, which would otherwise wait for the 15 s refresh.
        self.detachArena()
        self._attached = bool(self.sessionProvider.addArenaCtrl(self._listener))

    def detachArena(self):
        if self._attached:
            self._attached = False
            self.sessionProvider.removeArenaCtrl(self._listener)

    def start(self):
        if self._listening:
            return
        provider = self.sessionProvider
        provider.onBattleSessionStart += self.attachArena
        provider.onBattleSessionStop += self.detachArena
        self._listening = True

    def enabled(self):
        settings = settings_service.getComponentDict(config)
        return bool((settings[GLOBAL.ENABLED] or self._consumers) and settings.get(TEAM_PANELS.STATS_ENABLED, True))

    def acquire(self, owner):
        self._consumers.add(owner)
        self.start()

    def release(self, owner):
        self._consumers.discard(owner)

    def stop(self):
        if not self._listening:
            return
        self.detachArena()
        provider = self.sessionProvider
        provider.onBattleSessionStart -= self.attachArena
        provider.onBattleSessionStop -= self.detachArena
        self._listening = False

config = None
g_stats = None
g_calRating = CalculatorRating()
g_event = Events()


def configure(owner):
    global config, g_stats
    config = owner
    if g_stats is None:
        g_stats = Statistics()
    return g_stats


def shared():
    if g_stats is None:
        from driftkings.settings.definitions.battle.team_panels import TeamPanelsSettings
        configure(TeamPanelsSettings())
    return g_stats
