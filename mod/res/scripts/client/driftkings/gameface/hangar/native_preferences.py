# -*- coding: utf-8 -*-
"""Active native Gameface preference hooks, owned by the functional component."""
from gui.impl.lobby.hangar.presenters.user_missions_presenter import UserMissionsPresenter
from gui.impl.lobby.page.session_stats_presenter import SessionStatsPresenter
from gui.impl.lobby.user_missions.hangar_widget.presenters.battle_pass_presenter import BattlePassPresenter
from gui.impl.lobby.user_missions.hangar_widget.services import IBattlePassService, IUserMissionWidgetService

from helpers import dependency

from driftkings._constants import GLOBAL, HANGAR_PREFERENCES
from driftkings.core.hooks import override
from driftkings.settings.service import settings_service


def refresh_battle_pass(data):
    visible = dependency.instance(IBattlePassService).isVisible()
    if data[GLOBAL.ENABLED] and not data[HANGAR_PREFERENCES.SHOW_BATTLE_PASS_WIDGET]:
        visible = False
    dependency.instance(IUserMissionWidgetService).setGroupVisibility(BattlePassPresenter.GROUP, visible)


def install(config, _overrideIfAvailable):
    @_overrideIfAvailable(SessionStatsPresenter, '_SessionStatsPresenter__updateSessionStats')
    def new__updateSessionStats(func, self):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_BUTTON, True):
            return
        return func(self)


    @_overrideIfAvailable(SessionStatsPresenter, '_SessionStatsPresenter__updateBattleCount')
    def new__updateBattleCountPresenter(func, self, model):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_BATTLE_COUNT, True):
            model.setBattleCount(0)
            return
        return func(self, model)


    @_overrideIfAvailable(UserMissionsPresenter, '_updateMissions')
    def new__updateMissions(func, self, vm):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_DAILY_QUEST_WIDGET, True):
            self._addChild(self._WIDGET_ALIAS.Quests(), False)
            vm.setAreMissionsActive(False)
            return
        return func(self, vm)


    @_overrideIfAvailable(UserMissionsPresenter, '_updateEntryPoints')
    def new__updateEntryPoints(func, self, vm):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_EVENT_BANNER, True):
            self._addChild(self._WIDGET_ALIAS.Events(), False)
            vm.setIsAnyEntryPointAvailable(False)
            return
        return func(self, vm)


    @_overrideIfAvailable(UserMissionsPresenter, '_updateBattlePass')
    def new__updateBattlePass(func, self, vm):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_BATTLE_PASS_WIDGET, True):
            self._addChild(self._WIDGET_ALIAS.BattlePass(), False)
            vm.setIsBattlePassActive(False)
            return
        return func(self, vm)


    @override(BattlePassPresenter, 'isVisible')
    def new__battlePassIsVisible(func, self):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_BATTLE_PASS_WIDGET, True):
            return False
        return func(self)


    @override(UserMissionsPresenter, '_onGroupVisibilityChanged')
    def new__missionGroupVisibility(func, self, groupName, isVisible):
        settings = settings_service.getComponentDict(config)
        if groupName == BattlePassPresenter.GROUP and settings[GLOBAL.ENABLED] and not settings[HANGAR_PREFERENCES.SHOW_BATTLE_PASS_WIDGET]:
            isVisible = False
        return func(self, groupName, isVisible)

