# -*- coding: utf-8 -*-
import math

import CommandMapping
import VehicleGunRotator
import gun_rotation_shared
from Avatar import PlayerAvatar, MOVEMENT_FLAGS, _CRUISE_CONTROL_MODE
from AvatarInputHandler.player_notifications.siege_mode.sound_notifications import SoundNotifications
from constants import VEHICLE_SETTING, VEHICLE_SIEGE_STATE
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE

from Driftkings._constants import GLOBAL, SERVER_TURRET_EXTENDED
from Driftkings.common import checkKeys, getPlayer, sendPanelMessage, serverTime
from Driftkings.core.callbacks import callback, cancelCallback
from Driftkings.core.hooks import override
from Driftkings.core.keyboard import keyboard
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.server_turret import ServerTurretExtendedSettings as ConfigInterface


class MovementControl(object):
    timer = None
    callback = None

    @staticmethod
    def move_pressed(avatar, is_down, key):
        if CommandMapping.g_instance.isFiredList((CommandMapping.CMD_MOVE_FORWARD, CommandMapping.CMD_MOVE_FORWARD_SPEC, CommandMapping.CMD_MOVE_BACKWARD, CommandMapping.CMD_ROTATE_LEFT, CommandMapping.CMD_ROTATE_RIGHT), key):
            avatar.moveVehicle(0, is_down)

    def start_battle(self):
        keyboard.subscribe(self.keyPressed)
        self.timer = serverTime()
        SoundNotifications.TRANSITION_TIMER = 'siege_mode_transition_timer'
        if self.callback is None:
            self.callback = callback(0.1, self.onCallback)

    def endBattle(self):
        if self.callback is not None:
            cancelCallback(self.callback)
            self.callback = None
        keyboard.unsubscribe(self.keyPressed)

    def onCallback(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.AUTO_ACTIVATE_WHEEL_MODE]:
            self.changeMovement()
        self.callback = callback(0.1, self.onCallback)

    @staticmethod
    def getStatusText(enabled):
        return config.i18n['UI_battle_ON'] if enabled else config.i18n['UI_battle_OFF']

    @staticmethod
    def keyPressed(event):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        vehicle = getPlayer().getVehicleAttached()
        if not (vehicle and vehicle.isAlive() and vehicle.isWheeledTech and vehicle.typeDescriptor.hasSiegeMode):
            return
        if checkKeys(settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.BUTTON_MAX_MODE]) and event.isKeyDown():
            settings_service.apply(config, {SERVER_TURRET_EXTENDED.MAX_WHEEL_MODE: not settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.MAX_WHEEL_MODE]}, persist=False)
            message = '%s: %s' % (config.i18n['UI_setting_maxWheelMode_text'], MovementControl.getStatusText(settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.MAX_WHEEL_MODE]))
            sendPanelMessage(message, 'Green' if settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.MAX_WHEEL_MODE] else 'Red')
        if checkKeys(settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.BUTTON_AUTO_MODE]) and event.isKeyDown():
            settings_service.apply(config, {SERVER_TURRET_EXTENDED.AUTO_ACTIVATE_WHEEL_MODE: not settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.AUTO_ACTIVATE_WHEEL_MODE]}, persist=False)
            message = '%s: %s' % (config.i18n['UI_setting_autoActivateWheelMode_text'], MovementControl.getStatusText(settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.AUTO_ACTIVATE_WHEEL_MODE]))
            sendPanelMessage(message, 'Green' if settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.AUTO_ACTIVATE_WHEEL_MODE] else 'Red')

    # noinspection PyProtectedMember
    def changeMovement(self):
        player = getPlayer()
        vehicle = player.getVehicleAttached()
        if not (vehicle and vehicle.isAlive() and vehicle.isWheeledTech and vehicle.typeDescriptor.hasSiegeMode):
            return
        flags = player.makeVehicleMovementCommandByKeys()
        if vehicle.siegeState == VEHICLE_SIEGE_STATE.DISABLED:
            # noinspection PyProtectedMember
            if player._PlayerAvatar__cruiseControlMode:
                return self.changeSiege(True)
            if flags & MOVEMENT_FLAGS.ROTATE_RIGHT or flags & MOVEMENT_FLAGS.ROTATE_LEFT or flags & MOVEMENT_FLAGS.BLOCK_TRACKS:
                return
            if flags & MOVEMENT_FLAGS.FORWARD or flags & MOVEMENT_FLAGS.BACKWARD:
                return self.changeSiege(True)
        elif vehicle.siegeState == VEHICLE_SIEGE_STATE.ENABLED:
            # noinspection PyProtectedMember
            if not player._PlayerAvatar__cruiseControlMode:
                real_speed = int(vehicle.speedInfo.value[0] * 3.6)
                if (flags & MOVEMENT_FLAGS.ROTATE_RIGHT or flags & MOVEMENT_FLAGS.ROTATE_LEFT) and self.checkSpeedLimits(vehicle, real_speed):
                    return self.changeSiege(False)
                if flags & MOVEMENT_FLAGS.BLOCK_TRACKS:
                    return self.changeSiege(False)
                if 20 > real_speed > -20:
                    cmd_list = (CommandMapping.CMD_MOVE_FORWARD, CommandMapping.CMD_MOVE_FORWARD_SPEC, CommandMapping.CMD_MOVE_BACKWARD)
                    if not CommandMapping.g_instance.isActiveList(cmd_list):
                        return self.changeSiege(False)
                    if real_speed < 0 and flags & MOVEMENT_FLAGS.FORWARD:
                        return self.changeSiege(False)
                    if real_speed > 0 and flags & MOVEMENT_FLAGS.BACKWARD:
                        return self.changeSiege(False)

    def changeSiege(self, status):
        SoundNotifications.TRANSITION_TIMER = ''
        getPlayer().cell.vehicle_changeSetting(VEHICLE_SETTING.SIEGE_MODE_ENABLED, status)
        self.timer = serverTime()

    @staticmethod
    def checkSpeedLimits(vehicle, speed):
        if not settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.MAX_WHEEL_MODE]:
            return True
        speed_limits = vehicle.typeDescriptor.defaultVehicleDescr.physics['speedLimits']
        forward_limit = int(speed_limits[0] * 3.6)
        backward_limit = -int(speed_limits[1] * 3.6)
        return forward_limit > speed > backward_limit

    @staticmethod
    def fixSiegeModeCruiseControl():
        if not settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.FIX_WHEEL_CRUISE_CONTROL]:
            return False
        player = getPlayer()
        vehicle = player.getVehicleAttached()
        result = vehicle and vehicle.isAlive() and vehicle.isWheeledTech and vehicle.typeDescriptor.hasSiegeMode
        if result and vehicle.appearance and vehicle.appearance.engineAudition:
            sound_state_change = vehicle.typeDescriptor.type.siegeModeParams['soundStateChange']
            vehicle.appearance.engineAudition.setSiegeSoundEvents(sound_state_change.isEngine, sound_state_change.on, sound_state_change.off)
        return result


