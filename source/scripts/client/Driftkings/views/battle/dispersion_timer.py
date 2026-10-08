# -*- coding: utf-8 -*-
"""Presentation adapter for DispersionTimer; gameplay state stays in its component."""
from collections import defaultdict
from math import ceil, log

from aih_constants import CTRL_MODE_NAME
from gui.battle_control.avatar_getter import getInputHandler
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from Driftkings._constants import DISPERSION_TIMER
from Driftkings.common import logDebug
from Driftkings.core.battle_events import battleEvents
from Driftkings.meta.battle.dispersion_timer import DispersionTimerMeta


class DispersionTimer(DispersionTimerMeta):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(DispersionTimer, self).__init__(DISPERSION_TIMER.ID)
        self.macro = defaultdict(lambda: 'macros not found', timer=0, percent=0)
        self.min_angle = 1.0
        self.isPostmortem = False

    def _populate(self):
        super(DispersionTimer, self)._populate()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
        battleEvents.dispersion.connect(self.updateDispersion)

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        battleEvents.dispersion.disconnect(self.updateDispersion)
        super(DispersionTimer, self)._dispose()

    def onCameraChanged(self, ctrlMode, _=None):
        self.isPostmortem = ctrlMode in {CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM, CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER}
        if self.isPostmortem:
            self.min_angle = 1.0
            self.as_updateTimerTextS('')

    def updateDispersion(self, gunRotator):
        type_descriptor = gunRotator._avatar.vehicleTypeDescriptor
        if type_descriptor is None or self.isPostmortem:
            return self.as_updateTimerTextS('')
        aiming_angle = gunRotator.dispersionAngle
        if aiming_angle <= 0.0:
            return self.as_updateTimerTextS('')
        if self.min_angle > aiming_angle:
            self.min_angle = aiming_angle
            logDebug(self.ID, False, 'DispersionTimer - renew min dispersion angle {}', self.min_angle)

        diff = self.min_angle / aiming_angle
        percent = int(ceil(diff * 100))
        self.macro['timer'] = round(type_descriptor.gun.aimingTime * abs(log(diff)), 2)
        self.macro['color'] = self.getColor(percent)
        self.macro['percent'] = percent
        self.as_updateTimerTextS(self.getSettings()[DISPERSION_TIMER.TEMPLATE] % self.macro)

    def getColor(self, percent):
        settings = self.getSettings()
        value = percent
        if value < 15:
            color = settings[DISPERSION_TIMER.RED]
        elif value < 35:
            color = settings[DISPERSION_TIMER.ORANGE]
        elif value < 50:
            color = settings[DISPERSION_TIMER.YELLOW]
        elif value < 75:
            color = settings[DISPERSION_TIMER.GREEN]
        elif value < 90:
            color = settings[DISPERSION_TIMER.BLUE]
        else:
            color = settings[DISPERSION_TIMER.PURPLE]
        return color
