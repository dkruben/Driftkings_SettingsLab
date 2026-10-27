# -*- coding: utf-8 -*-
"""Server gun-angle synchronization; no vehicle movement or firing control.

The client's own angle decoding is used, as for its native server reticle.
"""
import VehicleGunRotator

from driftkings._constants import GLOBAL, SERVER_TURRET_SYNC
from driftkings.common.utils import events
from driftkings.flash.batalha.messages import sendPanelMessage
from driftkings.core.callbacks import callback
from driftkings.core.hooks import on_event, override
from driftkings.settings.definitions.battle.server_turret_sync import ServerTurretSyncSettings as Settings
from driftkings.settings.service import settings_service

config = Settings()


@override(VehicleGunRotator.VehicleGunRotator, 'setShotPosition')
def new__vehicleGunRotatorSetShotPosition(func, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
    settings = settings_service.getComponentDict(config)
    if settings[GLOBAL.ENABLED]:
        if self._avatar.vehicle and settings[SERVER_TURRET_SYNC.SERVER_TURRET]:
            self._VehicleGunRotator__turretYaw, self._VehicleGunRotator__gunPitch = self._avatar.vehicle.getServerGunAngles()
            forceValueRefresh = True
    return func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)


@on_event(events.PlayerAvatar.startGUI.after)
def new__startGUI(*args):
    settings = settings_service.getComponentDict(config)
    if settings[GLOBAL.ENABLED] and settings[SERVER_TURRET_SYNC.ACTIVATE_MESSAGE]:
        callback(5.0, lambda: sendPanelMessage(config.i18n['UI_battle_activateMessage']))

