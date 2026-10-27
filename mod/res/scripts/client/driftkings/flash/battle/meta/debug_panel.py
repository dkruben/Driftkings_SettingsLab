# -*- coding: utf-8 -*-
from driftkings.flash.battle.meta.base import HudMeta


class DebugPanelMeta(HudMeta):
    FLASH_CLASS = 'driftkings.battle.components.debug_panel.debugpanelui'

    def setClock(self, text, visible):
        if self._isDAAPIInited():
            self.flashObject.as_setClock(text, visible)
