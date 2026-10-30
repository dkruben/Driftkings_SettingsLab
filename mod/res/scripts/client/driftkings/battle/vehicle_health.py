# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_ALIASES
from driftkings.flash.battle.vehicle_health import OwnHealth
from driftkings.settings.definitions.battle.vehicle_health import VehicleHealthSettings as Settings

AS_BATTLE = BATTLE_ALIASES.VEHICLE_HEALTH
config = Settings()


def getBattleViews():
    return ((AS_BATTLE, OwnHealth, config),)
