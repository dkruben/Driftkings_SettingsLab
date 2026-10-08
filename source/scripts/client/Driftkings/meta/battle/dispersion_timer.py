# -*- coding: utf-8 -*-
from .base import CrosshairMeta


class DispersionTimerMeta(CrosshairMeta):
    FLASH_CLASS = 'driftkings.battle.components.dispersion_timer.DispersionTimerUI'

    def as_updateTimerTextS(self, text):
        if self._isDAAPIInited():
            return self.flashObject.as_updateTimerText(text)
