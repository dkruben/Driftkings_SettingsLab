# -*- coding: utf-8 -*-
from driftkings.flash.battle.meta.base import HudMeta


class OverlayMeta(HudMeta):
    FLASH_CLASS = 'driftkings.battle.components.overlay.overlayui'

    def reset(self, elements):
        if self._isDAAPIInited():
            return self.flashObject.as_reset(elements)

    def createElement(self, alias, kind, props):
        if self._isDAAPIInited():
            return self.flashObject.as_create(alias, kind, props)

    def update(self, alias, props, duration):
        if self._isDAAPIInited():
            return self.flashObject.as_update(alias, props, duration)

    def remove(self, alias):
        if self._isDAAPIInited():
            return self.flashObject.as_remove(alias)

    def onElementMoved(self, alias, x, y):
        raise NotImplementedError
