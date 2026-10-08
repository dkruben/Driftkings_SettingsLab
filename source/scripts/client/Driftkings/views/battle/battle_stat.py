# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_STAT
from Driftkings.settings.service import settings_service, affects
"""Presentation adapter for BattleStat; gameplay state stays in its component."""


from Driftkings.core.overlay import overlays
from Driftkings.views.battle.label import BattleLabel
from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.battle.battle_stat')


class Flash(BattleLabel):
    def __init__(self, ID, params):
        self._lastText = None
        self._lastVisible = None
        self._destroyed = False
        super(Flash, self).__init__(ID, _component, BATTLE_STAT.TEXT_POSITION)
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, BATTLE_STAT)
        self.font = params['font']
        self.size = params['size']
        self.color = params['color']
        self.bold = params['bold']
        self.italic = params['italic']
        self._begin_tag = '<font face=\'%s\' size=\'%d\' color=\'%s\'>%s%s' % (self.font, self.size, self.color, '<b>' if self.bold else '', '<i>' if self.italic else '')
        self._end_tag = '%s%s</font>' % ('</b>' if self.bold else '', '</i>' if self.italic else '')

    def _layout(self):
        result = super(Flash, self)._layout()
        result['border'] = False
        return result

    def onSettingsChanged(self, component, changes):
        if not self._destroyed and affects(changes, BATTLE_STAT.TEXT_LOCK, BATTLE_STAT.TEXT_POSITION):
            self.onApplySettings()

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        super(Flash, self).destroy()
        self._lastText = self._lastVisible = None

    def getHtmlTextWithTags(self, text='', font=None, size=None, color=None, bold=None, italic=None):
        if not text:
            return ''
        return '<font face=\'%s\' size=\'%d\' color=\'%s\'>%s%s%s%s%s</font>' % (font if font else self.font, size if size else self.size, color if color else self.color, '<b>' if bold or self.bold else '', '<i>' if italic or self.italic else '', text, '</b>' if bold or self.bold else '', '</i>' if italic or self.italic else '')

    def getSimpleTextWithTags(self, text):
        return self._begin_tag + text + self._end_tag if text else ''

    def HtmlText(self, text=''):
        if not self._destroyed and text != self._lastText:
            if overlays.update(self.ID, {'text': text}):
                self._lastText = text

    def setVisible(self, status):
        status = bool(status)
        if not self._destroyed and status != self._lastVisible:
            if overlays.update(self.ID, {'visible': status}):
                self._lastVisible = status


def _startFlash():
    _component().g_flash = Flash(_component().config.ID, settings_service.getComponentDict(_component().config)[BATTLE_STAT.TEXT_FORMAT])
