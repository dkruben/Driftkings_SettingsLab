# -*- coding: utf-8 -*-
import datetime

import BattleReplay
from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK
from gui.impl.lobby.hangar.presenters.crew_presenter import CrewPresenter
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement
from Vehicle import Vehicle

from driftkings._constants import BATTLE_MARKS_OF_EXCELLENCE, GLOBAL, MARK_LEVELS, MARK_THRESHOLDS, MARKS_MIN_TIER
from driftkings.common.config.json_reader import loadJson
from driftkings.common.utils import events
from driftkings.common.utils.achievement_dossiers import getAchievementDossier
from driftkings.common.utils.colorratting import getMoeDamageColor, getStatisticColor
from driftkings.common.utils.game import checkKeys
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.battle_events import battleEvents
from driftkings.core.battle_policy import battle_policy
from driftkings.core.cache import cache_directory
from driftkings.core.callbacks import callback
from driftkings.core.hooks import on_event, override
from driftkings.core.keyboard import keyboard
from driftkings.core.marks_calculator import (battle_curve, battle_estimate, battle_target, ceil_damage,
                                              combined_damage, replay_calibration, statistics, valid_calibration)
from driftkings.flash.battle.messages import sendPanelMessage
from driftkings.game_constants import BATTLE_EVENT_TYPE, DAMAGE_EVENTS
from driftkings.gameface.battle.battle_marks_of_excellence import BattleMarksAdapter
from driftkings.settings.definitions.battle.battle_marks_of_excellence import \
    BattleMarksOfExcellenceSettings as Settings
from driftkings.settings.service import settings_service
from driftkings.views.marks_model import compact_model


class MarksBattleCache(object):
    def __init__(self, component):
        from driftkings.settings.sections import previous_name
        self.component = previous_name(component)
        self.path = cache_directory('gun_marks_battle')
        self.values = {}

    def load(self, quiet=True):
        self.values = loadJson(self.component, self.component + '_stats', self.values, self.path)
        self.save(quiet)

    def save(self, quiet=True):
        self.values = loadJson(self.component, self.component + '_stats', self.values, self.path, True, quiet=quiet)


