# -*- coding: utf-8 -*-
from constants import ARENA_BONUS_TYPE, SHELL_TYPES
from helpers.CallbackDelayer import CallbackDelayer
from items import vehicles
from vehicle_systems.CompoundAppearance import CompoundAppearance

from Driftkings._constants import BATTLE_STAT, GLOBAL
from Driftkings.common import getPlayer, getEntity, replaceMacros, logError, getComparisonColor
from Driftkings.core.battle_events import battleEvents
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service, affects
from Driftkings.settings.templates.battle.battle_stat import BattleStatSettings as ConfigInterface
from Driftkings.ui import g_events
from Driftkings.views.battle.battle_stat import _startFlash

g_flash = None
config = ConfigInterface()


class TanksStatistic:
    def __init__(self):
        self.base = {}
        self.reset()

    def reset(self):
        self.base.clear()
        self.__allyTanksCount = None
        self.__enemyTanksCount = None
        self.__allyTeamHP = None
        self.__enemyTeamHP = None
        self.__allyTeamOneDamage = None
        self.__enemyTeamOneDamage = None
        self.__allyTeamDPM = None
        self.__enemyTeamDPM = None
        self.__allyTeamForces = None
        self.__enemyTeamForces = None
        self.__enemyChance = None
        self.__allyChance = None

    @property
    def allyChance(self):
        return self.__allyChance

    @property
    def enemyChance(self):
        return self.__enemyChance

    @property
    def allyTanksCount(self):
        return self.__allyTanksCount

    @property
    def enemyTanksCount(self):
        return self.__enemyTanksCount

    @property
    def allyTeamHP(self):
        return self.__allyTeamHP

    @property
    def enemyTeamHP(self):
        return self.__enemyTeamHP

    @property
    def allyTeamOneDamage(self):
        return self.__allyTeamOneDamage

    @property
    def enemyTeamOneDamage(self):
        return self.__enemyTeamOneDamage

    @property
    def allyTeamDPM(self):
        return self.__allyTeamDPM

    @property
    def enemyTeamDPM(self):
        return self.__enemyTeamDPM

    @property
    def allyTeamForces(self):
        return self.__allyTeamForces

    @property
    def enemyTeamForces(self):
        return self.__enemyTeamForces

    def _get_team_count(self, is_enemy, with_dead=False):
        return sum(1 for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_hp(self, is_enemy, with_dead=False):
        return sum(value['hp'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_damage(self, is_enemy, with_dead=False):
        return sum(value['gun']['currentDamage'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_dpm(self, is_enemy, with_dead=False):
        return sum(value['gun']['currentDpm'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def _get_team_forces(self, is_enemy, with_dead=False):
        return sum(value['force'] for value in self.base.values() if value['isEnemy'] == is_enemy and (with_dead or value['isAlive']))

    def __getAllyTanksCount(self, with_dead=False):
        return self._get_team_count(False, with_dead)

    def __getEnemyTanksCount(self, with_dead=False):
        return self._get_team_count(True, with_dead)

    def __getAllyTeamHP(self, with_dead=False):
        return self._get_team_hp(False, with_dead)

    def __getEnemyTeamHP(self, with_dead=False):
        return self._get_team_hp(True, with_dead)

    def __getAllyTeamOneDamage(self, with_dead=False):
        return self._get_team_damage(False, with_dead)

    def __getEnemyTeamOneDamage(self, with_dead=False):
        return self._get_team_damage(True, with_dead)

    def __getAllyTeamDPM(self, with_dead=False):
        return self._get_team_dpm(False, with_dead)

    def __getEnemyTeamDPM(self, with_dead=False):
        return self._get_team_dpm(True, with_dead)

    def __getAllyTeamForces(self, with_dead=False):
        return self._get_team_forces(False, with_dead)

    def __getEnemyTeamForces(self, with_dead=False):
        return self._get_team_forces(True, with_dead)

    def addVehicleInfo(self, vehicle_id, vehicle_info):
        player = getPlayer()
        if not vehicle_info or vehicle_info.get('vehicleType') is None or player is None:
            return False
        if vehicle_id not in self.base:
            v_type = vehicle_info['vehicleType']
            # Publish only complete records; a failed descriptor must not poison
            # the cache and prevent a later appearance from retrying this tank.
            tank = {}
            tank['accountDBID'] = vehicle_info['accountDBID']
            tank['userName'] = vehicle_info['name']
            tank['tank_id'] = v_type.type.compactDescr
            tank['name'] = v_type.type.shortUserString.replace(' ', '')
            tank['type'] = {'tag': set(vehicles.VEHICLE_CLASS_TAGS & v_type.type.tags).pop()}
            tank['isEnemy'] = vehicle_info['team'] != player.team
            tank['isAlive'] = vehicle_info['isAlive']
            tank['level'] = v_type.level
            tank['hpMax'] = v_type.maxHealth
            tank['hp'] = v_type.maxHealth if tank['isAlive'] else 0
            tank['gun'] = {'reload': float(v_type.gun.reloadTime)}
            if v_type.gun.clip[0] > 1:
                tank['gun']['ammer'] = {'reload': tank['gun']['reload'], 'capacity': v_type.gun.clip[0], 'shellReload': float(v_type.gun.clip[1])}
                tank['gun']['reload'] = (tank['gun']['ammer']['shellReload'] + tank['gun']['ammer']['reload'] / tank['gun']['ammer']['capacity'])
            tank['gun']['shell'] = {'AP': {'damage': 0, 'dpm': 0}, 'APRC': {'damage': 0, 'dpm': 0}, 'HC': {'damage': 0, 'dpm': 0}, 'HE': {'damage': 0, 'dpm': 0}}
            for shot in v_type.gun.shots:
                shell_type = self._getShellType(shot.shell.kind)
                damage = self._getShellDamage(shot.shell)
                if damage > tank['gun']['shell'][shell_type]['damage']:
                    damage_factor = 0.5 if shell_type == 'HE' else 1.0
                    tank['gun']['shell'][shell_type]['damage'] = damage * damage_factor
                    tank['gun']['shell'][shell_type]['dpm'] = damage * 60 / tank['gun']['reload']
            if 'SPG' == tank['type']['tag']:
                shell = 'HE'
            else:
                shell = self._getBestShellType(tank['gun']['shell'])
            tank['gun']['currentShell'] = shell
            tank['gun']['currentDamage'] = tank['gun']['shell'][shell]['damage']
            tank['gun']['currentDpm'] = tank['gun']['shell'][shell]['dpm']
            self.base[vehicle_id] = tank
            self.update(0, vehicle_id)
            return True
        return False

    @staticmethod
    def _getShellType(shell_kind):
        if shell_kind == SHELL_TYPES.ARMOR_PIERCING_CR:
            return 'APRC'
        elif shell_kind == SHELL_TYPES.HOLLOW_CHARGE:
            return 'HC'
        elif shell_kind == SHELL_TYPES.HIGH_EXPLOSIVE:
            return 'HE'
        else:
            return 'AP'

    @staticmethod
    def _getShellDamage(shell):
        damage = shell.armorDamage[0] if hasattr(shell, 'armorDamage') else shell.damage[0]
        return float(damage)

    @staticmethod
    def _getBestShellType(shell_data):
        if shell_data['AP']['damage'] > 0:
            return 'AP'
        elif shell_data['APRC']['damage'] > 0:
            return 'APRC'
        elif shell_data['HC']['damage'] > 0:
            return 'HC'
        else:
            return 'HE'

    def update(self, reason, vehicleID):
        if not self.base:
            return
        if reason <= 2:
            self.__allyTeamHP = self.__getAllyTeamHP()
            self.__enemyTeamHP = self.__getEnemyTeamHP()
        if reason <= 1:
            self.__allyTanksCount = self.__getAllyTanksCount()
            self.__enemyTanksCount = self.__getEnemyTanksCount()
            self.__allyTeamOneDamage = self.__getAllyTeamOneDamage()
            self.__enemyTeamOneDamage = self.__getEnemyTeamOneDamage()
            self.__allyTeamDPM = self.__getAllyTeamDPM()
            self.__enemyTeamDPM = self.__getEnemyTeamDPM()
        self._calculateForces()
        self.__allyTeamForces = self.__getAllyTeamForces()
        self.__enemyTeamForces = self.__getEnemyTeamForces()
        all_forces = self.__allyTeamForces + self.__enemyTeamForces
        if all_forces != 0:
            self.__allyChance = 100 * self.__allyTeamForces / all_forces
            self.__enemyChance = 100 * self.__enemyTeamForces / all_forces
            for value in self.base.values():
                if value['isAlive']:
                    value['contribution'] = 100 * value['force'] / all_forces
                else:
                    value['contribution'] = 0
        else:
            self.__allyChance = 0
            self.__enemyChance = 0
        self._triggerEvents(reason, vehicleID)

    def _calculateForces(self):
        for value in self.base.values():
            if value['isAlive']:
                if value['isEnemy']:
                    value['Th'] = value['hp'] / self.__allyTeamDPM if self.__allyTeamDPM > 0 else 999999.9
                    value['Te'] = self.__allyTeamHP / value['gun']['currentDpm'] if value['gun']['currentDpm'] > 0 else 999999.9
                else:
                    value['Th'] = value['hp'] / self.__enemyTeamDPM if self.__enemyTeamDPM > 0 else 999999.9
                    value['Te'] = self.__enemyTeamHP / value['gun']['currentDpm'] if value['gun']['currentDpm'] > 0 else 999999.9
                value['force'] = value['Th'] / value['Te'] if value['Te'] > 0 else 999999.9
            else:
                value['Th'] = 0
                value['Te'] = 999999.9
                value['force'] = 0

    def _triggerEvents(self, reason, vehicleID):
        g_events.onVehiclesChanged(self, reason, vehicleID)
        if reason <= 1:
            g_events.onCountChanged(self.__allyTanksCount, self.__enemyTanksCount)
        g_events.onHealthChanged(self.__allyTeamHP, self.__enemyTeamHP)
        g_events.onChanceChanged(self.__allyChance, self.__enemyChance, self.__allyTeamForces, self.__enemyTeamForces)


g_tanksStatistic = TanksStatistic()


class BattleStatDisplay(CallbackDelayer):
    def __init__(self):
        CallbackDelayer.__init__(self)
        self.macro = {}
        self.active = False
        self.inBattle = False

    def start(self):
        if self.active:
            return
        self.active = True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, BATTLE_STAT)
        for signal, handler in self.subscriptions():
            signal.connect(handler)
        battleEvents.acquire(self)

    def stop(self):
        if not self.active:
            return
        self.active = False
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        for signal, handler in self.subscriptions():
            signal.disconnect(handler)
        try:
            self.onBattleEnded()
        finally:
            battleEvents.release(self)

    def onSettingsChanged(self, component, changes):
        if affects(changes, GLOBAL.ENABLED, BATTLE_STAT.FORMAT, BATTLE_STAT.COLOR_RATING):
            self.refresh()

    def subscriptions(self):
        return ((battleEvents.started, self.onBattleStarted),
                (battleEvents.ended, self.onBattleEnded),
                (battleEvents.health, self.onHealthChanged),
                (battleEvents.appeared, self.onAppeared),
                (battleEvents.killed, self.onKilled))

    def onBattleStarted(self):
        self.onBattleEnded()
        arena = getPlayer().arena
        if arena.bonusType != ARENA_BONUS_TYPE.REGULAR:
            return
        self.inBattle = True
        for vehicleID, info in arena.vehicles.items():
            g_tanksStatistic.addVehicleInfo(vehicleID, info)
        self.refresh()

    def onBattleEnded(self):
        self.inBattle = False
        self.clearCallbacks()
        self.macro.clear()
        g_tanksStatistic.reset()
        if g_flash is not None:
            g_flash.setVisible(False)

    def refresh(self):
        self.clearCallbacks()
        if g_flash is not None:
            g_flash.setVisible(False)
        if g_tanksStatistic.base:
            self.flash_text()

    def onHealthChanged(self, vehicleID, health):
        if not self.inBattle:
            return
        if vehicleID not in g_tanksStatistic.base:
            player = getPlayer()
            arena = getattr(player, 'arena', None)
            info = arena.vehicles.get(vehicleID) if arena is not None else None
            if g_tanksStatistic.addVehicleInfo(vehicleID, info):
                self.refresh()
        tank = g_tanksStatistic.base.get(vehicleID)
        health = max(0, health)
        if tank is not None and (tank['hp'] != health or tank['isAlive'] != (health > 0)):
            alive = health > 0
            reason = 1 if tank['isAlive'] != alive else 2
            tank.update(hp=health, isAlive=alive)
            g_tanksStatistic.update(reason, vehicleID)

    def onAppeared(self, vehicleID):
        if self.inBattle:
            entity = getEntity(vehicleID)
            if entity is not None:
                self.onHealthChanged(vehicleID, entity.health)

    def onKilled(self, vehicleID):
        self.onHealthChanged(vehicleID, 0)

    @staticmethod
    def compare_sign(ally, enemy):
        if ally < enemy:
            return '&#x003C;'
        elif ally > enemy:
            return '&#x003E;'
        return '&#x007C;'

    def flash_text(self):
        if not self.inBattle or not settings_service.getComponentDict(config).get(GLOBAL.ENABLED, False) or g_flash is None:
            return
        g_flash.setVisible(True)
        ally = g_tanksStatistic.allyChance
        enemy = g_tanksStatistic.enemyChance
        ally_text = self.formatChanceText(ally, enemy)
        enemy_text = self.formatChanceText(enemy, ally)
        text = self.formatText(ally_text, enemy_text, ally, enemy)
        data = g_flash.getSimpleTextWithTags(text)
        g_flash.HtmlText(data)
        self.delayCallback(0.3, self.flash_text)

    def formatChanceText(self, value, comparison_value):
        color = getComparisonColor(value, comparison_value, settings_service.getComponentDict(config).get(BATTLE_STAT.COLOR_RATING, 0))
        return g_flash.getHtmlTextWithTags('%6.2f' % value, color=color)

    def updateMacros(self, data):
        for key, value in data.items():
            self.macro['{%s}' % key] = str(value)

    def formatText(self, ally_text, enemy_text, ally, enemy):
        data = {'header': 'Chances', 'allyChance': ally_text, 'enemyChance': enemy_text, 'compareSign': self.compare_sign(ally, enemy)}
        self.updateMacros(data)
        return replaceMacros(settings_service.getComponentDict(config)[BATTLE_STAT.FORMAT], self.macro)


g_mod = BattleStatDisplay()


# CompoundAppearance remains a feature-specific hook; common events belong to Core.
@override(CompoundAppearance, 'prerequisites')
def new__prerequisites(func, self, typeDescriptor, vehicleID, *args, **kwargs):
    result = func(self, typeDescriptor, vehicleID, *args, **kwargs)
    if g_mod.inBattle:
        try:
            player = getPlayer()
            arena = getattr(player, 'arena', None)
            info = arena.vehicles.get(vehicleID) if arena is not None else None
            if g_tanksStatistic.addVehicleInfo(vehicleID, info):
                g_mod.refresh()
        except Exception as error:
            logError(config.ID, '{}', error)
    return result


def init():
    _startFlash()
    g_mod.start()


def fini():
    global g_flash
    g_mod.stop()
    if g_flash is not None:
        g_flash.destroy()
        g_flash = None