class Support(object):
    @staticmethod
    def message():
        sendPanelMessage(config.i18n['UI_battle_activateMessage'])

    def start_battle(self):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.ACTIVATE_MESSAGE]:
            callback(5.0, self.message)


config = ConfigInterface()
movement_control = MovementControl()
support = Support()


@override(PlayerAvatar, 'handleKey')
def new__playerAvatarHandleKey(func, *args):
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.FIX_ACCURACY_IN_MOVE]:
        self, is_down, key, mods = args
        movement_control.move_pressed(self, is_down, key)
    return func(*args)


@override(VehicleGunRotator.VehicleGunRotator, 'setShotPosition')
def new__vehicleGunRotatorSetShotPosition(func, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        if self._avatar.vehicle and settings_service.getComponentDict(config)[SERVER_TURRET_EXTENDED.SERVER_TURRET]:
            self._VehicleGunRotator__turretYaw, self._VehicleGunRotator__gunPitch = self._avatar.vehicle.getServerGunAngles()
            forceValueRefresh = True
    return func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new__startGUI(func, *args):
    func(*args)
    support.start_battle()
    movement_control.start_battle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new__destroyGUI(func, *args):
    movement_control.endBattle()
    func(*args)


@override(PlayerAvatar, 'updateSiegeStateStatus')
def new__updateSiegeStateStatus(func, self, vehicleID, status, timeLeft):
    if not settings_service.getComponentDict(config)[GLOBAL.ENABLED] or not movement_control.fixSiegeModeCruiseControl():
        return func(self, vehicleID, status, timeLeft)
    typeDescr = self._PlayerAvatar__updateVehicleStatus(vehicleID)
    if not typeDescr:
        return
    if status in VEHICLE_SIEGE_STATE.SWITCHING:
        if typeDescr.type.shouldStopEngineOnSiegeSwitch and not typeDescr.type.hasAutoSiegeMode:
            self._PlayerAvatar__cruiseControlMode = _CRUISE_CONTROL_MODE.NONE
        self._PlayerAvatar__updateCruiseControlPanel()
    self.guiSessionProvider.invalidateVehicleState(VEHICLE_VIEW_STATE.SIEGE_MODE, (status, timeLeft))
    self._PlayerAvatar__onSiegeStateUpdated(vehicleID, status, timeLeft)


def decodeRestrictedValueFromUint(code, bits, minBound, maxBound):
    code -= 0.5
    t = float(code) / ((1 << bits) - 1)
    return minBound + t * (maxBound - minBound)


def decodeAngleFromUint(code, bits):
    code -= 0.5
    return math.pi * 2.0 * code / (1 << bits) - math.pi


gun_rotation_shared.decodeRestrictedValueFromUint = decodeRestrictedValueFromUint
gun_rotation_shared.decodeAngleFromUint = decodeAngleFromUint


def fini():
    movement_control.endBattle()
