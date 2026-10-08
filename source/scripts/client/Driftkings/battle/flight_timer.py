# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_ALIASES
from Driftkings.settings.templates.battle.flight_timer import FlightTimerSettings as ConfigInterface
from Driftkings.views.battle.flight_timer import FlightTime

AS_BATTLE = BATTLE_ALIASES.FLIGHT_TIMER
config = ConfigInterface()


def getBattleViews():
    return ((AS_BATTLE, FlightTime, config),)
