# -*- coding: utf-8 -*-
import math

import BigWorld
import CommandMapping
import Math
from Avatar import PlayerAvatar
from AvatarInputHandler import cameras
from AvatarInputHandler.control_modes import SniperControlMode, StrategicControlMode, ArcadeControlMode, ArtyControlMode
from gui.shared.personality import ServicesLocator

from Driftkings._constants import AUTO_AIM_OPTIMIZE, GLOBAL
from Driftkings.common import getEntity
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.auto_aim import AutoAimOptimizeSettings as Settings


class AutoAimController(object):
    def __init__(self, config):
        self.config = config
        self.lockRequest = False
        self.lockRelease = False
        self.optimizedTargetID = None


    def findTarget(self, player):
        if player.isObserver() or getattr(player, 'arena', None) is None:
            return
        ownVehicle = player.getVehicleAttached()
        if ownVehicle is None or not ownVehicle.isAlive():
            return
        angle = math.radians(settings_service.getComponentDict(self.config)[AUTO_AIM_OPTIMIZE.ANGLE])
        cameraDir, cameraPos = cameras.getWorldRayAndPoint(0, 0)
        cameraDir.normalise()
        result = None
        best = None
        for vId, vData in player.arena.vehicles.iteritems():
            if vData['team'] != player.team and vData['isAlive']:
                vehicle = getEntity(vId)
                if vehicle is not None and vehicle.isStarted and vehicle.isAlive():
                    # Entity position is at the tracks; aim at the hull centre.
                    descriptor = vehicle.typeDescriptor
                    bounds = descriptor.hull.hitTester.bbox
                    point = Math.Matrix(vehicle.matrix).applyPoint(
                        descriptor.chassis.hullPosition + (bounds[0] + bounds[1]) * 0.5)
                    radian = self.calc_radian(point, angle, cameraDir, cameraPos)
                    if radian is None:
                        continue
                    rank = (radian, (vehicle.position - ownVehicle.position).lengthSquared, vId)
                    if best is not None and rank >= best:
                        continue
                    if not settings_service.getComponentDict(self.config)[AUTO_AIM_OPTIMIZE.CATCH_HIDDEN_TARGET] and BigWorld.wg_collideSegment(
                            player.spaceID, cameraPos, point, 128) is not None:
                        continue
                    best, result = rank, vehicle
        return result

    @staticmethod
    def calc_radian(target_position, angle, cameraDir, cameraPos):
        cameraToTarget = target_position - cameraPos
        if cameraToTarget.lengthSquared <= 0.0:
            return
        dot = cameraToTarget.dot(cameraDir)
        if dot < 0:
            return
        cosine = dot / math.sqrt(cameraToTarget.lengthSquared)
        radian = math.acos(max(-1.0, min(1.0, cosine)))
        if radian > angle:
            return
        return radian

    def handleKey(self, original, mode, isDown, key, *args, **kwargs):
        artyMode = isinstance(mode, (StrategicControlMode, ArtyControlMode))
        enabled = (settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] and ServicesLocator.appLoader.getDefBattleApp() is not None
                   and CommandMapping.g_instance.isFired(CommandMapping.CMD_CM_LOCK_TARGET, key)
                   and not CommandMapping.g_instance.isFired(CommandMapping.CMD_CM_LOCK_TARGET_OFF, key)
                   and not (settings_service.getComponentDict(self.config)[AUTO_AIM_OPTIMIZE.DISABLE_ARTY_MODE] and artyMode))
        previous = self.lockRequest, self.lockRelease
        self.lockRequest, self.lockRelease = enabled and isDown, enabled and not isDown
        if self.lockRequest:
            self.optimizedTargetID = None
        try:
            # Preserve camera controls and the client's input restrictions.
            result = original(mode, isDown, key, *args, **kwargs)
            # Trajectory modes do not call autoAim themselves.
            if self.lockRequest and artyMode and not result:
                BigWorld.player().autoAim(BigWorld.target())
            return result
        finally:
            if self.lockRelease:
                self.optimizedTargetID = None
            self.lockRequest, self.lockRelease = previous


config = Settings()
controller = AutoAimController(config)


@override(PlayerAvatar, 'autoAim')
def new_autoAim(original, player, target=None, magnetic=False):
    currentID = player._PlayerAvatar__autoAimVehID
    if controller.lockRelease and magnetic and controller.optimizedTargetID == currentID:
        # Native magnetic aim must not toggle off the target found on key-down.
        return
    if controller.lockRequest and target is None and not currentID:
        target = controller.findTarget(player)
        result = original(player, target, magnetic)
        if target is not None and player._PlayerAvatar__autoAimVehID == target.id:
            controller.optimizedTargetID = target.id
        return result
    return original(player, target, magnetic)


@override(SniperControlMode, 'handleKeyEvent')
def new_keyEventSniper(func, *args, **kwargs):
    return controller.handleKey(func, *args, **kwargs)


@override(StrategicControlMode, 'handleKeyEvent')
def new_keyEventStrategic(func, *args, **kwargs):
    return controller.handleKey(func, *args, **kwargs)


@override(ArtyControlMode, 'handleKeyEvent')
def new_keyEventArty(func, *args, **kwargs):
    return controller.handleKey(func, *args, **kwargs)


@override(ArcadeControlMode, 'handleKeyEvent')
def new_keyEventArcade(func, *args, **kwargs):
    return controller.handleKey(func, *args, **kwargs)
