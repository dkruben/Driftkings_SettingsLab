# -*- coding: utf-8 -*-
import math

from constants import ARENA_GUI_TYPE
from gui.battle_control.arena_info import vos_collections
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID

from driftkings._constants import GLOBAL, HIGH_CALIBER_PROGRESS
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.battle_events import battleEvents
from driftkings.core.battle_policy import battle_policy
from driftkings.core.high_caliber import project
from driftkings.core.hooks import on_event
from driftkings.settings.definitions.battle.high_caliber_progress import HighCaliberProgressSettings as Settings
from driftkings.settings.service import settings_service
from driftkings.gameface.battle.high_caliber_gameface import MainGunAdapter

# RANDOM_NP2 battles use the RANDOM GUI; WINBACK has its own.
RANDOM_GUI_TYPES = tuple(getattr(ARENA_GUI_TYPE, name) for name in ('RANDOM', 'EPIC_RANDOM', 'WINBACK') if hasattr(ARENA_GUI_TYPE, name))

g_gameface = None
config = Settings()


class MainGun(object):
    def __init__(self):
        self.players_damage = dict()
        self.totals = [0, 0, True, 0, 0]
        self.payload = {'visible': False}
        self.destroyed = False

    @property
    def showMainGun(self):
        return settings_service.getComponentDict(config)[HIGH_CALIBER_PROGRESS.HIGH_CALIBER_PROGRESS]['enabled'] and scl.guiType in RANDOM_GUI_TYPES

    def battleLoading(self):
        enemy_health = scl.health.get(scl.enemyTeam)
        if self.showMainGun and enemy_health and enemy_health[1]:
            self.totals[0] = max(1000, int(math.ceil(scl.health[scl.enemyTeam][1] * 0.2)))
        self.updateMainGun()

    def playersDamage(self, attackerID, damage, targetTeam, attackerTeam):
        if attackerID is None or damage <= 0:
            self.updateMainGun()
            return
        p_damage = self.players_damage.setdefault(attackerID, [0, False])
        if targetTeam == attackerTeam:
            p_damage[1] = True
            if attackerID != scl.playerID:
                self.totals[3] = max([0] + [value[0] for key, value in self.players_damage.items()
                                          if key != scl.playerID and not value[1]])
        else:
            p_damage[0] += damage
            if attackerID != scl.playerID and not p_damage[1]:
                self.totals[3] = max(self.totals[3], p_damage[0])
        self.updateMainGun()

    def onPlayerFeedbackReceived(self, events):
        for event in events:
            eventType = event.getType()
            extra = event.getExtra()
            if eventType == FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY and extra is not None:
                damage = extra.getDamage()
                self.totals[4] += damage
                self.updateMainGun()

    def updateMainGun(self):
        settings = settings_service.getComponentDict(config)
        player = getPlayer()
        visible = bool(scl.inBattle and settings[GLOBAL.ENABLED] and player and player.arena
                       and battle_policy.decision('high_caliber_progress')[0]
                       and self.showMainGun and self.totals[0])
        self.payload = {'visible': False}
        if visible:
            options = settings[HIGH_CALIBER_PROGRESS.HIGH_CALIBER_PROGRESS]
            health = scl.health.get(scl.enemyTeam)
            # Health events and ribbons can arrive in either order. Account for
            # observed own damage before feedback credits it, without double counting.
            own = self.players_damage.get(scl.playerID, [0, False])
            pending = max(0, own[0] - self.totals[4])
            self.payload = project(self.totals[0], self.totals[3], self.totals[4],
                                   options['dynamic'], own[1], not self.destroyed,
                                   health[0] + pending if health is not None else None)
            self.payload['visible'] = True
            self.totals[1] = self.payload['remaining']
            self.totals[2] = self.payload['state'] != 'unavailable'
        if g_gameface is not None:
            g_gameface.refresh()


