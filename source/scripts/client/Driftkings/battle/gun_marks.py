# -*- coding: utf-8 -*-
from __future__ import print_function

import datetime
import math

import BattleReplay
import BigWorld
import Keys
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from CurrentVehicle import g_currentVehicle
from Vehicle import Vehicle
from constants import ARENA_BONUS_TYPE
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.battle_control.controllers import feedback_events
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement
from helpers import getFullClientVersion
from gui.impl.lobby.hangar.presenters.crew_presenter import CrewPresenter

from Driftkings._constants import GLOBAL, MARKS_ON_GUN_BATTLE
from Driftkings.common import loadJson, checkKeys, getPlayer, sendPanelMessage, getStatisticColor, getMoeDamageColor, getComparisonColor
from Driftkings.common.utils.achievement_dossiers import getAchievementDossier
from Driftkings.core.cache import cache_directory
from Driftkings.core.callbacks import callback
from Driftkings.core.hooks import override
from Driftkings.core.keyboard import keyboard
from Driftkings.core.overlay import ElementType
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.gun_marks import MarksOnGunBattleSettings as Settings
from Driftkings.views.battle.gun_marks import Flash

DAMAGE_EVENTS = frozenset([BATTLE_EVENT_TYPE.RADIO_ASSIST, BATTLE_EVENT_TYPE.TRACK_ASSIST, BATTLE_EVENT_TYPE.STUN_ASSIST, BATTLE_EVENT_TYPE.DAMAGE, BATTLE_EVENT_TYPE.TANKING, BATTLE_EVENT_TYPE.RECEIVED_DAMAGE])
ASSIST_NAMES = ('assistSpot', 'assistTrack', 'assistSpam')
MARK_LEVELS = (0.0, 20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0)


class MarksBattleCache(object):
    def __init__(self, component):
        self.component = component
        self.path = cache_directory('gun_marks_battle')
        self.values = {}

    def load(self, quiet=True):
        self.values = loadJson(self.component, self.component + '_stats', self.values, self.path)
        self.save(quiet)

    def save(self, quiet=True):
        self.values = loadJson(self.component, self.component + '_stats', self.values, self.path, True, quiet=quiet)


