# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_ALIASES
from driftkings.flash.battle.aiming_countdown import DispersionTimer
from driftkings.settings.definitions.battle.aiming_countdown import AimingCountdownSettings

AS_BATTLE = BATTLE_ALIASES.AIMING_COUNTDOWN
aiming_countdown_settings = AimingCountdownSettings()


def getBattleViews():
    return ((AS_BATTLE, DispersionTimer, aiming_countdown_settings),)
