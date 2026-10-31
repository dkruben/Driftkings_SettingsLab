# -*- coding: utf-8 -*-
"""Texts that follow the crosshair (aiming countdown, shell flight time, penetration) as owned
Gameface children of the native battle HUD. Each module keeps its settings; x/y stay an offset from
the crosshair, in interface units, as in the retired Flash views, and can be dragged with Ctrl."""
from collections import defaultdict
from importlib import import_module

from driftkings._constants import AIMING_COUNTDOWN, GLOBAL, PENETRATION_INDICATOR, SHELL_FLIGHT_TIME
from driftkings.core.hud_visibility import hudVisibility
from driftkings.gameface.battle.common import BattleCardAdapter
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.views.marks_model import finite

# Range of the x/y sliders in the settings panel.
POSITION_LIMIT = 2000


def _dead_camera(ctrlMode):
    from driftkings.game_constants import CTRL_MODE_NAME
    return ctrlMode in (CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM,
                        CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER)


class ReticleTextAdapter(BattleCardAdapter):
    """One text near the crosshair: Python formats it, JS places it at crosshair + offset."""
    QUIET_VISIBILITY = True
    COMPONENT = None
    SETTINGS = None
    # Key path of the x/y offset inside the module settings, and the text anchor.
    POSITION = ()
    ALIGN = 'left'

    def __init__(self, feature, namespace, title):
        super(ReticleTextAdapter, self).__init__(feature, namespace, get_logger('Driftkings.' + title), title, active=False)
        self.text = ''
        self.anchor = (.5, .5)
        self._crosshair = None
        self._inputHandler = None

    def settings(self):
        return settings_service.getComponentDict(getattr(import_module(self.COMPONENT), self.SETTINGS))

    def config(self):
        return getattr(import_module(self.COMPONENT), self.SETTINGS)

    def offsets(self, settings):
        for key in self.POSITION:
            settings = settings[key]
        return settings

    def startBattle(self):
        from gui.battle_control import avatar_getter
        from helpers import dependency
        from skeletons.gui.battle_session import IBattleSessionProvider
        if self.active:
            return
        self.active = True
        self.text = ''
        hudVisibility.attach(self)
        ctrl = dependency.instance(IBattleSessionProvider).shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.onCrosshairPositionChanged
            ctrl.onCrosshairViewChanged += self.onCrosshairViewChanged
            self._crosshair = ctrl
            self.updateAnchor()
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
            self._inputHandler = handler
        self.connectSources(ctrl)
        self.refresh()

    def stopBattle(self):
        if self.active:
            self.active = False
            hudVisibility.detach(self)
            self.disconnectSources(self._crosshair)
            if self._crosshair is not None:
                self._crosshair.onCrosshairPositionChanged -= self.onCrosshairPositionChanged
                self._crosshair.onCrosshairViewChanged -= self.onCrosshairViewChanged
                self._crosshair = None
            if self._inputHandler is not None:
                self._inputHandler.onCameraChanged -= self.onCameraChanged
                self._inputHandler = None
        self.text = ''
        self.refresh()

    def beforeDispose(self):
        self.stopBattle()

    def connectSources(self, crosshair):
        pass

    def disconnectSources(self, crosshair):
        pass

    def updateAnchor(self):
        """Crosshair position as a fraction of the screen; the strategic view aims at its centre."""
        from gui.battle_control.battle_constants import CROSSHAIR_VIEW_ID
        ctrl = self._crosshair
        if ctrl is None:
            return
        width, height = ctrl.getSize()
        x, y = ctrl.getPosition()
        if ctrl.getViewID() == CROSSHAIR_VIEW_ID.STRATEGIC or not width or not height:
            self.anchor = (.5, .5)
        else:
            self.anchor = (float(x) / width, float(y) / height)

    def onCrosshairPositionChanged(self, *_):
        self.updateAnchor()
        self.refresh()

    def onCrosshairViewChanged(self, *_):
        self.updateAnchor()
        self.refresh()

    def onCameraChanged(self, ctrlMode, *_, **__):
        if _dead_camera(ctrlMode):
            self.setText('')

    def setText(self, text):
        text = text or ''
        if text != self.text:
            self.text = text
            self.refresh()

    def savePosition(self, child, args):
        # Dragged with the battle cursor (Ctrl); the offset lands in the module's own x/y settings.
        if not self.active or not self.hudVisible or not child._guiVisible or not child._cursorVisible:
            return
        try:
            x, y = [max(-POSITION_LIMIT, min(POSITION_LIMIT, int(round(finite(args.get(key)))))) for key in ('x', 'y')]
        except (AttributeError, TypeError, ValueError):
            return
        values = {GLOBAL.X: x, GLOBAL.Y: y}
        for key in reversed(self.POSITION):
            values = {key: values}
        settings_service.apply(self.config(), values)

    def refresh(self):
        settings = self.settings()
        offsets = self.offsets(settings)
        config = {'x': offsets[GLOBAL.X], 'y': offsets[GLOBAL.Y], 'align': self.ALIGN, 'locked': False}
        enabled = bool(self.active and self.visible and self.hudVisible and settings[GLOBAL.ENABLED] and self.text)
        self.publish({'text': self.text, 'anchorX': self.anchor[0], 'anchorY': self.anchor[1]}, config, enabled)