class Worker(object):

    def __init__(self):
        self._arena = None
        self.altMode = False
        self.movingAvgDamage = 0.0
        self.damageRating = 0.0
        self.battleDamage = 0.0
        self.battleCount = 0
        self.RADIO_ASSIST = 0.0
        self.TRACK_ASSIST = 0.0
        self.STUN_ASSIST = 0.0
        self.TANKING = 0.0
        self.killed = False
        self.level = False
        self.values = [0, 0, 0, 0, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1]
        self.name = ''
        self.dossier = None
        self.initiated = False
        self.replay = False
        self.formatStrings = {'status': '', 'battleMarkOfGun': '', 'currentMarkOfGun': '', 'nextMarkOfGun': '', 'damageCurrent': '', 'damageCurrentPercent': '', 'damageNextPercent': '', 'damageToMark65': '', 'damageToMark85': '', 'damageToMark95': '', 'damageToMark100': '', 'damageToMarkInfo': '', 'damageToMarkInfoLevel': '', 'c_status': '', 'c_battleMarkOfGun': '', 'c_currentMarkOfGun': '', 'c__nextMarkOfGun': '', 'c_damageCurrent': '', 'c_damageCurrentPercent': '', 'c_damageNextPercent': '', 'c_damageToMark65': '', 'c_damageToMark85': '', 'c_damageToMark95': '', 'c_damageToMark100': '', 'c_damageToMarkInfo': '', 'c_damageToMarkInfoLevel': '', 'colorOpen': '<font color="{color}">', 'colorClose': '</font>', 'color': '', 'assistSpot': settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_SPOT], 'assistTrack': settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_TRACK], 'assistSpam': settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_SPAM]}
        self.messages = {
            'battleMessageskill4ltu': '<font size=\"20\">{c_battleMarkOfGun} ({currentMarkOfGun}){status}</font>\n',
            'battleMessageskill4ltuAlt': '<font size=\"20\">{c_battleMarkOfGun} ({currentMarkOfGun}){status}</font>\n<font size=\"12\">{c_damageCurrent} ({damageCurrentPercent})</font>',
            'battleMessagesMyp': '<font size=\"20\">{c_battleMarkOfGun}{c_damageCurrent}{status}</font>\n',
            'battleMessagesMypAlt': '<font size=\"20\">{c_battleMarkOfGun}{c_damageCurrent}{status}</font>\n<font size=\"15\">{currentMarkOfGun}{damageCurrentPercent}</font>',
            'battleMessagesspoter': '<font size=\"20\">{c_battleMarkOfGun}:{c_damageCurrent}{assistCurrent}</font>\n<font size=\"15\">{c_nextMarkOfGun}:{c_damageNextPercent}\n{currentMarkOfGun}:{damageCurrentPercent}</font>',
            'battleMessagesspoterAlt': '<font size=\"20\">{c_battleMarkOfGun}:{c_damageCurrent}{assistCurrent}</font>\n<font size=\"15\">{c_nextMarkOfGun}:{c_damageNextPercent}\n{currentMarkOfGun}:{damageCurrentPercent}</font>\n<font size=\"12\">{c_damageToMark65}{c_damageToMark85}\n{c_damageToMark95}{c_damageToMark100}</font>',
            'battleMessagescircon': '<font size=\"14\">{currentMarkOfGun}</font> <font size=\"10\">{damageCurrentPercent}</font><font size=\"14\"> ~ {c_nextMarkOfGun}</font> <font size=\"10\">{c_damageNextPercent}</font>\n<font size=\"20\">{c_battleMarkOfGun}{status}</font><font size=\"14\">{c_damageCurrent}</font>',
            'battleMessagescirconAlt': '<font size=\"14\">{currentMarkOfGun}</font> <font size=\"10\">{damageCurrentPercent}</font><font size=\"14\"> ~ {c_nextMarkOfGun}</font> <font size=\"10\">{c_damageNextPercent}</font>\n<font size=\"20\">{c_battleMarkOfGun}{status}</font><font size=\"14\">{c_damageCurrent}</font>\n<font size=\"12\">{c_damageToMark65}{c_damageToMark85}\n{c_damageToMark95}{c_damageToMark100}</font>',
            'battleMessageReplay': '<font size=\"72\">{battleMarkOfGun}</font>',
            'battleMessageReplayAlt': '<font size=\"72\">{battleMarkOfGun}</font><font size=\"32\">{damageCurrent}</font>',
            'battleMessageReplayColor': '<font size=\"72\">{c_battleMarkOfGun}</font>',
            'battleMessageReplayColorAlt': '<font size=\"72\">{c_battleMarkOfGun}</font><font size=\"32\">{c_damageCurrent}</font>',
            'battleMessageoldskool': '<font size=\"15\">{c_battleMarkOfGun}\n{c_damageCurrent}{assistCurrent}</font>',
            'battleMessageoldskoolAlt': '<font size=\"15\">{c_battleMarkOfGun}<tab>{c_nextMarkOfGun}\n{c_damageCurrent}{assistCurrent}<tab>{c_damageNextPercent}</font>',
            'battleMessagesspoterNew': '<font size=\"32\">{c_battleMarkOfGun}{c_damageCurrent}</font>',
            'battleMessagesspoterNewAlt': '<font size=\"32\">{c_nextMarkOfGun}:{c_damageNextPercent}</font>\n<font size=\"32\">{c_damageToMark100}</font>',
            'battleMessageskorbenDallasNoMercy': '<p align=\"right\"><font size=\"54\"><font color=\"{status}\">{battleMarkOfGun}</font></font></p>\n<p align=\"right\"><font size=\"22\">{damageCurrent}</font></p>\n<p align=\"right\"><font size=\"22\">{damageCurrentPercent}</font></p>',
            'battleMessageskorbenDallasNoMercyAlt': '<p align=\"right\"><font size=\"54\"><font color=\"{status}\">{battleMarkOfGun}</font></font></p>\n<p align=\"right\"><font size=\"22\">{damageCurrent}</font></p>\n<p align=\"right\"><font size=\"22\">{damageCurrentPercent}</font></p>',
        }
        self.levels = []
        self.damages = []
        self.battleMessage = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE] if not self.altMode else settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ALT]
        self.checkBattleMessage()
        self.health = {}
        self.battleDamageRatingIndex = []
        self.startCount = 0
        self.gunLevel = 0
        self.dateTime = datetime.datetime.toordinal(datetime.datetime.utcnow())

    def checkBattleMessage(self):
        if not settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI]:
            self.battleMessage = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE] if not self.altMode else settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ALT]
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 1:
            self.battleMessage = self.messages['battleMessageskill4ltu'] if not self.altMode else self.messages['battleMessageskill4ltuAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 2:
            self.battleMessage = self.messages['battleMessagesMyp'] if not self.altMode else self.messages['battleMessagesMypAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 3:
            self.battleMessage = self.messages['battleMessagesspoter'] if not self.altMode else self.messages['battleMessagesspoterAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 4:
            self.battleMessage = self.messages['battleMessagescircon'] if not self.altMode else self.messages['battleMessagescirconAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 5:
            self.battleMessage = self.messages['battleMessageReplay'] if not self.altMode else self.messages['battleMessageReplayAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 6:
            self.battleMessage = self.messages['battleMessageReplayAlt'] if not self.altMode else self.messages['battleMessageReplayAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 7:
            self.battleMessage = self.messages['battleMessageReplayColor'] if not self.altMode else self.messages['battleMessageReplayColorAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 8:
            self.battleMessage = self.messages['battleMessageReplayColorAlt'] if not self.altMode else self.messages['battleMessageReplayColorAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 9:
            self.battleMessage = self.messages['battleMessageoldskool'] if not self.altMode else self.messages['battleMessageoldskoolAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 10:
            self.battleMessage = self.messages['battleMessagesspoterNew'] if not self.altMode else self.messages['battleMessagesspoterNewAlt']

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 11:
            self.battleMessage = self.messages['battleMessageskorbenDallasNoMercy'] if not self.altMode else self.messages['battleMessageskorbenDallasNoMercyAlt']

    def clearData(self):
        self.altMode = False
        self.movingAvgDamage = 0.0
        self.damageRating = 0.0
        self.battleDamage = 0.0
        self.battleCount = 0
        self.RADIO_ASSIST = 0.0
        self.TRACK_ASSIST = 0.0
        self.STUN_ASSIST = 0.0
        self.TANKING = 0.0
        self.killed = False
        self.level = False
        self.values = [0, 0, 0, 0, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1, datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1]
        self.name = ''
        self.initiated = False
        self.replay = False
        self.formatStrings = {'status': '', 'battleMarkOfGun': '', 'currentMarkOfGun': '', 'nextMarkOfGun': '', 'damageCurrent': '', 'damageCurrentPercent': '', 'damageNextPercent': '', 'damageToMark65': '', 'damageToMark85': '', 'damageToMark95': '', 'damageToMark100': '', 'damageToMarkInfo': '', 'damageToMarkInfoLevel': '', 'c_status': '', 'c_battleMarkOfGun': '', 'c_currentMarkOfGun': '', 'c__nextMarkOfGun': '', 'c_damageCurrent': '', 'c_damageCurrentPercent': '', 'c_damageNextPercent': '', 'c_damageToMark65': '', 'c_damageToMark85': '', 'c_damageToMark95': '', 'c_damageToMark100': '', 'c_damageToMarkInfo': '', 'c_damageToMarkInfoLevel': '', 'colorOpen': '<font color="{color}">', 'colorClose': '</font>', 'color': '', 'assistSpot': settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_SPOT], 'assistTrack': settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_TRACK], 'assistSpam': settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_ASSIST_SPAM]}
        self.levels = []
        self.damages = []
        self.checkBattleMessage()
        self.health.clear()
        self.battleDamageRatingIndex = []
        self.dateTime = datetime.datetime.toordinal(datetime.datetime.utcnow())

    def getCurrentHangarData(self):
        if g_currentVehicle.item:
            self.damageRating = g_currentVehicle.getDossier().getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
            self.movingAvgDamage = g_currentVehicle.getDossier().getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            self.battleCount = g_currentVehicle.getDossier().getRandomStats().getBattlesCountVer2()
            self.level = g_currentVehicle.item.level > 4
            self.name = '%s' % g_currentVehicle.item.name
            if self.level and self.movingAvgDamage:
                dBid = self.check_player_thread()
                if dBid not in marks_cache.values:
                    marks_cache.values[dBid] = {}
                if self.name in marks_cache.values[dBid]:
                    self.requestCurData(self.damageRating, self.movingAvgDamage)
                else:
                    self.requestNewData(self.damageRating, self.movingAvgDamage)

    def onBattleEvents(self, events):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        guiSessionProvider = getPlayer().guiSessionProvider
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() == getPlayer().playerVehicleID:
            for data in events:
                feedbackEvent = feedback_events.PlayerFeedbackEvent.fromDict(data)
                eventType = feedbackEvent.getBattleEventType()
                if eventType in DAMAGE_EVENTS:
                    extra = feedbackEvent.getExtra()
                    if extra:
                        if eventType == BATTLE_EVENT_TYPE.RADIO_ASSIST:
                            self.RADIO_ASSIST += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.TRACK_ASSIST:
                            self.TRACK_ASSIST += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.STUN_ASSIST:
                            self.STUN_ASSIST += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.TANKING:
                            self.TANKING += float(extra.getDamage())
                        if eventType == BATTLE_EVENT_TYPE.DAMAGE:
                            arenaDP = guiSessionProvider.getArenaDP()
                            if arenaDP.isEnemyTeam(arenaDP.getVehicleInfo(feedbackEvent.getTargetID()).team):
                                self.battleDamage += float(extra.getDamage())
            self.calc()

    def shots(self, avatar, newHealth, attackerID):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        if not avatar.isStarted:
            return
        if newHealth > 0 >= avatar.health:
            return
        player = getPlayer()
        if avatar.id not in self.health:
            self.health[avatar.id] = max(0, avatar.health)
        if not avatar.isPlayerVehicle and attackerID == player.playerVehicleID:
            arenaDP = player.guiSessionProvider.getArenaDP()
            vo = arenaDP.getVehicleInfo(avatar.id)
            if not arenaDP.isEnemyTeam(vo.team):
                self.battleDamage -= float(max(0, self.health[avatar.id] - newHealth))
                self.calc()
        self.health[avatar.id] = max(0, avatar.health)

    def initVehicle(self, avatar):
        if not avatar.isStarted:
            return
        self.health[avatar.id] = max(0, avatar.health)

    def requestNewData(self, damageRating, movingAvgDamage):
        p0 = 0
        d0 = 0
        p1 = damageRating
        d1 = movingAvgDamage
        t0 = datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1
        self.values = [p0, d0, p1, d1, t0, t0]
        marks_cache.values[self.check_player_thread()][self.name] = self.values
        self.initiated = False

    def requestCurData(self, damageRating, movingAvgDamage):
        self.values = marks_cache.values[self.check_player_thread()][self.name]
        if len(self.values) == 4:
            tm = datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1
            self.values.extend([tm, tm])
            marks_cache.values[self.check_player_thread()][self.name] = self.values
        if movingAvgDamage not in self.values or datetime.datetime.toordinal(datetime.datetime.utcnow()) >= self.values[5] + 1:
            p0 = self.values[2]
            d0 = self.values[3]
            t0 = self.values[5]
            p1 = damageRating
            d1 = movingAvgDamage
            t1 = datetime.datetime.toordinal(datetime.datetime.utcnow())
            self.values = [p0, d0, p1, d1, t0, t1]
            marks_cache.values[self.check_player_thread()][self.name] = self.values
        if self.values[0] == self.values[2] and self.values[1] == self.values[3]:
            self.values[3] += 10
            self.values[5] = datetime.datetime.toordinal(datetime.datetime.utcnow())
            marks_cache.values[self.check_player_thread()][self.name] = self.values
        EDn = self.battleDamage + max(self.RADIO_ASSIST, self.TRACK_ASSIST, self.STUN_ASSIST)
        k = 0.0198019801980198022206547392443098942749202251434326171875  # 2 / (100.0 + 1)
        EMA = k * EDn + (1 - k) * self.movingAvgDamage
        p0, d0, p1, d1, t0, t1 = self.values
        result = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0) if p0 != 100.0 or p1 != 100.0 else 100.0
        nextMark = round(min(100.0, result), 2) if result > 0 else 0.0
        self.initiated = self.values[1] and not nextMark >= self.damageRating and not self.damageRating - nextMark > 3

    def getColor(self, percent, damage):
        a = filter(lambda x: x <= round(percent, 2), self.levels)
        i = self.levels.index(a[-1]) if a else 0
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            n = min(i + 1, len(self.levels) - 1)
        else:
            n = max(2, min(i + 1, len(self.levels) - 1))
        index = settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0)
        targets = self.battleDamageRatingIndex[1:]
        colorNowDamage = getMoeDamageColor(damage, targets, index)
        colorNextDamage = getMoeDamageColor(self.damages[n], targets, index)
        colorNextPercent = getStatisticColor('mog', percent, index)
        levels = self.levels[n] if self.levels else 0
        damages = self.damages[n] if self.damages else 0
        return levels, damages, colorNowDamage, colorNextDamage, colorNextPercent

    def calcBattlePercents(self):
        if len(self.values) == 4:
            p0, d0, p1, d1 = self.values
        else:
            p0, d0, p1, d1, t0, t1 = self.values
        _, _, p20, p40, p55, p65, p85, p95, p100 = worker.calcStatistics(self.damageRating, self.movingAvgDamage)
        curPercent = p1
        limit = min(30000, p100 * 5)
        nextPercent = float(int(curPercent + 1))
        halfPercent = nextPercent - curPercent >= 0.5
        EDn = 0
        k = 0.0198019801980198022206547392443098942749202251434326171875  # 2 / (100.0 + 1)
        EMA = k * EDn + (1 - k) * d1
        start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(start)
        self.damages.append(EDn)
        while start <= curPercent < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 11:
            self.formatStrings['damageCurrentPercent'] = '<b>%.0f</b>' % EDn if EDn < limit or self.replay else config.i18n['NaN']
        else:
            self.formatStrings['damageCurrentPercent'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_CURRENT_PERCENT] % EDn if EDn < limit or self.replay else config.i18n['NaN']
        self.levels.append(curPercent)
        self.damages.append(EDn)
        if halfPercent and settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            halfPercent = nextPercent - 0.5
            while start <= halfPercent < 100 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(halfPercent)
            self.damages.append(EDn)

        while start <= nextPercent < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent)
        self.damages.append(EDn)

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            nextPercent_0_5 = nextPercent + 0.5
            while start <= nextPercent_0_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent_0_5)
            self.damages.append(EDn)

        nextPercent1 = nextPercent + 1.0
        while start <= nextPercent1 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent1)
        self.damages.append(EDn)

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            nextPercent1_5 = nextPercent + 1.5
            while start <= nextPercent1_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent1_5)
            self.damages.append(EDn)

        nextPercent2 = nextPercent + 2.0
        while start <= nextPercent2 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent2)
        self.damages.append(EDn)

        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            nextPercent2_5 = nextPercent + 2.5
            while start <= nextPercent2_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent2_5)
            self.damages.append(EDn)

        nextPercent3 = nextPercent + 3.0
        while start <= nextPercent3 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent3)
        self.damages.append(EDn)
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            nextPercent3_5 = nextPercent + 3.5
            while start <= nextPercent3_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent3_5)
            self.damages.append(EDn)

        nextPercent4 = nextPercent + 4.0
        while start <= nextPercent4 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent4)
        self.damages.append(EDn)
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            nextPercent4_5 = nextPercent + 4.5
            while start <= nextPercent4_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent4_5)
            self.damages.append(EDn)

        nextPercent5 = nextPercent + 5.0
        while start <= nextPercent5 < 100.001 and 0 <= start <= 100 and EDn < limit:
            EDn += 1
            EMA = k * EDn + (1 - k) * d1
            start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        self.levels.append(nextPercent5)
        self.damages.append(EDn)
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE_HALF_PERCENTS]:
            nextPercent5_5 = nextPercent + 5.5
            while start <= nextPercent5_5 < 100.001 and 0 <= start <= 100 and EDn < limit:
                EDn += 1
                EMA = k * EDn + (1 - k) * d1
                start = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
            self.levels.append(nextPercent5_5)
            self.damages.append(EDn)
        if EDn >= min(30000, EDn * 5):
            self.initiated = False

        self.battleDamageRatingIndex = [0, p20, p40, p55, p65, p85, p95, p100]

        self.formatStrings['damageToMark65'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK65] % p65
        self.formatStrings['c_damageToMark65'] = '<font color="%s">%s</font>' % (getStatisticColor('mog', 65, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0)), self.formatStrings['damageToMark65'])

        self.formatStrings['damageToMark85'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK85] % p85
        self.formatStrings['c_damageToMark85'] = '<font color="%s">%s</font>' % (getStatisticColor('mog', 85, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0)), self.formatStrings['damageToMark85'])

        self.formatStrings['damageToMark95'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK95] % p95
        self.formatStrings['c_damageToMark95'] = '<font color="%s">%s</font>' % (getStatisticColor('mog', 95, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0)), self.formatStrings['damageToMark95'])

        self.formatStrings['damageToMark100'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK100] % p100
        self.formatStrings['c_damageToMark100'] = '<font color="%s">%s</font>' % (getStatisticColor('mog', 100, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0)), self.formatStrings['damageToMark100'])

        self.formatStrings['damageToMarkInfo'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO] % self.formatStrings['damageToMark100']
        self.formatStrings['c_damageToMarkInfo'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO] % self.formatStrings['damageToMarkInfo']
        self.formatStrings['damageToMarkInfoLevel'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO_LEVEL] % 100
        self.formatStrings['c_damageToMarkInfoLevel'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO] % self.formatStrings['damageToMarkInfoLevel']

        for i in [65, 85, 95, 100]:
            if self.damageRating < i:
                self.formatStrings['damageToMarkInfo'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO] % self.formatStrings['damageToMark%s' % i]
                self.formatStrings['c_damageToMarkInfo'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO] % self.formatStrings['c_damageToMark%s' % i]
                self.formatStrings['damageToMarkInfoLevel'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_TO_MARK_INFO_LEVEL] % i
                self.formatStrings['c_damageToMarkInfoLevel'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_DAMAGE_TO_MARK_INFO] % self.formatStrings['damageToMarkInfoLevel']
                break

    def checkMark(self, nextMark):
        levels = [65.0, 85.0, 95.0, 100.0]
        for i in levels[self.gunLevel - 4:]:
            if self.damageRating < i <= nextMark:
                return True
        return

    def keyPressed(self, event):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        player = getPlayer()
        if not player.arena:
            return
        if player.arena.bonusType != ARENA_BONUS_TYPE.REGULAR:
            return
        if self.level and self.movingAvgDamage:
            isKeyDownTrigger = event.isKeyDown()

            if event.key in [Keys.KEY_LALT, Keys.KEY_RALT]:
                if isKeyDownTrigger:
                    self.altMode = True
                    self.checkBattleMessage()
                    g_flash.setupSize()
                    self.calc()
                if event.isKeyUp():
                    self.altMode = False
                    self.checkBattleMessage()
                    g_flash.setupSize()
                    self.calc()
            if checkKeys(settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BUTTON_SHOW]) and isKeyDownTrigger:
                settings_service.apply(config, {MARKS_ON_GUN_BATTLE.UI: settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] + 1}, persist=False)
                if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] > 11:
                    settings_service.apply(config, {MARKS_ON_GUN_BATTLE.UI: 1}, persist=False)
                status = [config.i18n['UI_menu_UIConfig'], config.i18n['UI_menu_UIskill4ltu'], config.i18n['UI_menu_UIMyp'], config.i18n['UI_menu_UIspoter'], config.i18n['UI_menu_UIcircon'], config.i18n['UI_menu_UIReplay'], config.i18n['UI_menu_UIReplayDamage'], config.i18n['UI_menu_UIReplayColor'], config.i18n['UI_menu_UIReplayColorDamage'], config.i18n['UI_menu_UIoldskool'], config.i18n['UI_menu_UIspoterNew'], config.i18n['UI_menu_UIkorbenDallasNoMercy']]
                message = config.i18n['UI_message'] % status[settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI]]
                sendPanelMessage(message)
                self.checkBattleMessage()
                g_flash.setupSize()
                self.calc()
            if checkKeys(settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BUTTON_RESET]) and isKeyDownTrigger:
                settings_service.apply(config, {MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT: 100}, persist=False)
                sendPanelMessage(config.i18n['battleMessageSizeReset'])
                # noinspection PyTypeChecker
                settings_service.apply(config, {MARKS_ON_GUN_BATTLE.PANEL: {'x': 230.0}}, persist=False)
                g_flash.data[ElementType.LABEL]['x'] = 230.0
                # noinspection PyTypeChecker
                settings_service.apply(config, {MARKS_ON_GUN_BATTLE.PANEL: {'y': -228.0}}, persist=False)
                g_flash.data[ElementType.LABEL]['y'] = -228.0
                self.altMode = True
                self.checkBattleMessage()
                g_flash.setupSize()
                self.altMode = False
                g_flash.setupSize()
                self.calc()
            if checkKeys(settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BUTTON_SIZE_UP]) and isKeyDownTrigger:
                settings_service.apply(config, {MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT: min(1000, settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] + 10)}, persist=False)
                message = config.i18n['battleMessageSizeUp'] + '<b>[%s]</b>' % settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] < 1000 else config.i18n['battleMessageSizeLimitMax']
                sendPanelMessage(message)
                self.altMode = True
                self.checkBattleMessage()
                g_flash.setupSize()
                self.altMode = False
                g_flash.setupSize()
                self.calc()
            if checkKeys(settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BUTTON_SIZE_DOWN]) and isKeyDownTrigger:
                settings_service.apply(config, {MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT: max(10, settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] - 10)}, persist=False)
                message = config.i18n['battleMessageSizeDown'] + '<b>[%s]</b>' % settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] > 10 else config.i18n['battleMessageSizeLimitMin']
                sendPanelMessage(message)
                self.altMode = True
                self.checkBattleMessage()
                g_flash.setupSize()
                self.altMode = False
                g_flash.setupSize()
                self.calc()

    def calc(self):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        if not self.level:
            return
        if not self.movingAvgDamage:
            return
        assists = (self.RADIO_ASSIST, self.TRACK_ASSIST, self.STUN_ASSIST)
        assistCurrent = ASSIST_NAMES[assists.index(max(assists))]
        EDn = self.battleDamage + max(assists)
        k = 0.0198019801980198022206547392443098942749202251434326171875  # 2 / (100.0 + 1)
        EMA = k * EDn + (1 - k) * self.movingAvgDamage
        p0, d0, p1, d1, t0, t1 = self.values
        result = p0 + (EMA - d0) / (d1 - d0) * (p1 - p0)
        nextMark = round(min(100.0, result), 2) if result > 0.0 else 0.0
        unknown = t0 < self.dateTime or t1 < self.dateTime
        if not unknown and d0 and self.initiated or self.replay:
            if nextMark >= self.damageRating:
                self.formatStrings['color'] = getComparisonColor(nextMark, self.damageRating, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0))
                if self.checkMark(nextMark):
                    self.formatStrings['color'] = getStatisticColor('mog', nextMark, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0))
                self.formatStrings['status'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_STATUS_UP] if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] != 11 else self.formatStrings['color']
                self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_STATUS_UP], self.formatStrings['colorClose'])
            else:
                self.formatStrings['color'] = getComparisonColor(nextMark, self.damageRating, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0))
                if self.checkMark(nextMark):
                    self.formatStrings['color'] = getStatisticColor('mog', nextMark, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0))
                self.formatStrings['status'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_STATUS_DOWN] if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] != 11 else self.formatStrings['color']
                self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_STATUS_DOWN], self.formatStrings['colorClose'])
        else:
            self.formatStrings['color'] = getStatisticColor('mog', None, settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0))
            self.formatStrings['status'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_STATUS_UNKNOWN] if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] != 11 else self.formatStrings['color']
            self.formatStrings['c_status'] = '%s%s%s' % (self.formatStrings['colorOpen'], settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_C_STATUS_UNKNOWN], self.formatStrings['colorClose'])
            unknown = True
        self.formatStrings['battleMarkOfGun'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_BATTLE_MARK_OF_GUN] % nextMark
        self.formatStrings['c_battleMarkOfGun'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['battleMarkOfGun'], self.formatStrings['colorClose'])
        nextMarkOfGun, damage, colorNowDamage, colorNextDamage, colorNextPercent = self.getColor(nextMark, EDn)
        self.formatStrings['nextMarkOfGun'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_NEXT_MARK_OF_GUN] % nextMarkOfGun
        self.formatStrings['c_nextMarkOfGun'] = '%s%s%s' % ('<font color="%s">' % colorNextPercent if not unknown else self.formatStrings['colorOpen'], self.formatStrings['nextMarkOfGun'], self.formatStrings['colorClose'])
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 11:
            self.formatStrings['damageCurrent'] = "<b>%.0f</b>" % EDn
        else:
            self.formatStrings['damageCurrent'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_CURRENT] % EDn
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI] == 11:
            self.formatStrings['damageNextPercent'] = "<b>%.0f</b>" % damage if damage < 30000 or self.replay else config.i18n['NaN']
        else:
            self.formatStrings['damageNextPercent'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_DAMAGE_NEXT_PERCENT] % damage if damage < 30000 or self.replay else config.i18n['NaN']
        self.formatStrings['c_damageCurrent'] = '%s%s%s' % ('<font color="%s">' % colorNowDamage if not unknown else self.formatStrings['colorOpen'], self.formatStrings['damageCurrent'], self.formatStrings['colorClose'])
        self.formatStrings['c_damageCurrentPercent'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['damageCurrentPercent'], self.formatStrings['colorClose'])
        self.formatStrings['c_damageNextPercent'] = '%s%s%s' % ('<font color="%s">' % colorNextDamage if not unknown else self.formatStrings['colorOpen'], self.formatStrings['damageNextPercent'], self.formatStrings['colorClose'])
        self.formatStrings['assistCurrent'] = self.formatStrings[assistCurrent] if max(assists) else self.formatStrings['assistTrack']
        g_flash.setVisible(True)
        g_flash.set_text(self.battleMessage.format(**self.formatStrings).format(color=self.formatStrings['color']))

    @staticmethod
    def isAvailable():
        vehicle = getPlayer().getVehicleAttached()
        if vehicle is None:
            return
        return vehicle.id == getPlayer().playerVehicleID

    # noinspection PyUnusedLocal
    def onVehicleKilled(self, target_id, *args):
        if target_id == getPlayer().playerVehicleID:
            self.killed = True
            self.calc()

    def startBattle(self):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        if settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE]:
            message = 'Mod: Marks of Excellence %s [by github.com/spoter]' % config.ID
            message += '\nRe-Worked for [Driftkings]'
            color = 'Purple'
            sendPanelMessage(message, color)
            status = [config.i18n['UI_menu_UIConfig'], config.i18n['UI_menu_UIskill4ltu'], config.i18n['UI_menu_UIMyp'], config.i18n['UI_menu_UIspoter'], config.i18n['UI_menu_UIcircon'], config.i18n['UI_menu_UIReplay'], config.i18n['UI_menu_UIReplayDamage'], config.i18n['UI_menu_UIReplayColor'], config.i18n['UI_menu_UIReplayColorDamage'], config.i18n['UI_menu_UIoldskool'], config.i18n['UI_menu_UIspoterNew'], config.i18n['UI_menu_UIkorbenDallasNoMercy']]
            message = config.i18n['UI_message'] % status[settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.UI]]
            sendPanelMessage(message)
        self.replay = BattleReplay.isPlaying()
        if self.replay and not settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_REPLAY]:
            return
        self.startCount = 0
        callback(1.0, self.treadStartBattle)

    def treadStartBattle(self):
        vehicle = getPlayer().getVehicleAttached()
        if not vehicle:
            self.startCount += 1
            if self.startCount < 10:
                return callback(1.0, self.treadStartBattle)
            else:
                return

        g_flash.setVisible(False)
        dBid = self.check_player_thread()
        self.gunLevel = vehicle.publicInfo['marksOnGun']
        self.name = vehicle.typeDescriptor.name
        self.level = vehicle.typeDescriptor.level > 4
        if dBid not in marks_cache.values:
            marks_cache.values[dBid] = {}
        if self.replay:
            test = None
            if self.name in marks_cache.values[dBid]:
                test = dBid
            else:
                for ids in marks_cache.values:
                    if self.name in marks_cache.values[ids]:
                        test = ids
                        break
            if test:
                values = marks_cache.values[test][self.name]
                self.damageRating = values[2]
                self.movingAvgDamage = values[3]
            else:
                self.damageRating = 94.0
                self.movingAvgDamage = 3500.0
                self.name = 'ReplayTest'

        if self.level and self.movingAvgDamage:
            keyboard.subscribe(self.keyPressed)
            self._arena = getPlayer().arena
            self._arena.onVehicleKilled += self.onVehicleKilled
            self.formatStrings['currentMarkOfGun'] = settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_CURRENT_MARK_OF_GUN] % self.damageRating
            self.formatStrings['c_currentMarkOfGun'] = '%s%s%s' % (self.formatStrings['colorOpen'], self.formatStrings['currentMarkOfGun'], self.formatStrings['colorClose'])
            if self.name in marks_cache.values[dBid]:
                self.requestCurData(self.damageRating, self.movingAvgDamage)
            else:
                self.requestNewData(self.damageRating, self.movingAvgDamage)
            self.calcBattlePercents()
            g_flash.setupSize()
            self.calc()
            if 'ReplayTest' not in self.name:
                marks_cache.save(quiet=not self.values)

    def endBattle(self):
        keyboard.unsubscribe(self.keyPressed)
        if self._arena is not None:
            self._arena.onVehicleKilled -= self.onVehicleKilled
            self._arena = None
        from Driftkings.core.callbacks import callbacks
        callbacks.cancelOwner(__name__)

    @staticmethod
    def check_player_thread():
        player = getPlayer()
        if hasattr(player, 'databaseID'):
            return '%s' % player.databaseID
        return '%s' % player.arena.vehicles[player.playerVehicleID]['accountDBID']

    @staticmethod
    def getNormalizeDigits(value):
        return int(math.ceil(value))

    @staticmethod
    def calcPercent(ema, start, end, d, p):
        while start <= end < 100.001 and ema < 30000:
            ema += 0.1
            start = ema / d * p
        return ema

    @staticmethod
    def getNormalizeDigitsCoeff(value):
        return int(math.ceil(math.ceil(value / 10.0)) * 10)

    def calcStatistics(self, p, d):
        pC = math.floor(p) + 1
        dC = self.calcPercent(d, p, pC, d, p)
        p20 = self.calcPercent(0, 0.0, 20.0, d, p)
        p40 = self.calcPercent(0, 0.0, 40.0, d, p)
        p55 = self.calcPercent(0, 0.0, 55.0, d, p)
        p65 = self.calcPercent(0, 0.0, 65.0, d, p)
        p85 = self.calcPercent(0, 0.0, 85.0, d, p)
        p95 = self.calcPercent(0, 0.0, 95.0, d, p)
        p100 = self.calcPercent(0, 0.0, 100.0, d, p)
        data = [0, p20, p40, p55, p65, p85, p95, p100]
        idx = filter(lambda x: x >= p, MARK_LEVELS)[0]
        limit1 = dC
        limit2 = data[MARK_LEVELS.index(idx)]
        check = MARK_LEVELS.index(idx)
        delta = limit2 - limit1
        for value in xrange(len(data)):
            if data[value] == limit1 or data[value] == limit2:
                continue
            if value > check:
                data[value] = self.getNormalizeDigitsCoeff(data[value] + delta)
        if pC == 101:
            pC = 100
            dC = data[7]
        return pC, dC, data[1], data[2], data[3], data[4], data[5], data[6], data[7]


