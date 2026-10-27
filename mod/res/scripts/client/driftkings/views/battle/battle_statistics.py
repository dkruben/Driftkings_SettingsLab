# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_STATISTICS
from driftkings.settings.service import affects, settings_service

"""Presentation adapter for BattleStat; gameplay state stays in its component."""


from importlib import import_module

from driftkings.flash.core import overlays
from driftkings.views.battle.label import CachedBattleLabel


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.battle.battle_statistics')


class Flash(CachedBattleLabel):
    def __init__(self, section, params):
        super(Flash, self).__init__(section, _component, BATTLE_STATISTICS.TEXT_POSITION, BATTLE_STATISTICS)
        self.font = params['font']
        self.size = params['size']
        self.color = params['color']
        self.bold = params['bold']
        self.italic = params['italic']
        self._begin_tag = '<font face=\'%s\' size=\'%d\' color=\'%s\'>%s%s' % (self.font, self.size, self.color, '<b>' if self.bold else '', '<i>' if self.italic else '')
        self._end_tag = '%s%s</font>' % ('</b>' if self.bold else '', '</i>' if self.italic else '')

    def onSettingsChanged(self, component, changes):
        if not self._destroyed and affects(changes, BATTLE_STATISTICS.TEXT_LOCK, BATTLE_STATISTICS.TEXT_POSITION):
            self.onApplySettings()

    def getHtmlTextWithTags(self, text='', font=None, size=None, color=None, bold=None, italic=None):
        if not text:
            return ''
        return '<font face=\'%s\' size=\'%d\' color=\'%s\'>%s%s%s%s%s</font>' % (font if font else self.font, size if size else self.size, color if color else self.color, '<b>' if bold or self.bold else '', '<i>' if italic or self.italic else '', text, '</b>' if bold or self.bold else '', '</i>' if italic or self.italic else '')

    def getSimpleTextWithTags(self, text):
        return self._begin_tag + text + self._end_tag if text else ''

    def HtmlText(self, text=''):
        if not self._destroyed and text != self._lastText:
            if overlays.update(self.section, {'text': text}):
                self._lastText = text

    def setVisible(self, status):
        status = bool(status)
        if not self._destroyed and status != self._lastVisible:
            if overlays.update(self.section, {'visible': status}):
                self._lastVisible = status


def _startFlash():
    _component().g_flash = Flash(_component().config.NAME, settings_service.getComponentDict(_component().config)[BATTLE_STATISTICS.TEXT_FORMAT])
