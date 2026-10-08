# -*- coding: utf-8 -*-
"""PlayerPanelPro wiring; settings and roster presentation have separate owners."""
from gui.shared.personality import ServicesLocator

from Driftkings.core import player_ratings
from Driftkings.settings.templates.battle.players_panel import PlayerPanelProSettings
from Driftkings.views.battle.player_ratings import RatingViews

g_config=PlayerPanelProSettings()
g_stats=player_ratings.configure(g_config)
g_panels=RatingViews(g_config, g_stats)
_started=False


def init():
    global _started
    if _started: return
    _started=True
    ServicesLocator.itemsCache.onSyncCompleted += g_stats.captureOwnStats
    g_stats.captureOwnStats()
    g_panels.start()


def fini():
    global _started
    if not _started: return
    _started=False
    ServicesLocator.itemsCache.onSyncCompleted -= g_stats.captureOwnStats
    g_panels.stop()


def getBattleViews():
    return g_panels.getBattleViews()
