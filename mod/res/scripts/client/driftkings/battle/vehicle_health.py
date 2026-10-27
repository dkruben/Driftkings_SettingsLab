# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_ALIASES
from driftkings.settings.definitions.battle.vehicle_health import VehicleHealthSettings as Settings
from driftkings.flash.batalha.vehicle_health import OwnHealth

AS_BATTLE = BATTLE_ALIASES.VEHICLE_HEALTH
config = Settings()


def getBattleViews():
    return ((AS_BATTLE, OwnHealth, config),)