class SysClass(object):
    def __init__(self):
        self.active = False
        self.inBattle = False
        self.player = None
        self.arena = None
        self.feedback = None
        self.reset()

    def reset(self):
        self.health = dict()
        self.vehicles = dict()
        self.guiType = 0
        self.playerID = None
        self.enemyTeam = None
        self._health = [0, 0, 0, 0]

    def start(self):
        if self.active:
            return
        self.active = True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, HIGH_CALIBER_PROGRESS)
        battleEvents.started.connect(self.battleLoading)
        battleEvents.loaded.connect(self.onRosterReady)
        battleEvents.ended.connect(self.destroyBattle)
        battleEvents.killed.connect(self._onVehicleKilled)
        battleEvents.acquire(self)

    def stop(self):
        if not self.active:
            return
        self.active = False
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        battleEvents.started.disconnect(self.battleLoading)
        battleEvents.loaded.disconnect(self.onRosterReady)
        battleEvents.ended.disconnect(self.destroyBattle)
        battleEvents.killed.disconnect(self._onVehicleKilled)
        try:
            self.destroyBattle()
        finally:
            battleEvents.release(self)

    def onSettingsChanged(self, component, changes):
        self.refresh()

    def refresh(self):
        mainGuns.updateMainGun()

    def battleLoading(self):
        self.destroyBattle()
        player = getPlayer()
        # Match MarksOnGunBattle and BattleEfficiency: statistics-bearing
        # battles only (random, incl. RANDOM_NP2/WINBACK), before subscribing to damage/roster events.
        if not player or not player.arena or not battle_policy.decision('high_caliber_progress')[0]:
            return
        arena_dp = player.guiSessionProvider.getArenaDP()
        enemy_teams = arena_dp.getEnemyTeams() if arena_dp else ()
        self.guiType = player.arena.guiType
        self.playerID = player.playerVehicleID
        self.enemyTeam = enemy_teams[0] if enemy_teams else None
        self.player = player
        self.arena = player.arena
        self.inBattle = True
        player.onVehicleEnterWorld += self._onEnterWorld
        player.arena.onVehicleAdded += self._onVehicleUpdate
        player.arena.onVehicleUpdated += self._onVehicleUpdate
        # Native player feedback: damage dealt arrives here whatever the ribbons settings are.
        feedback = player.guiSessionProvider.shared.feedback
        if feedback is not None:
            feedback.onPlayerFeedbackReceived += self._onPlayerFeedbackReceived
            self.feedback = feedback
        self.onRosterReady()

    def _onPlayerFeedbackReceived(self, events):
        if self.inBattle:
            mainGuns.onPlayerFeedbackReceived(events)

    def onRosterReady(self, *args):
        if not self.inBattle:
            return
        self.tanklistsCreate()
        mainGuns.battleLoading()

    def destroyBattle(self):
        self.inBattle = False
        if self.player is not None:
            self.player.onVehicleEnterWorld -= self._onEnterWorld
            self.player = None
        if self.arena is not None:
            self.arena.onVehicleAdded -= self._onVehicleUpdate
            self.arena.onVehicleUpdated -= self._onVehicleUpdate
            self.arena = None
        if self.feedback is not None:
            self.feedback.onPlayerFeedbackReceived -= self._onPlayerFeedbackReceived
            self.feedback = None
        self.reset()
        mainGuns.__init__()
        mainGuns.updateMainGun()

    def tanklistsCreate(self):
        arena_dp = self.player.guiSessionProvider.getArenaDP()
        if arena_dp is None:
            return
        enemy_teams = arena_dp.getEnemyTeams()
        if enemy_teams:
            self.enemyTeam = enemy_teams[0]
        collection = vos_collections.VehiclesInfoCollection().iterator(arena_dp)
        for vInfoVO in collection:
            if not vInfoVO or not vInfoVO.vehicleType or not vInfoVO.vehicleType.classTag:
                continue
            maxHealth = vInfoVO.vehicleType.maxHealth
            if not maxHealth:
                continue
            if vInfoVO.vehicleID in self.vehicles:
                continue
            health = maxHealth if vInfoVO.isAlive() else 0
            self.vehicles.setdefault(vInfoVO.vehicleID, [health, maxHealth, vInfoVO.team, vInfoVO.vehicleType.classTag])
            if vInfoVO.team == getPlayer().team:
                self._health[1] += health
                self._health[3] += health
            else:
                if self.enemyTeam is None:
                    self.enemyTeam = vInfoVO.team
                self._health[0] += health
                self._health[2] += health

            hDic = self.health.setdefault(vInfoVO.team, [0, 0])
            hDic[0] += health
            hDic[1] += maxHealth

    def updateHealthPoints(self, damage, team):
        if damage <= 0 or team not in self.health:
            return
        self.health[team][0] -= damage
        if self.health[team][0] < 0:
            self.health[team][0] = 0
        index = 1 if team == getPlayer().team else 0
        self._health[index] -= damage
        if self._health[index] <= 0:
            self._health[index] = 0

    def onHealthChanged(self, vehicle, newHealth, _, attackerID, __):
        if self.guiType in RANDOM_GUI_TYPES:
            target = self.vehicles.get(vehicle.id)
            attacker = self.vehicles.get(attackerID)
            if target and target[0] > 0:
                newHealth = max(0, newHealth)
                damage = target[0] - newHealth
                if damage <= 0:
                    return
                target[0] = newHealth
                self.updateHealthPoints(damage, target[2])
                mainGuns.playersDamage(attackerID, damage, target[2], attacker[2] if attacker else None)

    def _onVehicleKilled(self, targetID, *_, **__):
        if not self.inBattle:
            return
        target = self.vehicles.get(targetID)
        if target and target[0] > 0:
            self.updateHealthPoints(target[0], target[2])
            target[0] = 0
        if self.playerID == targetID:
            mainGuns.destroyed = True
        mainGuns.updateMainGun()

    def _onVehicleUpdate(self, tid):
        if not self.inBattle:
            return
        arena_dp = self.player.guiSessionProvider.getArenaDP()
        if arena_dp is None:
            return
        vInfoVO = arena_dp.getVehicleInfo(tid)
        if not vInfoVO or not vInfoVO.vehicleType or not vInfoVO.vehicleType.classTag:
            return
        maxHealth = vInfoVO.vehicleType.maxHealth
        if not maxHealth:
            return
        if tid in self.vehicles:
            return None
        health = maxHealth if vInfoVO.isAlive() else 0
        self.vehicles.setdefault(tid, [health, maxHealth, vInfoVO.team, vInfoVO.vehicleType.classTag])
        if vInfoVO.team == getPlayer().team:
            self._health[1] += health
        else:
            if self.enemyTeam is None:
                self.enemyTeam = vInfoVO.team
            self._health[0] += health
        hDic = self.health.setdefault(vInfoVO.team, [0, 0])
        hDic[0] += health
        hDic[1] += maxHealth
        # Vehicles can arrive after startGUI. Recompute the target and publish
        # once their maximum HP is known, without resetting accumulated damage.
        mainGuns.battleLoading()

    def _onEnterWorld(self, vehicle):
        target = self.vehicles.get(vehicle.id)
        newHealth = max(0, vehicle.health)
        if target and target[0] != newHealth and vehicle.isAlive():
            self.updateHealthPoints(max(target[0] - newHealth, 0), target[2])
            target[0] = newHealth
            mainGuns.updateMainGun()


@on_event(battleEvents.healthDetailed)
def new__onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    if scl.inBattle:
        scl.onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID)


# Initialize the mod
mainGuns = MainGun()
scl = SysClass()


def init():
    global g_gameface
    if g_gameface is None:
        g_gameface = MainGunAdapter()
        g_gameface.install()
    scl.start()


def fini():
    global g_gameface
    scl.stop()
    if g_gameface is not None:
        g_gameface.dispose()
        g_gameface = None