class Worker(object):

    def __init__(self):
        # Kept across clearData(): arena, dossier and the per-session counters.
        self._arena = None
        self.dossier = None
        self.startCount = 0
        self.gunLevel = 0
        self.health = {}
        self.clearData()

    def clearData(self):
        today = datetime.datetime.toordinal(datetime.datetime.utcnow())
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
        self.values = [0, 0, 0, 0, today - 1, today - 1]
        self.name = ''
        self.vehicleID = None
        self.initiated = False
        self.replay = False
        self.approximate = False
        self.levels = []
        self.damages = []
        self.health.clear()
        self.battleDamageRatingIndex = []
        self.dateTime = today

    def getCurrentHangarData(self):
        if g_currentVehicle.item:
            self.damageRating = g_currentVehicle.getDossier().getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0
            self.movingAvgDamage = g_currentVehicle.getDossier().getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage')
            self.battleCount = g_currentVehicle.getDossier().getRandomStats().getBattlesCountVer2()
            self.level = g_currentVehicle.item.level >= MARKS_MIN_TIER
            self.name = '%s' % g_currentVehicle.item.name
            if self.level and self.movingAvgDamage:
                dBid = self.check_player_thread()
                if dBid not in marks_cache.values:
                    marks_cache.values[dBid] = {}
                if valid_calibration(marks_cache.values[dBid].get(self.name)):
                    self.requestCurData(self.damageRating, self.movingAvgDamage)
                else:
                    self.requestNewData(self.damageRating, self.movingAvgDamage)

    def onBattleEvents(self, events):
        if not g_panel.active or not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        guiSessionProvider = getPlayer().guiSessionProvider
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() == getPlayer().playerVehicleID:
            for feedbackEvent in events:
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
        if not g_panel.active or not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
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
        EDn = combined_damage(self.battleDamage, self.RADIO_ASSIST, self.TRACK_ASSIST, self.STUN_ASSIST)
        nextMark = 100.0 if self.values[0] == self.values[2] == 100.0 else battle_estimate(EDn, self.movingAvgDamage, self.values)
        self.initiated = self.values[1] and not nextMark >= self.damageRating and not self.damageRating - nextMark > 3

    def calcBattlePercents(self):
        self.levels, self.damages, stats, current_damage, within_limit, unavailable = battle_curve(
            self.values, self.damageRating, self.movingAvgDamage,
            settings_service.getComponentDict(config)[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_BATTLE_HALF_PERCENTS])
        _, _, p20, p40, p55, p65, p85, p95, p100 = stats
        if unavailable:
            self.initiated = False
        self.battleDamageRatingIndex = [0, p20, p40, p55, p65, p85, p95, p100]

    def keyPressed(self, event):
        settings = settings_service.getComponentDict(config)
        if not settings[GLOBAL.ENABLED] or not event.isKeyDown():
            return
        player = getPlayer()
        if not player.arena or not battle_policy.decision('battle_marks_of_excellence')[0]:
            return
        if checkKeys(settings[BATTLE_MARKS_OF_EXCELLENCE.BUTTON_RESET]):
            defaults = config.getSettingsDefaults()
            settings_service.apply(config, {
                BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT: defaults[BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT],
                BATTLE_MARKS_OF_EXCELLENCE.PANEL: defaults[BATTLE_MARKS_OF_EXCELLENCE.PANEL]})
        elif checkKeys(settings[BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_UP]):
            settings_service.apply(config, {BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT:
                min(1000, settings[BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT] + 10)})
        elif checkKeys(settings[BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_DOWN]):
            settings_service.apply(config, {BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT:
                max(10, settings[BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT] - 10)})

    def calc(self):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        if not self.level:
            return
        if not self.movingAvgDamage:
            return
        assists = (self.RADIO_ASSIST, self.TRACK_ASSIST, self.STUN_ASSIST)
        EDn = combined_damage(self.battleDamage, *assists)
        if self.values[3] == self.values[1]:
            g_panel.unavailable(self.vehicleID)
            return
        nextMark = battle_estimate(EDn, self.movingAvgDamage, self.values)
        p0, d0, p1, d1, t0, t1 = self.values
        unknown = t0 < self.dateTime or t1 < self.dateTime
        unknown = unknown or not (d0 and self.initiated)
        g_panel.setVisible(True)
        payload = compact_model(self.vehicleID, self.damageRating, nextMark, self.battleDamage,
                                assists, getattr(self, 'markTargets', {}), self.gunLevel, not unknown or self.replay,
                                self.approximate)
        g_panel.set_marks(payload)

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
        settings = settings_service.getComponentDict(config)
        if not settings[GLOBAL.ENABLED]:
            return
        if settings[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_BATTLE]:
            message = 'Mod: Marks of Excellence %s [by github.com/spoter]' % config.NAME
            message += '\nRe-Worked for [Driftkings]'
            color = 'Purple'
            sendPanelMessage(message, color)
        self.replay = BattleReplay.isPlaying()
        if self.replay and not settings[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_REPLAY]:
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

        g_panel.setVisible(False)
        dBid = self.check_player_thread()
        self.gunLevel = vehicle.publicInfo['marksOnGun']
        self.name = vehicle.typeDescriptor.name
        self.vehicleID = vehicle.typeDescriptor.type.compactDescr
        self.level = vehicle.typeDescriptor.level >= MARKS_MIN_TIER
        if not self.level:
            # Lower tiers show no panel at all, not even the "unavailable" state.
            return
        if dBid not in marks_cache.values:
            marks_cache.values[dBid] = {}
        if self.replay:
            settings = settings_service.getComponentDict(config)
            values, self.approximate = replay_calibration(
                marks_cache.values, dBid, self.name, settings[BATTLE_MARKS_OF_EXCELLENCE.REPLAY_BASE_PERCENT],
                settings[BATTLE_MARKS_OF_EXCELLENCE.REPLAY_BASE_DAMAGE], self.dateTime)
            if values is None:
                g_panel.unavailable(self.vehicleID)
                return
            self.damageRating, self.movingAvgDamage = values[2:4]

        if self.level and self.movingAvgDamage:
            keyboard.subscribe(self.keyPressed)
            self._arena = getPlayer().arena
            self._arena.onVehicleKilled += self.onVehicleKilled
            if self.approximate:
                # Borrowed or base data: never write it into the replay owner's cache.
                self.values = values
                self.initiated = False
            elif valid_calibration(marks_cache.values[dBid].get(self.name)):
                self.requestCurData(self.damageRating, self.movingAvgDamage)
            else:
                self.requestNewData(self.damageRating, self.movingAvgDamage)
            if self.values[1] == self.values[3]:
                g_panel.unavailable(self.vehicleID)
                return
            self.calcBattlePercents()
            self.markTargets = dict((limit, battle_target(limit, self.values)) for limit in MARK_THRESHOLDS)
            g_panel.setupSize()
            self.calc()
            if not self.replay:
                marks_cache.save(quiet=not self.values)
        else:
            g_panel.unavailable(self.vehicleID)

    def endBattle(self):
        keyboard.unsubscribe(self.keyPressed)
        if self._arena is not None:
            self._arena.onVehicleKilled -= self.onVehicleKilled
            self._arena = None
        from driftkings.core.callbacks import callbacks
        callbacks.cancelOwner(__name__)

    @staticmethod
    def check_player_thread():
        player = getPlayer()
        if hasattr(player, 'databaseID'):
            return '%s' % player.databaseID
        return '%s' % player.arena.vehicles[player.playerVehicleID]['accountDBID']

    @staticmethod
    def getNormalizeDigits(value):
        return ceil_damage(value)


    def calcStatistics(self, p, d):
        return statistics(p, d)


