# -*- coding: utf-8 -*-
from .base import HudMeta


class DistanceMarkerMeta(HudMeta):
    FLASH_CLASS = 'driftkings.battle.components.distance_marker.DistanceMarkerUI'

    def as_applyConfigS(self, config):
        if self._isDAAPIInited():
            return self.flashObject.as_applyConfig(config)

    def as_isPointInMarkerS(self, x, y):
        if self._isDAAPIInited():
            return self.flashObject.as_isPointInMarker(x, y)

    def py_requestFrameData(self):
        raise NotImplementedError
