# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_PERFORMANCE
from driftkings.settings.service import affects, settings_service

"""Presentation adapter for BattleEfficiency; gameplay state stays in its component."""


from importlib import import_module

from driftkings.flash.core import overlays
from driftkings.views.battle.label import CachedBattleLabel


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.components.battle_performance')


class Flash(CachedBattleLabel):
    def __init__(self, section):
        super(Flash, self).__init__(section, _component, BATTLE_PERFORMANCE.POSITION, BATTLE_PERFORMANCE)
        self.setVisible(False)

    def onSettingsChanged(self, component, changes):
        if self._destroyed:
            return
        if affects(changes, BATTLE_PERFORMANCE.TEXT_LOCK, BATTLE_PERFORMANCE.POSITION):
            self.onApplySettings()
        if affects(changes, BATTLE_PERFORMANCE.TEXT_SHADOW):
            shadow = settings_service.getComponentDict(_component().config)[BATTLE_PERFORMANCE.TEXT_SHADOW]
            overlays.update(self.section, {'shadow': shadow})

    def setVisible(self, visible):
        visible = bool(visible)
        if not self._destroyed and visible != self._lastVisible:
            if overlays.update(self.section, {'visible': visible}):
                self._lastVisible = visible

    def addText(self, text):
        if self._destroyed:
            return
        text_style = settings_service.getComponentDict(_component().config)[BATTLE_PERFORMANCE.TEXT_STYLE]
        formatted_text = '<font size=\'%s\' face=\'%s\' color=\'%s\'><p align=\'%s\'>%s</p></font>' % (
            text_style['size'], text_style['font'], text_style['color'], text_style['align'], text)
        if formatted_text != self._lastText:
            if overlays.update(self.section, {'text': formatted_text}):
                self._lastText = formatted_text


def _startFlash():
    _component().g_flash = Flash(_component().config.NAME)
