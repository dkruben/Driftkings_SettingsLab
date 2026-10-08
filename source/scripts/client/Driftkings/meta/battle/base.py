# -*- coding: utf-8 -*-
"""Common DAAPI lifecycle; the native page owns component destruction."""
from account_helpers.settings_core.settings_constants import GRAPHICS
from constants import ARENA_BONUS_TYPE
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.battle_session import IBattleSessionProvider

from Driftkings.core.hud_visibility import hudVisibility
from Driftkings.settings.service import settings_service


class ComponentMeta(BaseDAAPIComponent):
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

    def __init__(self, ID):
        super(BattleMeta, self).__init__()
        self.ID = ID

    def getSettings(self):
        return settings_service.getComponentDict(self.ID)

    @property
    def _arenaDP(self):
        return self.sessionProvider.getArenaDP()

    @property
    def _arenaVisitor(self):
        return self.sessionProvider.arenaVisitor

    @property
    def isComp7Battle(self):
        return self._arenaVisitor.getArenaBonusType() == ARENA_BONUS_TYPE.COMP7

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


class CrosshairMeta(BattleMeta):
    def as_onCrosshairPositionChangedS(self, x, y):
        if self._isDAAPIInited():
            return self.flashObject.as_onCrosshairPositionChanged(x, y)
