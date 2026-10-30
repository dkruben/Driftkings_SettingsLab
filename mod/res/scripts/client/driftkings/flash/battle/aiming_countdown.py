# -*- coding: utf-8 -*-
"""Presentation adapter for DispersionTimer; gameplay state stays in its component."""
from collections import defaultdict

from gui.battle_control.avatar_getter import getInputHandler
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from driftkings._constants import AIMING_COUNTDOWN
from driftkings.core.aiming_timing import dispersion_timing
from driftkings.core.battle_events import battleEvents
from driftkings.flash.battle.meta.dispersion_timer import DispersionTimerMeta
from driftkings.game_constants import CTRL_MODE_NAME
from driftkings.logger import get_logger

LOG = get_logger('driftkings.flash.battle.aiming_countdown')


class DispersionTimer(DispersionTimerMeta):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(DispersionTimer, self).__init__(AIMING_COUNTDOWN.NAME)
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
        self.min_angle, percent, self.macro['timer'] = dispersion_timing(
            self.min_angle, aiming_angle, type_descriptor.gun.aimingTime)
        self.macro['color'] = self.getColor(percent)
        self.macro['percent'] = percent
        self.as_updateTimerTextS(self.getSettings()[AIMING_COUNTDOWN.TEMPLATE] % self.macro)

    def getColor(self, percent):
        settings = self.getSettings()
        value = percent
        if value < 15:
            color = settings[AIMING_COUNTDOWN.RED]
        elif value < 35:
            color = settings[AIMING_COUNTDOWN.ORANGE]
        elif value < 50:
            color = settings[AIMING_COUNTDOWN.YELLOW]
        elif value < 75:
            color = settings[AIMING_COUNTDOWN.GREEN]
        elif value < 90:
            color = settings[AIMING_COUNTDOWN.BLUE]
        else:
            color = settings[AIMING_COUNTDOWN.PURPLE]
        return color
