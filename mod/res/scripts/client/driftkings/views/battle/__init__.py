# -*- coding: utf-8 -*-
"""Native Scaleform package contract, loaded once by each battle application."""


def getViewSettings():
    from gui.Scaleform.framework import ComponentSettings, ScopeTemplates

    from driftkings.views import BATTLE_COMPONENTS
    return tuple(ComponentSettings(alias, definition[0], ScopeTemplates.DEFAULT_SCOPE)
                 for alias, definition in sorted(BATTLE_COMPONENTS.items()))


def getBusinessHandlers():
    from driftkings.views.battle.handler import BattleViewHandler
    return (BattleViewHandler(),)


def getContextMenuHandlers():
    return ()
