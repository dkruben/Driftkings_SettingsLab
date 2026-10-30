# -*- coding: utf-8 -*-
"""Clock transport owned by the native battle debug panel's view lifecycle."""
import locale
from time import strftime

from driftkings._constants import BATTLE_PREFERENCES, GLOBAL
from driftkings.flash.battle.meta.debug_panel import DebugPanelMeta
from driftkings.settings.service import settings_service
from driftkings.ui.utils.timers import CyclicTimerEvent


class DebugPanelView(DebugPanelMeta):
    def __init__(self):
        super(DebugPanelView, self).__init__()
        self.timer = CyclicTimerEvent(1.0, self.updateClock)

    def _populate(self):
        super(DebugPanelView, self)._populate()
        self.timer.start()

    def _dispose(self):
        self.timer.stop()
        super(DebugPanelView, self)._dispose()

    def updateClock(self):
        settings = settings_service.getComponentDict(BATTLE_PREFERENCES.NAME)
        enabled = settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.IN_BATTLE]
        text = strftime(settings[BATTLE_PREFERENCES.FORMAT]) if enabled else ''
        if isinstance(text, bytes):
            text = text.decode(locale.getpreferredencoding() or 'utf-8', 'replace')
        self.setClock(text, enabled)
