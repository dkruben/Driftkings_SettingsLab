# -*- coding: utf-8 -*-
"""Native battle Flash presentation hooks; settings/data belong to the component."""
from gui.battle_results.components.common import ShowRateSatisfactionCmp
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel
from gui.Scaleform.daapi.view.battle.shared.hint_panel import BattleHintPanel
from gui.Scaleform.daapi.view.battle.shared.hint_panel import plugins as hint_plugins
from gui.Scaleform.daapi.view.battle.shared.page import SharedPage
from gui.Scaleform.daapi.view.battle.shared.stats_exchange import BattleStatisticsDataController
import messenger.gui.Scaleform.view.battle.messenger_view as messenger_view

from driftkings._constants import BATTLE_PREFERENCES, GLOBAL
from driftkings.core.hooks import override
from driftkings.settings.service import settings_service


def install(config, _getAttackerName):
    @override(BattleHintPanel, '_initPlugins')
    def _initPlugins(func, self, *args, **kwargs):
        settings = settings_service.getComponentDict(config)
        if not settings[GLOBAL.ENABLED]:
            return func(self, *args, **kwargs)
        if settings.get(BATTLE_PREFERENCES.HIDE_HINT, False):
            if self._plugins is not None:
                self._plugins.stop()
                self._plugins.fini()
                self._plugins = None
            return None
        return func(self, *args, **kwargs)


    @override(hint_plugins, 'createPlugins')
    def new_createPlugins(func, *args, **kwargs):
        settings = settings_service.getComponentDict(config)
        result = func(*args, **kwargs)
        if settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.SHOW_BATTLE_HINT]:
            result.clear()
        return result


    @override(SharedPage, 'as_onPostmortemActiveS')
    def new_setPostmortemTipsVisibleS(func, self, value):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED]:
            if not settings[BATTLE_PREFERENCES.POSTMORTEM_TIPS]:
                value = False
        func(self, value)


    @override(SharedPage, '_switchToPostmortem')
    def new_switchToPostmortem(func, *args):
        settings = settings_service.getComponentDict(config)
        if not settings[GLOBAL.ENABLED] or settings[BATTLE_PREFERENCES.POSTMORTEM_TIPS]:
            func(*args)


    @override(BattleStatisticsDataController, 'as_setQuestsInfoS')
    def new_setQuestsInfoS(func, self, data, _):
        func(self, data, True)


    @override(messenger_view, '_makeSettingsVO')
    def new__makeSettingsVO(func, self):
        makeSettingsVO = func(self)
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED]:
            makeSettingsVO['numberOfMessagesInHistory'] = settings[BATTLE_PREFERENCES.MAX_CHAT_LINES]
        return makeSettingsVO


    @override(ShowRateSatisfactionCmp, '_convert')
    def new_showRateSatisfactionCmp(func, self, value, reusable):
        settings = settings_service.getComponentDict(config)
        if settings[GLOBAL.ENABLED] and not settings.get(BATTLE_PREFERENCES.SHOW_PLAYER_SATISFACTION_WIDGET, True):
            return False
        return func(self, value, reusable)


    def _withEnemyName(method):
        def hook(func, self, value, actionTypeImg, vehicleTypeImg, vehicleName, shellTypeStr, shellTypeBG, shellModeImg=None):
            settings = settings_service.getComponentDict(config)
            if settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.ADD_ENEMY_NAME]:
                vehicleName = vehicleName + ' | ' + _getAttackerName(vehicleName)
            return func(self, value, actionTypeImg, vehicleTypeImg, vehicleName, shellTypeStr, shellTypeBG, shellModeImg)
        # The explicit method identifies each hook, including its diagnostics key.
        return override(DamageLogPanel, method)(hook)


    _withEnemyName('_addToTopLog')
    _withEnemyName('_addToBottomLog')
