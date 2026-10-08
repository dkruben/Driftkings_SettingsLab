# -*- coding: utf-8 -*-
from functools import partial

from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import _LogViewComponent, DamageLogPanel
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE

from Driftkings._constants import GLOBAL, LOGS_SWAPPER
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.components.log_files import LogsSwapperSettings as ConfigInterface

config = ConfigInterface()


class WGLogs(object):
    def __init__(self):
        override(_LogViewComponent, 'addToLog', self.new__addToLog)
        # Route the final Flash calls, preserving BattleOptions and other log hooks.
        for top, bottom in (('as_addDetailMessageTopS', 'as_addDetailMessageBottomS'), ('as_detailStatsTopS', 'as_detailStatsBottomS')):
            originalTop = getattr(DamageLogPanel, top)
            originalBottom = getattr(DamageLogPanel, bottom)
            override(DamageLogPanel, top, partial(self.routeLog, originalBottom))
            override(DamageLogPanel, bottom, partial(self.routeLog, originalTop))

    def routeLog(self, opposite, func, panel, *args, **kwargs):
        target = opposite if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[LOGS_SWAPPER.LOG_SWAPPER] else func
        return target(panel, *args, **kwargs)

    def new__addToLog(self, func, component, event):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return func(component, event)
        validated = self.getFilters()
        filtered_events = [e for e in event if not validated.get(e.getType(), False)]
        return func(component, filtered_events)

    @staticmethod
    def getFilters():
        return {
            PERSONAL_EFFICIENCY_TYPE.RECEIVED_CRITICAL_HITS: settings_service.getComponentDict(config)[LOGS_SWAPPER.WG_LOG_HIDE_CRITICS],
            PERSONAL_EFFICIENCY_TYPE.BLOCKED_DAMAGE: settings_service.getComponentDict(config)[LOGS_SWAPPER.WG_LOG_HIDE_BLOCK],
            PERSONAL_EFFICIENCY_TYPE.ASSIST_DAMAGE: settings_service.getComponentDict(config)[LOGS_SWAPPER.WG_LOG_HIDE_ASSIST],
            PERSONAL_EFFICIENCY_TYPE.STUN: settings_service.getComponentDict(config)[LOGS_SWAPPER.WG_LOG_HIDE_ASSIST]
        }


g_logs = WGLogs()
