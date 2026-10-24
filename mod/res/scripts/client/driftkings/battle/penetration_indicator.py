# -*- coding: utf-8 -*-
from AvatarInputHandler.gun_marker_ctrl import _CrosshairShotResults, computePiercingPowerAtDist
from DestructibleEntity import DestructibleEntity
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.genConsts.CROSSHAIR_VIEW_ID import CROSSHAIR_VIEW_ID
from Vehicle import Vehicle

from driftkings._constants import BATTLE_ALIASES, GLOBAL, PENETRATION_INDICATOR
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.hooks import override
from driftkings.game_constants import SHELL_MECHANICS_TYPE, SHELL_TYPES
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.penetration_indicator import PenetrationIndicatorSettings as Settings
from driftkings.settings.service import settings_service
from driftkings.ui import g_events
from driftkings.views.battle.penetration_indicator import ArmorCalculator

LOG = get_logger('driftkings.battle.penetration_indicator')

AS_BATTLE = BATTLE_ALIASES.PENETRATION_INDICATOR
config = Settings()


class _ShotResult(_CrosshairShotResults):
    """Armour and penetration numbers along the shot; the marker colour comes from the client."""
    ENTITY_TYPES = (Vehicle, DestructibleEntity)
    JET_FACTOR = 0.001
    PP_REDUCTION_FACTOR = 3.0

    @classmethod
    def _isDestructibleComponent(cls, entity, componentID):
        return entity.isDestructibleComponent(componentID) if isinstance(entity, DestructibleEntity) else True

    @classmethod
    def _getShotResult(cls, gunMarker, multiplier, player):
        if player is None or gunMarker.collData is None:
            return None
        entity = gunMarker.collData.entity
        if not isinstance(entity, cls.ENTITY_TYPES) or not entity.isAlive() or entity.publicInfo['team'] == player.team:
            return None
        return cls._result(gunMarker, multiplier, player)

    @classmethod
    def _result(cls, gunMarker, multiplier, player):
        collision_details = cls._getAllCollisionDetails(gunMarker.position, gunMarker.direction, gunMarker.collData.entity)
        if collision_details is None:
            return None
        vDesc = player.getVehicleDescriptor()
        gunInstallationSlot = vDesc.gunInstallations[gunMarker.gunInstallationIndex]
        shot = vDesc.shot if gunInstallationSlot.isMainInstallation() else gunInstallationSlot.gun.shots[0]
        shell = shot.shell
        distance = player.position.flatDistTo(gunMarker.position)
        piercing_power = computePiercingPowerAtDist(shot.piercingPower, distance, shot.maxDistance, multiplier)
        if cls._isModernMechanics(shell):
            return cls._computeArmorModernHE(collision_details, shell, piercing_power, gunMarker.collData.entity)
        else:
            return cls._computeArmorDefault(collision_details, shell, piercing_power, gunMarker.collData.entity)

    @staticmethod
    def _isModernMechanics(shell):
        return shell.kind == SHELL_TYPES.HIGH_EXPLOSIVE and shell.type.mechanics == SHELL_MECHANICS_TYPE.MODERN

    @classmethod
    def _computeArmorDefault(cls, collision_details, shell, full_piercing_power, entity):
        armor = 0
        piercing_power = full_piercing_power
        ignored_materials = set()
        isJet = False
        jet_loss = shell.type.piercingPowerLossFactorByDistance if cls._SHELL_EXTRA_DATA[shell.kind].hasPenetrationLoss else 0.0
        jet_start_dist = 0.0
        no_damage = True
        ricochet = False

        for detail in collision_details:
            if not cls._isDestructibleComponent(entity, detail.compName):
                continue
            mat_info = detail.matInfo
            if not mat_info or (detail.compName, mat_info.kind) in ignored_materials:
                continue
            hitAngleCos = detail.hitAngleCos if mat_info.useHitAngle else 1.0
            if isJet:
                jetDist = detail.dist - jet_start_dist
                if jetDist > 0.0:
                    piercing_power *= 1.0 - jetDist * jet_loss
            else:
                ricochet = cls._shouldRicochet(shell, hitAngleCos, mat_info)
                if ricochet:
                    break
            armor += cls._computePenetrationArmor(shell, hitAngleCos, mat_info)
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            if jet_loss > 0.0:
                isJet = True
                jet_start_dist = detail.dist + mat_info.armor * cls.JET_FACTOR
            if mat_info.collideOnceOnly:
                ignored_materials.add((detail.compName, mat_info.kind))
        return int(armor), int(piercing_power), int(shell.caliber), ricochet, no_damage

    @classmethod
    def _computeArmorModernHE(cls, collision_details, shell, piercing_power, entity):
        armor = 0
        ignored_materials = set()
        no_damage = True

        for detail in collision_details:
            if not cls._isDestructibleComponent(entity, detail.compName):
                continue
            mat_info = detail.matInfo
            if not mat_info or (detail.compName, mat_info.kind) in ignored_materials:
                continue
            hitAngleCos = detail.hitAngleCos if mat_info.useHitAngle else 1.0
            plate_armor = cls._computePenetrationArmor(shell, hitAngleCos, mat_info)
            armor += plate_armor
            if mat_info.vehicleDamageFactor:
                no_damage = False
                break
            if shell.type.shieldPenetration:
                # Each shield reduces the power by its own armour, as in the client.
                piercing_power = max(0, piercing_power - plate_armor * cls.PP_REDUCTION_FACTOR)
            if mat_info.collideOnceOnly:
                ignored_materials.add((detail.compName, mat_info.kind))
        return int(armor), int(piercing_power), int(shell.caliber), False, no_damage


