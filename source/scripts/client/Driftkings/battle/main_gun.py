# -*- coding: utf-8 -*-
import math

from Vehicle import Vehicle
from constants import ARENA_BONUS_TYPE
from constants import ARENA_GUI_TYPE
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.battle_control.arena_info import vos_collections
from gui.battle_control.battle_constants import FEEDBACK_EVENT_ID

from Driftkings._constants import GLOBAL, MAIN_GUN
from Driftkings.common import getPlayer
from Driftkings.core.battle_events import battleEvents
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service, affects
from Driftkings.settings.templates.battle.main_gun import MainGunSettings as ConfigInterface
from Driftkings.views.battle.main_gun import _startFlash

g_flash = None
config = ConfigInterface()


class MainGun(object):
    def __init__(self):
        self.players_damage = dict()
        self.mainGunText = ''
        self.totals = [0, 0, True, 0, 0]

    @property
    def showMainGun(self):
        return settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['enabled'] and '{mainGun}' in settings_service.getComponentDict(config)[MAIN_GUN.FORMAT] and scl.guiType in (ARENA_GUI_TYPE.RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM)

    def battleLoading(self):
        enemy_health = scl.health.get(scl.enemyTeam)
        if self.showMainGun and enemy_health and enemy_health[1]:
            self.totals[0] = max(1000, int(math.ceil(scl.health[scl.enemyTeam][1] * 0.2)))
        self.updateMainGun()

    def playersDamage(self, attackerID, damage, targetTeam, attackerTeam):
        if attackerID is None or damage <= 0:
            return
        p_damage = self.players_damage.setdefault(attackerID, [0, False])
        if targetTeam == attackerTeam:
            p_damage[1] = True
        else:
            p_damage[0] += damage
            if self.showMainGun and settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['dynamic']:
                player_damage = self.players_damage.setdefault(scl.playerID, [0, False])
                if attackerID != scl.playerID and p_damage[0] > self.totals[3] and not p_damage[1]:
                    if p_damage[0] > self.totals[0] and p_damage[0] > player_damage[0]:
                        self.totals[3] = p_damage[0]
                        self.totals[2] = False
                        self.updateMainGun()
                if player_damage[1]:
                    self.totals[2] = False
                    self.updateMainGun()

    def onPlayerFeedbackReceived(self, events):
        for event in events:
            eventType = event.getType()
            extra = event.getExtra()
            if eventType == FEEDBACK_EVENT_ID.PLAYER_DAMAGED_HP_ENEMY and extra is not None:
                damage = extra.getDamage()
                self.totals[4] += damage
                if settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['dynamic']:
                    self.updateMainGun()

    @staticmethod
    def recipes(value):
        return '{:,}'.format(int(value)).replace(',', ' ')

    def updateMainGun(self):
        if not scl.inBattle or not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            if g_flash is not None: g_flash.hide()
            return
        player = getPlayer()
        if not player or not player.arena or player.arena.bonusType != ARENA_BONUS_TYPE.REGULAR or not self.showMainGun or not self.totals[0]:
            if g_flash is not None: g_flash.hide()
            return
        macros = {
            'mainGun': 0,
            'mainGunIcon': settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['mainGunIcon'],
            'mainGunDoneIcon': '',
            'mainGunFailureIcon': settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['mainGunFailureIcon']
        }
        if self.showMainGun:
            dynamic = settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['dynamic']
            if dynamic:
                if self.totals[3] and self.totals[4] > self.totals[3]:
                    self.totals[3] = self.totals[4]
                    self.totals[2] = True
                self.totals[1] = max(max(self.totals[0], self.totals[3]) - self.totals[4], 0)
            mainGunAchived = dynamic and not self.totals[1] and self.totals[2]
            if mainGunAchived:
                macros['mainGun'] = ''
            elif not self.totals[2] and dynamic:
                macros['mainGun'] = ''
            else:
                macros['mainGun'] = self.recipes(self.totals[int(dynamic)])
            macros['mainGunDoneIcon'] = settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['mainGunDoneIcon'] if mainGunAchived else ''
            macros['mainGunFailureIcon'] = settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['mainGunFailureIcon'] if not self.totals[2] and dynamic else ''
        self.mainGunText = settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['format'].format(**macros)
        if g_flash is not None:
            g_flash.addText(settings_service.getComponentDict(config)[MAIN_GUN.FORMAT].format(mainGun=self.mainGunText))


class SysClass(object):
    def __init__(self):
        self.active = False
        self.inBattle = False
        self.player = None
        self.arena = None
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
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, MAIN_GUN)
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
        if affects(changes, GLOBAL.ENABLED, MAIN_GUN.FORMAT, MAIN_GUN.MAIN_GUN):
            self.refresh()

    def refresh(self):
        if g_flash is not None:
            g_flash.hide()
        if self.inBattle and settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            mainGuns.updateMainGun()

    def battleLoading(self):
        self.destroyBattle()
        player = getPlayer()
        # Match MarksOnGunBattle and BattleEfficiency: statistics-bearing
        # regular battles only, before subscribing to damage/roster events.
        if not player or not player.arena or player.arena.bonusType != ARENA_BONUS_TYPE.REGULAR:
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
        self.onRosterReady()

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
        self.reset()
        mainGuns.__init__()
        if g_flash is not None:
            g_flash.hide()

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
        health = self.health[team][0]
        index = 1 if team == getPlayer().team else 0
        self._health[index] -= damage
        if self._health[index] <= 0:
            self._health[index] = 0
        if mainGuns.showMainGun and settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['dynamic'] and team == self.enemyTeam:
            if health and mainGuns.totals[2] and mainGuns.totals[1] and health < mainGuns.totals[1]:
                mainGuns.totals[2] = False
                mainGuns.updateMainGun()

    def onHealthChanged(self, vehicle, newHealth, _, attackerID, __):
        if self.guiType in [ARENA_GUI_TYPE.RANDOM, ARENA_GUI_TYPE.EPIC_RANDOM]:
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
        if self.playerID == targetID and mainGuns.showMainGun and settings_service.getComponentDict(config)[MAIN_GUN.MAIN_GUN]['dynamic'] and mainGuns.totals[1]:
            mainGuns.totals[2] = False
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


@override(RibbonsAggregator, '_onPlayerFeedbackReceived')
def new__onPlayerFeedbackReceived(func, self, events):
    result = func(self, events)
    if scl.inBattle:
        mainGuns.onPlayerFeedbackReceived(events)
    return result


@override(Vehicle, 'onHealthChanged')
def new__onHealthChanged(func, self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs):
    result = func(self, newHealth, oldHealth, attackerID, attackReasonID, *args, **kwargs)
    if scl.inBattle:
        scl.onHealthChanged(self, newHealth, oldHealth, attackerID, attackReasonID)
    return result


# Initialize the mod
mainGuns = MainGun()
scl = SysClass()


def init():
    _startFlash()
    scl.start()


def fini():
    global g_flash
    scl.stop()
    if g_flash is not None:
        g_flash.destroy()
        g_flash = None
