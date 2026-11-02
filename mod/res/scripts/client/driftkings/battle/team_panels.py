# -*- coding: utf-8 -*-
"""PlayerPanelPro wiring; settings and roster presentation have separate owners."""
from gui.shared.personality import ServicesLocator

from driftkings.core import player_ratings
from driftkings.flash.battle.player_ratings import RatingViews
from driftkings.settings.definitions.battle.team_panels import TeamPanelsSettings

team_panels_settings = TeamPanelsSettings()
g_stats = player_ratings.configure(team_panels_settings)
g_panels = RatingViews(team_panels_settings, g_stats)
_started=False


def init():
    global _started
    if _started: return
    _started=True
    ServicesLocator.itemsCache.onSyncCompleted += g_stats.captureOwnStats
    g_stats.captureOwnStats()
    g_stats.start()
    g_panels.start()


def fini():
    global _started
    if not _started: return
    _started=False
    ServicesLocator.itemsCache.onSyncCompleted -= g_stats.captureOwnStats
    g_stats.stop()
    g_panels.stop()


def getBattleViews():
    return g_panels.getBattleViews()
