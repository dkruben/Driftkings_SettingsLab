# -*- coding: utf-8 -*-
import datetime

import BattleReplay
import BigWorld
from CurrentVehicle import g_currentVehicle
from gui.impl.lobby.hangar.presenters.crew_presenter import CrewPresenter
from Vehicle import Vehicle

from driftkings._constants import BATTLE_MARKS_OF_EXCELLENCE, GLOBAL, MARK_THRESHOLDS, MARKS_MIN_TIER
from driftkings.common.config.json_reader import loadJson
from driftkings.common.utils import events
from driftkings.common.utils.dossiers import damage_rating, total_record
from driftkings.common.utils.game import checkKeys
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
from driftkings.settings.definitions.battle.battle_marks_of_excellence import BattleMarksOfExcellenceSettings
from driftkings.settings.service import settings_service
from driftkings.views.marks_model import compact_model


class MarksBattleCache(object):
    # Prepara o ficheiro e os dados da cache de calibração das marcas.
    def __init__(self, component):
        from driftkings.settings.sections import previous_name
        self.component = previous_name(component)
        self.path = cache_directory('gun_marks_battle')
        self.values = {}

    # Carrega a calibração guardada para as marcas de excelência.
    def load(self, quiet=True):
        self.values = loadJson(self.component, self.component + '_stats', self.values, self.path)
        self.save(quiet)

    # Guarda a calibração das marcas no ficheiro de cache.
    def save(self, quiet=True):
        self.values = loadJson(self.component, self.component + '_stats', self.values, self.path, True, quiet=quiet)


class Worker(object):

    # Inicializa as referências da sessão e os contadores de dano das marcas.
    def __init__(self):
        # Kept across clearData(): arena, dossier and the per-session counters.
        self._arena = None
        self.dossier = None
        self.startCount = 0
        self.gunLevel = 0
        self.health = {}
        self.clearData()

    # Repõe os contadores e os dados calculados para a batalha.
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

    # Lê do dossiê os dados de marcas do veículo selecionado.
    def getCurrentHangarData(self):
        if g_currentVehicle.item:
            dossier = g_currentVehicle.getDossier()
            self.damageRating = damage_rating(dossier)
            self.movingAvgDamage = total_record(dossier, 'movingAvgDamage')
            self.battleCount = dossier.getRandomStats().getBattlesCountVer2()
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

    # Acumula os danos e a assistência relevantes para as marcas.
    def onBattleEvents(self, events):
        if not g_panel.active or not settings_service.getComponentDict(battle_marks_of_excellence_settings)[GLOBAL.ENABLED]:
            return
        guiSessionProvider = BigWorld.player().guiSessionProvider
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() == BigWorld.player().playerVehicleID:
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

    # Processa a perda de vida dos veículos para atualizar os danos observados.
    def shots(self, avatar, newHealth, attackerID):
        if not g_panel.active or not settings_service.getComponentDict(battle_marks_of_excellence_settings)[GLOBAL.ENABLED]:
            return
        if not avatar.isStarted:
            return
        if newHealth > 0 >= avatar.health:
            return
        player = BigWorld.player()
        if avatar.id not in self.health:
            self.health[avatar.id] = max(0, avatar.health)
        if not avatar.isPlayerVehicle and attackerID == player.playerVehicleID:
            arenaDP = player.guiSessionProvider.getArenaDP()
            vo = arenaDP.getVehicleInfo(avatar.id)
            if not arenaDP.isEnemyTeam(vo.team):
                self.battleDamage -= float(max(0, self.health[avatar.id] - newHealth))
                self.calc()
        self.health[avatar.id] = max(0, avatar.health)

    # Regista a vida inicial de um veículo que entra no mundo.
    def initVehicle(self, avatar):
        if not avatar.isStarted:
            return
        self.health[avatar.id] = max(0, avatar.health)

    # Cria uma calibração inicial quando não existem dados válidos em cache.
    def requestNewData(self, damageRating, movingAvgDamage):
        p0 = 0
        d0 = 0
        p1 = damageRating
        d1 = movingAvgDamage
        t0 = datetime.datetime.toordinal(datetime.datetime.utcnow()) - 1
        self.values = [p0, d0, p1, d1, t0, t0]
        marks_cache.values[self.check_player_thread()][self.name] = self.values
        self.initiated = False

    # Recupera a calibração existente e atualiza os dados do veículo.
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

    # Calcula a curva de dano e os patamares percentuais das marcas.
    def calcBattlePercents(self):
        self.levels, self.damages, stats, current_damage, within_limit, unavailable = battle_curve(
            self.values, self.damageRating, self.movingAvgDamage,
            settings_service.getComponentDict(battle_marks_of_excellence_settings)[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_BATTLE_HALF_PERCENTS])
        _, _, p20, p40, p55, p65, p85, p95, p100 = stats
        if unavailable:
            self.initiated = False
        self.battleDamageRatingIndex = [0, p20, p40, p55, p65, p85, p95, p100]

    # Trata os atalhos configurados para o painel de marcas.
    def keyPressed(self, event):
        settings = settings_service.getComponentDict(battle_marks_of_excellence_settings)
        if not settings[GLOBAL.ENABLED] or not event.isKeyDown():
            return
        player = BigWorld.player()
        if not player.arena or not battle_policy.decision('battle_marks_of_excellence')[0]:
            return
        if checkKeys(settings[BATTLE_MARKS_OF_EXCELLENCE.BUTTON_RESET]):
            defaults = battle_marks_of_excellence_settings.getSettingsDefaults()
            settings_service.apply(battle_marks_of_excellence_settings, {
                BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT: defaults[BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT],
                BATTLE_MARKS_OF_EXCELLENCE.PANEL: defaults[BATTLE_MARKS_OF_EXCELLENCE.PANEL]})
        elif checkKeys(settings[BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_UP]):
            settings_service.apply(battle_marks_of_excellence_settings, {BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT:
                min(1000, settings[BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT] + 10)})
        elif checkKeys(settings[BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_DOWN]):
            settings_service.apply(battle_marks_of_excellence_settings, {BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT:
                max(10, settings[BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT] - 10)})

    # Recalcula o progresso estimado das marcas com os dados da batalha.
    def calc(self):
        if not settings_service.getComponentDict(battle_marks_of_excellence_settings)[GLOBAL.ENABLED]:
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

    # Verifica se o veículo observado é o veículo do jogador.
    @staticmethod
    def isAvailable():
        vehicle = BigWorld.player().getVehicleAttached()
        if vehicle is None:
            return
        return vehicle.id == BigWorld.player().playerVehicleID

    # noinspection PyUnusedLocal
    # Assinala a destruição do veículo do jogador e atualiza a estimativa.
    def onVehicleKilled(self, target_id, *args):
        if target_id == BigWorld.player().playerVehicleID:
            self.killed = True
            self.calc()

    # Prepara o módulo de marcas de excelência em batalha para a batalha atual.
    def startBattle(self):
        settings = settings_service.getComponentDict(battle_marks_of_excellence_settings)
        if not settings[GLOBAL.ENABLED]:
            return
        if settings[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_BATTLE]:
            message = 'Mod: Marks of Excellence %s [by github.com/spoter]' % battle_marks_of_excellence_settings.NAME
            message += '\nRe-Worked for [Driftkings]'
            color = 'Purple'
            sendPanelMessage(message, color)
        self.replay = BattleReplay.isPlaying()
        if self.replay and not settings[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_REPLAY]:
            return
        self.startCount = 0
        callback(1.0, self.treadStartBattle)

    # Aguarda a disponibilidade do veículo antes de iniciar os cálculos.
    def treadStartBattle(self):
        vehicle = BigWorld.player().getVehicleAttached()
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
            settings = settings_service.getComponentDict(battle_marks_of_excellence_settings)
            values, self.approximate = replay_calibration(
                marks_cache.values, dBid, self.name, settings[BATTLE_MARKS_OF_EXCELLENCE.REPLAY_BASE_PERCENT],
                settings[BATTLE_MARKS_OF_EXCELLENCE.REPLAY_BASE_DAMAGE], self.dateTime)
            if values is None:
                g_panel.unavailable(self.vehicleID)
                return
            self.damageRating, self.movingAvgDamage = values[2:4]

        if self.level and self.movingAvgDamage:
            keyboard.subscribe(self.keyPressed)
            self._arena = BigWorld.player().arena
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

    # Limpa o estado de marcas de excelência em batalha no fim da batalha.
    def endBattle(self):
        keyboard.unsubscribe(self.keyPressed)
        if self._arena is not None:
            self._arena.onVehicleKilled -= self.onVehicleKilled
            self._arena = None
        from driftkings.core.callbacks import callbacks
        callbacks.cancelOwner(__name__)

    # Obtém o identificador da conta usado na cache das marcas.
    @staticmethod
    def check_player_thread():
        player = BigWorld.player()
        if hasattr(player, 'databaseID'):
            return '%s' % player.databaseID
        return '%s' % player.arena.vehicles[player.playerVehicleID]['accountDBID']

    # Arredonda o dano para a apresentação dos patamares.
    @staticmethod
    def getNormalizeDigits(value):
        return ceil_damage(value)


    # Calcula os valores de referência a partir da percentagem e do dano.
    def calcStatistics(self, p, d):
        return statistics(p, d)


