# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_ALIASES
from Driftkings.settings.templates.battle.dispersion_timer import DispersionTimerSettings as ConfigInterface
from Driftkings.views.battle.dispersion_timer import DispersionTimer

AS_BATTLE = BATTLE_ALIASES.DISPERSION_TIMER
config = ConfigInterface()


def getBattleViews():
    return ((AS_BATTLE, DispersionTimer, config),)
