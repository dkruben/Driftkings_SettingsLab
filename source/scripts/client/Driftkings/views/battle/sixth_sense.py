# -*- coding: utf-8 -*-
"""Presentation adapter for SixthSense; gameplay state stays in its component."""
from importlib import import_module
from random import choice

from PlayerEvents import g_playerEvents
from SoundGroups import g_instance

from Driftkings._constants import SIXTH_SENSE
from Driftkings.meta.battle.sixth_sense import SixthSenseMeta


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.battle.sixth_sense')


class SixthSense(SixthSenseMeta):
    def __init__(self):
        super(SixthSense, self).__init__(SIXTH_SENSE.ID)
        self.radio_installed = False
        self.__sounds = dict()
        self.__visible = False
        self.__message = None
        self.__radar = None
        self.__soundID = None
        try:
            from constants import DIRECT_DETECTION_TYPE
            self.__radar = DIRECT_DETECTION_TYPE.STEALTH_RADAR
        except:
            pass

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
        if self.getSettings()[SIXTH_SENSE.PLAY_TICK_SOUND]:
            self.__soundID = self._arenaVisitor.type.getCountdownTimerSound()
        g_playerEvents.onRoundFinished += self._onRoundFinished
        g_playerEvents.onObservedByEnemy += self._onObservedByEnemy
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleStateUpdated += self._onVehicleStateUpdated
        optional_devices = self.sessionProvider.shared.optionalDevices
        if optional_devices is not None:
            optional_devices.onDescriptorDevicesChanged += self.onDevicesChanged

    def _dispose(self):
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
        message = choice(_component().MESSAGES)
        if message == self.__message:
            message = self.getNewRandomMessage()
        return message

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
                if settings[SIXTH_SENSE.USER_SOUND] and not settings[SIXTH_SENSE.PLAY_TICK_SOUND]:
                    g_instance.playSound2D(settings[SIXTH_SENSE.SIXTH_SENSE_SOUND])
        else:
            time = settings[SIXTH_SENSE.LAMP_SHOW_TIME]
            if settings[SIXTH_SENSE.USER_SOUND] and not settings[SIXTH_SENSE.PLAY_TICK_SOUND]:
                g_instance.playSound2D(settings[SIXTH_SENSE.SIXTH_SENSE_SOUND])
            if self.radio_installed:
                time -= 1.5
        self.__message = self.getNewRandomMessage()
        self.as_showS(time)

    def _onVehicleStateUpdated(self, state, value):
        if state in _component()._STATES_TO_HIDE:
            self.as_hideS()

    def _onRoundFinished(self, *_):
        self.as_hideS()

    def getTimerString(self, timeLeft):
        return self.__message.format(timeLeft)

    def playSound(self):
        if self.__soundID is not None:
            self.callWWISE(self.__soundID)
