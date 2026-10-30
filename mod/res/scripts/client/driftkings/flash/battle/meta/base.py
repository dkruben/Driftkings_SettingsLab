# -*- coding: utf-8 -*-
"""Common DAAPI lifecycle; the native page owns component destruction."""
from account_helpers.settings_core.settings_constants import GRAPHICS
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.battle_session import IBattleSessionProvider

from driftkings.core.battle_capabilities import battle_capabilities
from driftkings.core.diagnostics import diagnostics
from driftkings.core.hud_visibility import hudVisibility
from driftkings.settings.service import settings_service


class ComponentMeta(BaseDAAPIComponent):
    def _populate(self):
        self._sentValues = {}
        super(ComponentMeta, self)._populate()

    def _dispose(self):
        try:
            super(ComponentMeta, self)._dispose()
        finally:
            self._sentValues = {}

    def _sendChanged(self, method, *values):
        """Deduplicate scalar, void setters only; commit cache after success."""
        if not self._isDAAPIInited():
            self._sentValues = {}
            return
        flash = self.flashObject
        cache = getattr(self, '_sentValues', None)
        if cache is None:
            cache = self._sentValues = {}
        previous = cache.get(method)
        if previous is not None and previous[0] is flash and previous[1] == values:
            if diagnostics.enabled:
                diagnostics.count('flash.' + self.FLASH_CLASS + '.' + method + '.skipped')
            return
        if diagnostics.enabled:
            result = diagnostics.call('flash.' + self.FLASH_CLASS + '.' + method, getattr(flash, method), *values)
        else:
            result = getattr(flash, method)(*values)
        cache[method] = (flash, values)
        return result

    def as_setComponentVisible(self, visible):
        if self._isDAAPIInited():
            return self.flashObject.setCompVisible(visible)


class HudMeta(ComponentMeta):
    def _populate(self):
        super(HudMeta, self)._populate()
        hudVisibility.attach(self)

    def _dispose(self):
        hudVisibility.detach(self)
        super(HudMeta, self)._dispose()

    def setBattleHudVisible(self, visible):
        if self._isDAAPIInited():
            return self.flashObject.as_setBattleHudVisible(visible)


class BattleMeta(HudMeta):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, section):
        super(BattleMeta, self).__init__()
        self.section = section

    def getSettings(self):
        return settings_service.getComponentDict(self.section)

    @property
    def _arenaDP(self):
        return self.sessionProvider.getArenaDP()

    @property
    def _arenaVisitor(self):
        return self.sessionProvider.arenaVisitor

    @property
    def isComp7Battle(self):
        return battle_capabilities.is_comp7()

    @property
    def gui(self):
        return self._arenaVisitor.gui

    def isSPG(self):
        return self.getVehicleInfo().isSPG()

    def getVehicleInfo(self, vID=None):
        return self._arenaDP.getVehicleInfo(vID)

    @property
    def isPlayerVehicle(self):
        vehicle = self.sessionProvider.shared.vehicleState.getControllingVehicle()
        if vehicle is not None:
            return vehicle.isPlayerVehicle
        observed_veh_id = self.sessionProvider.shared.vehicleState.getControllingVehicleID()
        return self.playerVehicleID == observed_veh_id or observed_veh_id == 0

    @property
    def playerVehicleID(self):
        return self._arenaDP.getPlayerVehicleID()

    def isColorBlind(self):
        return bool(self.settingsCore.getSetting(GRAPHICS.COLOR_BLIND))