class AimingCountdownAdapter(ReticleTextAdapter):
    COMPONENT = 'driftkings.battle.aiming_countdown'
    SETTINGS = 'aiming_countdown_settings'

    def __init__(self):
        super(AimingCountdownAdapter, self).__init__('DriftkingsAimingCountdown', AIMING_COUNTDOWN, 'AimingCountdown')
        self.minAngle = 1.0
        self.dead = False

    @property
    def ALIGN(self):
        return self.settings().get('align', 'left')

    def connectSources(self, crosshair):
        from driftkings.core.battle_events import battleEvents
        self.minAngle = 1.0
        self.dead = False
        battleEvents.dispersion.connect(self.updateDispersion)

    def disconnectSources(self, crosshair):
        from driftkings.core.battle_events import battleEvents
        battleEvents.dispersion.disconnect(self.updateDispersion)

    def onCameraChanged(self, ctrlMode, *_, **__):
        self.dead = _dead_camera(ctrlMode)
        if self.dead:
            self.minAngle = 1.0
            self.setText('')

    def updateDispersion(self, gunRotator):
        from driftkings.core.aiming_timing import dispersion_timing
        descriptor = gunRotator._avatar.vehicleTypeDescriptor
        angle = gunRotator.dispersionAngle
        if descriptor is None or self.dead or angle <= 0.0:
            return self.setText('')
        settings = self.settings()
        self.minAngle, percent, timer = dispersion_timing(self.minAngle, angle, descriptor.gun.aimingTime)
        macro = defaultdict(lambda: 'macros not found', timer=timer, percent=percent, color=self.color(settings, percent))
        self.setText(settings[AIMING_COUNTDOWN.TEMPLATE] % macro)

    @staticmethod
    def color(settings, percent):
        for limit, key in ((15, AIMING_COUNTDOWN.RED), (35, AIMING_COUNTDOWN.ORANGE), (50, AIMING_COUNTDOWN.YELLOW),
                           (75, AIMING_COUNTDOWN.GREEN), (90, AIMING_COUNTDOWN.BLUE)):
            if percent < limit:
                return settings[key]
        return settings[AIMING_COUNTDOWN.PURPLE]


class FlightTimeAdapter(ReticleTextAdapter):
    COMPONENT = 'driftkings.battle.shell_flight_time'
    SETTINGS = 'shell_flight_time_settings'

    def __init__(self):
        super(FlightTimeAdapter, self).__init__('DriftkingsFlightTime', SHELL_FLIGHT_TIME, 'FlightTime')

    @property
    def ALIGN(self):
        return self.settings().get('align', 'left')

    def connectSources(self, crosshair):
        if crosshair is not None:
            crosshair.onGunMarkerStateChanged += self.onGunMarkerStateChanged

    def disconnectSources(self, crosshair):
        if crosshair is not None:
            crosshair.onGunMarkerStateChanged -= self.onGunMarkerStateChanged

    def onGunMarkerStateChanged(self, _, position, *__, **___):
        from math_utils import VectorConstant

        from driftkings.common.utils.wgutils import getPlayer
        from driftkings.core.aiming_timing import flight_time
        from driftkings.core.battle_policy import battle_policy
        settings = self.settings()
        if not battle_policy.decision('shell_flight_time', settings[GLOBAL.ENABLED], settings[SHELL_FLIGHT_TIME.SPG_ONLY])[0]:
            return self.setText('')
        player = getPlayer()
        if player is None or player.gunRotator is None:
            return self.setText('')
        shotPos, shotVec = player.gunRotator.getCurShotPosition()
        # Current clients pass GunMarkerState; older clients passed Vector3.
        position = getattr(position, 'position', position)
        if position is None or not hasattr(position, 'flatDistTo'):
            return self.setText('')
        distance = position.flatDistTo(shotPos)
        speed = shotVec.flatDistTo(VectorConstant.Vector3Zero)
        if speed <= 0.0:
            return self.setText('')
        macro = defaultdict(lambda: 'Macros not found', flightTime=flight_time(distance, speed), distance=distance)
        template = settings[SHELL_FLIGHT_TIME.TEMPLATE]
        if '%(' in template:
            message = template % macro
        else:
            macro['distance'] = int(distance)
            message = template.format(**macro)
        self.setText(message)


class PenetrationAdapter(ReticleTextAdapter):
    COMPONENT = 'driftkings.battle.penetration_indicator'
    SETTINGS = 'penetration_indicator_settings'
    POSITION = ('position',)
    # The Flash view centred its text on the offset.
    ALIGN = 'center'

    def __init__(self):
        super(PenetrationAdapter, self).__init__('DriftkingsPenetration', PENETRATION_INDICATOR, 'Penetration')
        self.macro = defaultdict(lambda: 'macros not found')

    def connectSources(self, crosshair):
        from driftkings.ui.common.events import g_events
        g_events.onArmorChanged += self.onArmorChanged
        g_events.onMarkerColorChanged += self.onMarkerColorChanged

    def disconnectSources(self, crosshair):
        from driftkings.ui.common.events import g_events
        g_events.onArmorChanged -= self.onArmorChanged
        g_events.onMarkerColorChanged -= self.onMarkerColorChanged

    def onMarkerColorChanged(self, color):
        self.macro['color'] = self.config().i18n['UI_colors'].get(color, '#FFD700')
        self.macro['message'] = self.settings()[PENETRATION_INDICATOR.MESSAGES].get(color, '')

    def onArmorChanged(self, data):
        if data is None:
            return self.setText('')
        armor, piercingPower, caliber, ricochet, noDamage = data
        labels = self.config().i18n
        self.macro.update(ricochet=labels['UI_ricochet'] if ricochet else '', noDamage=labels['UI_noDamage'] if noDamage else '',
                          countedArmor=armor, piercingPower=piercingPower, piercingReserve=piercingPower - armor, caliber=caliber)
        self.setText(self.settings()[PENETRATION_INDICATOR.TEMPLATE] % self.macro)