class _ShotResultAll(_ShotResult):

    @classmethod
    def _getShotResult(cls, gunMarker, multiplier, player):
        collision = gunMarker.collData
        if player is None or collision is None or not isinstance(collision.entity, cls.ENTITY_TYPES) or not collision.entity.isAlive():
            return None
        return cls._result(gunMarker, multiplier, player)


class ShotResultIndicatorPlugin(plugins.ShotResultIndicatorPlugin):

    def __init__(self, parentObj):
        super(ShotResultIndicatorPlugin, self).__init__(parentObj)
        self.__player = getPlayer()
        self.__data = None
        self.__resolver = _ShotResultAll if settings_service.getComponentDict(config)[PENETRATION_INDICATOR.DISPLAY_ON_ALLIES] else _ShotResult

    def _getShotResolverResult(self, gunMarker):
        # The client's own resolver decides the colour; allies are included when the option asks for it.
        team = 0 if self.__resolver is _ShotResultAll else self.__playerTeam
        return self.__shotResultResolver.getShotResult(gunMarker, team, self.__piercingMultiplier)

    def __onGunMarkerStateChanged(self, markerType, gunMarkerState, supportMarkersInfo):
        if not self.__isEnabled:
            return
        shot_result = self._getShotResult(gunMarkerState, supportMarkersInfo)
        data = self.__resolver._getShotResult(gunMarkerState, self.__piercingMultiplier, self.__player)
        if shot_result in self.__colors:
            color = self.__colors[shot_result]
            if self.__cache[markerType] != shot_result and self._parentObj.setGunMarkerColor(markerType, color):
                self.__cache[markerType] = shot_result
                g_events.onMarkerColorChanged(color)
            if self.__data != data:
                self.__data = data
                g_events.onArmorChanged(data)

    def __setMapping(self, keys):
        super(ShotResultIndicatorPlugin, self).__setMapping(keys)
        self.__mapping[CROSSHAIR_VIEW_ID.STRATEGIC] = True

    def start(self):
        super(ShotResultIndicatorPlugin, self).start()
        self.__player = getPlayer()


@override(plugins, 'createPlugins')
def createPlugins(func, *args):
    _plugins = func(*args)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        _plugins['shotResultIndicator'] = ShotResultIndicatorPlugin
    return _plugins


def getBattleViews():
    return ((AS_BATTLE, ArmorCalculator, config),)
