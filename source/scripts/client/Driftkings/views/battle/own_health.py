# -*- coding: utf-8 -*-
"""Presentation adapter for OwnHealth; gameplay state stays in its component."""
from PlayerEvents import g_playerEvents
from aih_constants import CTRL_MODE_NAME
from constants import ARENA_PERIOD
from gui.Scaleform.daapi.view.battle.shared.formatters import getHealthPercent, normalizeHealth
from gui.battle_control import avatar_getter
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.battle_control.controllers.prebattle_setups_ctrl import IPrebattleSetupsListener

from Driftkings._constants import OWN_HEALTH, GLOBAL
from Driftkings.common import percentToRgb
from Driftkings.meta.battle.own_health import OwnHealthMeta
from Driftkings.settings.service import settings_service


class OwnHealth(OwnHealthMeta, IPrebattleSetupsListener):
    def __init__(self):
        super(OwnHealth, self).__init__(OWN_HEALTH.ID)
        self.is_alive_mode = True
        self.is_battle_period = False
        self.maxHealth = 0
        self.currentHealth = 0
        self.template = '%d - %.2f%%'

    def updateVehicleParams(self, vehicle, *_):
        if vehicle is None or getattr(vehicle, 'descriptor', None) is None:
            return
        if self.maxHealth != vehicle.descriptor.maxHealth:
            self.maxHealth = vehicle.descriptor.maxHealth
        self._updateHealth(self.maxHealth)

    def _populate(self):
        super(OwnHealth, self)._populate()
        self._applySettings()
        settings_service.onModSettingsChanged.connect(self._onSettingsChanged, OWN_HEALTH)
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
        g_playerEvents.onArenaPeriodChange += self.onArenaPeriodChange
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleControlling += self.__onVehicleControlling
            ctrl.onVehicleStateUpdated += self.__onVehicleStateUpdated
            vehicle = ctrl.getControllingVehicle()
            if vehicle is not None:
                self.__onVehicleControlling(vehicle)
        arena = self._arenaVisitor.getArenaSubscription()
        if arena is not None:
            self.is_battle_period = arena.period == ARENA_PERIOD.BATTLE
        vInfo = self.getVehicleInfo()
        if vInfo is not None:
            self.is_alive_mode = vInfo.isAlive()
        self.as_BarVisibleS(settings_service.getSetting(OWN_HEALTH, GLOBAL.ENABLED) and self.is_battle_period and self.is_alive_mode)

    def onArenaPeriodChange(self, period, *_):
        self.is_battle_period = period == ARENA_PERIOD.BATTLE
        self.as_BarVisibleS(settings_service.getSetting(OWN_HEALTH, GLOBAL.ENABLED) and self.is_battle_period and self.is_alive_mode)

    def _dispose(self):
        settings_service.onModSettingsChanged.disconnect(self._onSettingsChanged)
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        g_playerEvents.onArenaPeriodChange -= self.onArenaPeriodChange
        ctrl = self.sessionProvider.shared.vehicleState
        if ctrl is not None:
            ctrl.onVehicleControlling -= self.__onVehicleControlling
            ctrl.onVehicleStateUpdated -= self.__onVehicleStateUpdated
        super(OwnHealth, self)._dispose()

    def _onSettingsChanged(self, component, changes):
        self._applySettings()
        if self.currentHealth > 0:
            self._updateHealth(self.currentHealth)

    def _applySettings(self):
        self.as_updateSettingsS()
        self.as_BarVisibleS(settings_service.getSetting(OWN_HEALTH, GLOBAL.ENABLED) and self.is_battle_period and self.is_alive_mode)

    def __onVehicleControlling(self, vehicle):
        if vehicle is None:
            return
        if self.maxHealth != vehicle.maxHealth:
            self.maxHealth = vehicle.maxHealth
        self.is_alive_mode = vehicle.health > 0
        self.as_BarVisibleS(settings_service.getSetting(OWN_HEALTH, GLOBAL.ENABLED) and self.is_battle_period and self.is_alive_mode)
        self._updateHealth(vehicle.health)

    def __onVehicleStateUpdated(self, state, value):
        if state == VEHICLE_VIEW_STATE.HEALTH:
            self.is_alive_mode = value > 0
            self.as_BarVisibleS(settings_service.getSetting(OWN_HEALTH, GLOBAL.ENABLED) and self.is_battle_period and self.is_alive_mode)
            self._updateHealth(value)

    def onCameraChanged(self, ctrlMode, *_, **__):
        self.is_alive_mode = ctrlMode not in {
            CTRL_MODE_NAME.KILL_CAM,
            CTRL_MODE_NAME.POSTMORTEM,
            CTRL_MODE_NAME.DEATH_FREE_CAM,
            CTRL_MODE_NAME.RESPAWN_DEATH,
            CTRL_MODE_NAME.VEHICLES_SELECTION,
            CTRL_MODE_NAME.LOOK_AT_KILLER
        }
        self.as_BarVisibleS(settings_service.getSetting(OWN_HEALTH, GLOBAL.ENABLED) and self.is_battle_period and self.is_alive_mode)

    @staticmethod
    def getAVGColor(percent=1.0):
        return percentToRgb(percent, **settings_service.getSetting(OWN_HEALTH, OWN_HEALTH.AVG_COLOR))

    def _updateHealth(self, health):
        if not isinstance(health, (int, long, float)) or health < 0:
            return
        self.currentHealth = health
        if health > self.maxHealth:
            self.maxHealth = health
        if self.maxHealth <= 0:
            return
        percent = getHealthPercent(health, self.maxHealth)
        text = self.template % (int(normalizeHealth(health)), percent * 100.0)
        self.as_setOwnHealthS(percent, text, self.getAVGColor(percent))