g_flash = Flash()
config = Settings()
marks_cache = MarksBattleCache(config.ID)
marks_cache.load(quiet=False)
worker = Worker()


@override(CrewPresenter, '_CrewPresenter__updateCrewModel')
def new__updateCrewModel(func, *args):
    worker.getCurrentHangarData()
    return func(*args)


@override(PlayerAvatar, 'onBattleEvents')
def new_onBattleEvents(func, *args):
    func(*args)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        worker.onBattleEvents(args[1])


@override(Vehicle, 'onHealthChanged')
def new_onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    worker.shots(self, newHealth, attackerID)
    func(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs)


@override(Vehicle, 'startVisual')
def new_vehicleStartVisual(func, *args):
    func(*args)
    worker.initVehicle(args[0])


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
        g_flash.startBattle()
        worker.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    try:
        if getPlayer().arena.bonusType == ARENA_BONUS_TYPE.REGULAR:
            g_flash.stopBattle()
            worker.endBattle()
            worker.clearData()
    except StandardError:
        pass
    func(*args)


@override(MarkOnGunAchievement, 'getUserCondition')
def new_getUserCondition(func, *args):
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MARKS_ON_GUN_BATTLE.SHOW_IN_STATISTIC]:
        targetData = getAchievementDossier(args[0])
        if targetData is not None:
            damage = ProfileUtils.getValueOrUnavailable(ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamage()))
            track = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedTrack))
            radio = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats()._getAvgValue(targetData.getRandomStats().getBattlesCountVer2, targetData.getRandomStats().getDamageAssistedRadio))
            stun = ProfileUtils.getValueOrUnavailable(targetData.getRandomStats().getAvgDamageAssistedStun())
            currentDamage = int(damage + max(track, radio, stun))
            damageRating = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
            movingAvgDamage = targetData.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            if damageRating:
                pC, dC, p20, p40, p55, p65, p85, p95, p100 = worker.calcStatistics(damageRating, movingAvgDamage)
                levels = [p20, p40, p55, p65, p85, p95, p100]
                index = settings_service.getComponentDict(config).get(MARKS_ON_GUN_BATTLE.COLOR_RATING, 0)
                data = {
                    'nextPercent': '%.0f' % pC,
                    'needDamage': '<font color="%s">%s</font>' % (getMoeDamageColor(int(dC), levels, index), int(dC)),
                    'currentMovingAvgDamage': '<font color="%s">%s</font>' % (getMoeDamageColor(movingAvgDamage, levels, index), movingAvgDamage),
                    'currentDamage': '<font color="%s">%s</font>' % (getMoeDamageColor(currentDamage, levels, index), currentDamage),
                    '_20': worker.getNormalizeDigits(p20),
                    '_40': worker.getNormalizeDigits(p40),
                    '_55': worker.getNormalizeDigits(p55),
                    '_65': worker.getNormalizeDigits(p65),
                    '_85': worker.getNormalizeDigits(p85),
                    '_95': worker.getNormalizeDigits(p95),
                    '_100': worker.getNormalizeDigits(p100)
                }
                data.update(('c%s' % level, getStatisticColor('mog', level, index))
                            for level in (20, 40, 55, 65, 85, 95, 100))
                temp = config.i18n['UI_tooltips'].format(**data)
                return temp
    return func(*args)


_exports = {'MoESetupSize': g_flash.setupSize, 'MoEText': g_flash.set_text,
            'MoEUpdateObject': g_flash.updateObject, 'MoEData': g_flash.getData,
            'MoEName': g_flash.getNames}
_previousExports = {}
_MISSING = object()


def init():
    for name, value in _exports.items():
        _previousExports[name] = getattr(BigWorld, name, _MISSING)
        setattr(BigWorld, name, value)


def fini():
    worker.endBattle()
    g_flash.stopBattle()
    worker.clearData()
    for name, value in _exports.items():
        if getattr(BigWorld, name, None) == value:
            previous = _previousExports.get(name, _MISSING)
            if previous is _MISSING:
                delattr(BigWorld, name)
            else:
                setattr(BigWorld, name, previous)
    _previousExports.clear()
