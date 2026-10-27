# -*- coding: utf-8 -*-
from driftkings.flash.battle.meta.base import BattleMeta


class MinimapMeta(BattleMeta):
    FLASH_CLASS = 'driftkings.battle.components.minimap.minimapenhancementsui'

    def as_minimapPresentationS(self, options):
        if self._isDAAPIInited():
            return self.flashObject.as_minimapPresentation(options)

    def as_minimapVehicleS(self, payload):
        if self._isDAAPIInited():
            return self.flashObject.as_minimapVehicle(payload)

    def as_minimapRangesS(self, payload):
        if self._isDAAPIInited():
            return self.flashObject.as_minimapRanges(payload)

    def as_minimapCameraS(self, strategic):
        if self._isDAAPIInited():
            return self.flashObject.as_minimapCamera(strategic)