g_panel = BattleMarksAdapter()
config = Settings()
marks_cache = MarksBattleCache(config.NAME)
marks_cache.load(quiet=False)
worker = Worker()


@override(CrewPresenter, '_CrewPresenter__updateCrewModel')
def new__updateCrewModel(func, *args):
    worker.getCurrentHangarData()
    return func(*args)


@on_event(battleEvents.feedback)
def new_onBattleEvents(*args):
    if battle_policy.decision('battle_marks_of_excellence')[0]:
        worker.onBattleEvents(args[1])


@on_event(battleEvents.healthBefore)
def new_onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    worker.shots(self, newHealth, attackerID)


@override(Vehicle, 'startVisual')
def new_vehicleStartVisual(func, *args):
    func(*args)
    worker.initVehicle(args[0])


@on_event(events.PlayerAvatar.startGUI.after)
def new_startGUI(*args):
    if battle_policy.decision('battle_marks_of_excellence')[0]:
        g_panel.startBattle()
        worker.startBattle()


@on_event(events.PlayerAvatar.destroyGUI.before)
def new_destroyGUI(*args):
    try:
        worker.endBattle()
    finally:
        g_panel.stopBattle()
        worker.clearData()


@override(MarkOnGunAchievement, 'getUserCondition')
def new_getUserCondition(func, *args):
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_STATISTIC]:
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
                index = settings_service.getComponentDict(config).get(BATTLE_MARKS_OF_EXCELLENCE.COLOR_RATING, 0)
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
                            for level in map(int, MARK_LEVELS[1:]))
                temp = config.i18n['UI_tooltips'].format(**data)
                return temp
    return func(*args)


def init():
    g_panel.install()


def fini():
    try:
        worker.endBattle()
    finally:
        g_panel.dispose()
        worker.clearData()
