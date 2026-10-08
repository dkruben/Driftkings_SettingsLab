# -*- coding: utf-8 -*-
"""Native Scaleform package contract, loaded once by each battle application."""


def getViewSettings():
    from gui.Scaleform.framework import ComponentSettings, ScopeTemplates
    from Driftkings.views import BATTLE_COMPONENTS
    return tuple(ComponentSettings(alias, definition[0], ScopeTemplates.DEFAULT_SCOPE)
                 for alias, definition in sorted(BATTLE_COMPONENTS.items()))


def getBusinessHandlers():
    from .handler import BattleViewHandler
    return (BattleViewHandler(),)


def getContextMenuHandlers():
    return ()
