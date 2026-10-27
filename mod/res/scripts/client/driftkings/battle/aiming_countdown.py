# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_ALIASES
from driftkings.settings.definitions.battle.aiming_countdown import AimingCountdownSettings as Settings
from driftkings.flash.batalha.aiming_countdown import DispersionTimer

AS_BATTLE = BATTLE_ALIASES.AIMING_COUNTDOWN
config = Settings()


def getBattleViews():
    return ((AS_BATTLE, DispersionTimer, config),)
