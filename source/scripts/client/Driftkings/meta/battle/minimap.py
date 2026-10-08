# -*- coding: utf-8 -*-
from .base import BattleMeta


class MinimapMeta(BattleMeta):
    FLASH_CLASS = 'driftkings.battle.components.minimap.MinimapCentred'

    def as_minimapPresentationS(self, options):
        if self._isDAAPIInited():
            return self.flashObject.as_minimapPresentation(options)

    def as_minimapVehicleS(self, payload):
        if self._isDAAPIInited():
            return self.flashObject.as_minimapVehicle(payload)

    def as_minimapRangesS(self, payload):
        if self._isDAAPIInited():
            return self.flashObject.as_minimapRanges(payload)
