# -*- coding: utf-8 -*-
from .base import BattleMeta


class OwnHealthMeta(BattleMeta):
    FLASH_CLASS = 'driftkings.battle.components.health.OwnHealthUI'

    def as_setOwnHealthS(self, scale, text, color):
        if self._isDAAPIInited():
            return self.flashObject.as_setOwnHealth(scale, text, color)

    def as_BarVisibleS(self, visible):
        if self._isDAAPIInited():
            return self.flashObject.as_BarVisible(visible)

    def as_updateSettingsS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_updateSettings()

    def getAVGColor(self):
        raise NotImplementedError
