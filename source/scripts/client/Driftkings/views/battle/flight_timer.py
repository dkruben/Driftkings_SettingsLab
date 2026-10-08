# -*- coding: utf-8 -*-
"""Presentation adapter for FlightTimer; gameplay state stays in its component."""
from collections import defaultdict

from aih_constants import CTRL_MODE_NAME
from gui.battle_control import avatar_getter
from math_utils import VectorConstant

from Driftkings._constants import FLIGHT_TIMER, GLOBAL
from Driftkings.common import getPlayer
from Driftkings.meta.battle.flight_timer import FlightTimeMeta


class FlightTime(FlightTimeMeta):

    def __init__(self):
        super(FlightTime, self).__init__(FLIGHT_TIMER.ID)
        self.macrosDict = defaultdict(lambda: 'Macros not found', flightTime=0, distance=0)

    def isFlightTimeEnabled(self):
        settings = self.getSettings()
        enabled = settings[GLOBAL.ENABLED]
        if settings[FLIGHT_TIMER.SPG_ONLY]:
            return enabled and self.isSPG()
        return enabled

    def _populate(self):
        super(FlightTime, self)._populate()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
            ctrl.onGunMarkerStateChanged += self.__onGunMarkerStateChanged
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
            ctrl.onGunMarkerStateChanged -= self.__onGunMarkerStateChanged
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        super(FlightTime, self)._dispose()

    def onCameraChanged(self, ctrlMode, *_, **__):
        if ctrlMode in {CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER}:
            self.as_flightTimeS('')

    def __onGunMarkerStateChanged(self, _, position, *__, **___):
        if not self.isFlightTimeEnabled():
            return self.as_flightTimeS('')
        player = getPlayer()
        if player is None:
            return self.as_flightTimeS('')
        if player.gunRotator is None:
            return self.as_flightTimeS('')
        shotPos, shotVec = player.gunRotator.getCurShotPosition()
        # Current clients pass GunMarkerState; older clients passed Vector3.
        position = getattr(position, 'position', position)
        if position is None or not hasattr(position, 'flatDistTo'):
            return self.as_flightTimeS('')
        flatDist = position.flatDistTo(shotPos)
        horizontalSpeed = shotVec.flatDistTo(VectorConstant.Vector3Zero)
        if horizontalSpeed <= 0.0:
            return self.as_flightTimeS('')
        self.macrosDict['flightTime'] = flatDist / horizontalSpeed
        self.macrosDict['distance'] = flatDist
        self.as_flightTimeS(self.getSettings()[FLIGHT_TIMER.TEMPLATE] % self.macrosDict)
