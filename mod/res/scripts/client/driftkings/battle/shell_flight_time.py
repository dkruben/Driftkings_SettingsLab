# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_ALIASES
from driftkings.settings.definitions.battle.shell_flight_time import ShellFlightTimeSettings as Settings
from driftkings.flash.batalha.shell_flight_time import FlightTime

AS_BATTLE = BATTLE_ALIASES.SHELL_FLIGHT_TIME
config = Settings()


def getBattleViews():
    return ((AS_BATTLE, FlightTime, config),)
