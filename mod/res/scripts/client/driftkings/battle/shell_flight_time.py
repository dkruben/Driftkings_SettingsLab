# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_ALIASES
from driftkings.flash.battle.shell_flight_time import FlightTime
from driftkings.settings.definitions.battle.shell_flight_time import ShellFlightTimeSettings

AS_BATTLE = BATTLE_ALIASES.SHELL_FLIGHT_TIME
shell_flight_time_settings = ShellFlightTimeSettings()


def getBattleViews():
    return ((AS_BATTLE, FlightTime, shell_flight_time_settings),)