g_panel = BattleMarksAdapter()
battle_marks_of_excellence_settings = BattleMarksOfExcellenceSettings()
marks_cache = MarksBattleCache(battle_marks_of_excellence_settings.NAME)
marks_cache.load(quiet=False)
worker = Worker()


# Atualiza os dados de marcas após a atualização do veículo no hangar.
@override(CrewPresenter, '_CrewPresenter__updateCrewModel')
def new__updateCrewModel(func, *args):
    worker.getCurrentHangarData()
    return func(*args)


# Encaminha os eventos de batalha quando o modo permite calcular marcas.
@on_event(battleEvents.feedback)
def new_onBattleEvents(*args):
    if battle_policy.decision('battle_marks_of_excellence')[0]:
        worker.onBattleEvents(args[1])


# Encaminha as alterações de vida para o cálculo do dano observado.
@on_event(battleEvents.healthBefore)
def new_onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    worker.shots(self, newHealth, attackerID)


# Regista a vida do veículo após a criação da sua representação visual.
@override(Vehicle, 'startVisual')
def new_vehicleStartVisual(func, *args):
    func(*args)
    worker.initVehicle(args[0])


# Inicia o módulo de marcas de excelência em batalha quando a interface de batalha está disponível.
@on_event(events.PlayerAvatar.startGUI.after)
def new_startGUI(*args):
    if battle_policy.decision('battle_marks_of_excellence')[0]:
        g_panel.startBattle()
        worker.startBattle()


# Encerra o módulo de marcas de excelência em batalha quando a interface de batalha é destruída.
@on_event(events.PlayerAvatar.destroyGUI.before)
def new_destroyGUI(*args):
    try:
        worker.endBattle()
    finally:
        g_panel.stopBattle()
        worker.clearData()


# Inicializa o módulo de marcas de excelência em batalha.
def init():
    g_panel.install()


# Liberta os recursos do módulo de marcas de excelência em batalha.
def fini():
    try:
        worker.endBattle()
    finally:
        g_panel.dispose()
        worker.clearData()
