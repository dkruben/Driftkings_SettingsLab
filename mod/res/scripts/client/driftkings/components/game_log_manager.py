# -*- coding: utf-8 -*-
"""Functional damage-log filtering; presentation routing lives in Flash."""
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE

from driftkings._constants import GAME_LOG_MANAGER
from driftkings.flash.battle.game_log import WGLogs
from driftkings.settings.definitions.components.game_log_manager import GameLogManagerSettings
from driftkings.settings.service import settings_service

game_log_manager_settings = GameLogManagerSettings()


def get_filters():
    settings = settings_service.getComponentDict(game_log_manager_settings)
    return {
        PERSONAL_EFFICIENCY_TYPE.RECEIVED_CRITICAL_HITS: settings[GAME_LOG_MANAGER.WG_LOG_HIDE_CRITICS],
        PERSONAL_EFFICIENCY_TYPE.BLOCKED_DAMAGE: settings[GAME_LOG_MANAGER.WG_LOG_HIDE_BLOCK],
        PERSONAL_EFFICIENCY_TYPE.ASSIST_DAMAGE: settings[GAME_LOG_MANAGER.WG_LOG_HIDE_ASSIST],
        PERSONAL_EFFICIENCY_TYPE.STUN: settings[GAME_LOG_MANAGER.WG_LOG_HIDE_ASSIST]
    }


g_logs = WGLogs(game_log_manager_settings, get_filters)
