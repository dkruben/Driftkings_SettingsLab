# -*- coding: utf-8 -*-
"""Presentation adapter for SixthSense; gameplay state stays in its component."""
from importlib import import_module
from random import choice

from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from PlayerEvents import g_playerEvents
from SoundGroups import g_instance

from driftkings._constants import SIXTH_SENSE_ALERT
from driftkings.flash.batalha.meta.sixth_sense import SixthSenseMeta

_STATES_TO_HIDE = frozenset((
    VEHICLE_VIEW_STATE.SWITCHING, VEHICLE_VIEW_STATE.RESPAWNING,
    VEHICLE_VIEW_STATE.DESTROYED, VEHICLE_VIEW_STATE.CREW_DEACTIVATED))
_MESSAGES = (
    "Detected: <font color='#daff8f'>{}</font> sec.",
    "Hide: <font color='#daff8f'>{}</font> sec.",
    "Run: <font color='#daff8f'>{}</font> sec.",
    "Alert: <font color='#ff7f7f'>{}</font> sec.",
    "Danger: <font color='#ff5555'>{}</font> sec.")

def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.battle.sixth_sense_alert')


class SixthSense(SixthSenseMeta):
    def __init__(self):
        super(SixthSense, self).__init__(SIXTH_SENSE_ALERT.NAME)
        self.radio_installed = False
        self.iconReady = False
        self.__sounds = dict()
        self.__visible = False
        self.__message = None
        self.__radar = None
        self.__soundID = None
        try:
            from constants import DIRECT_DETECTION_TYPE
            self.__radar = DIRECT_DETECTION_TYPE.STEALTH_RADAR
        except (ImportError, AttributeError):
            # Older clients do not define the stealth radar detection type.
            self.__radar = None

    def callWWISE(self, wwiseEventName):
        if wwiseEventName in self.__sounds:
            sound = self.__sounds[wwiseEventName]
        else:
            sound = g_instance.getSound2D(wwiseEventName)
            self.__sounds[wwiseEventName] = sound
        if sound is not None:
            if sound.isPlaying:
                sound.stop()
            sound.play()

    def _populate(self):
        super(SixthSense, self)._populate()
        _component().g_view = self
        if self.getSettings()[SIXTH_SENSE_ALERT.PLAY_TICK_SOUND]:
            self.__soundID = self._arenaVisitor.type.getCountdownTimerSound()
        g_playerEvents.onRoundFinished += self._onRoundFinished
        g_playerEvents.onObservedByEnemy += self._onObservedByEnemy
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleStateUpdated += self._onVehicleStateUpdated
        optional_devices = self.sessionProvider.shared.optionalDevices
        if optional_devices is not None:
            optional_devices.onDescriptorDevicesChanged += self.onDevicesChanged

    def onIconReady(self):
        self.iconReady = True

    def _dispose(self):
        self.iconReady = False
        if _component().g_view is self:
            _component().g_view = None
        if self.sessionProvider.isReplayPlaying and self._getPyReloading():
            self.as_hideS()
        for sound in self.__sounds.values():
            sound.stop()
        self.__sounds.clear()
        self.__soundID = None
        g_playerEvents.onRoundFinished -= self._onRoundFinished
        g_playerEvents.onObservedByEnemy -= self._onObservedByEnemy
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleStateUpdated -= self._onVehicleStateUpdated
        optional_devices = self.sessionProvider.shared.optionalDevices
        if optional_devices is not None:
            optional_devices.onDescriptorDevicesChanged -= self.onDevicesChanged
        super(SixthSense, self)._dispose()

    def onDevicesChanged(self, devices):
        self.radio_installed = 'improvedRadioCommunication' in (device.groupName for device in devices if device is not None)

    def getNewRandomMessage(self):
        return choice([message for message in _MESSAGES if message != self.__message])

    def _onObservedByEnemy(self, detection_type, is_observed):
        if not is_observed:
            self.as_hideS()
            return
        self.__last_detection_type = detection_type
        settings = self.getSettings()
        if hasattr(self, 'isComp7Battle') and self.isComp7Battle:
            if detection_type == self.__radar:
                time = 2
            else:
                time = 4
                if settings[SIXTH_SENSE_ALERT.USER_SOUND] and not settings[SIXTH_SENSE_ALERT.PLAY_TICK_SOUND]:
                    self.callWWISE(settings[SIXTH_SENSE_ALERT.SIXTH_SENSE_SOUND])
        else:
            time = settings[SIXTH_SENSE_ALERT.LAMP_SHOW_TIME]
            if settings[SIXTH_SENSE_ALERT.USER_SOUND] and not settings[SIXTH_SENSE_ALERT.PLAY_TICK_SOUND]:
                self.callWWISE(settings[SIXTH_SENSE_ALERT.SIXTH_SENSE_SOUND])
            if self.radio_installed:
                time -= 1.5
        self.__message = self.getNewRandomMessage()
        self.as_showS(time)

    def _onVehicleStateUpdated(self, state, value):
        if state in _STATES_TO_HIDE:
            self.as_hideS()

    def _onRoundFinished(self, *_):
        self.as_hideS()

    def getTimerString(self, timeLeft):
        return self.__message.format(timeLeft)

    def playSound(self):
        if self.__soundID is not None:
            self.callWWISE(self.__soundID)
