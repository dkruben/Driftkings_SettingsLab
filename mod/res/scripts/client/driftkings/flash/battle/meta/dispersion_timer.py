# -*- coding: utf-8 -*-
from driftkings.flash.battle.meta.base import CrosshairMeta


class DispersionTimerMeta(CrosshairMeta):
    FLASH_CLASS = 'driftkings.battle.components.dispersion_timer.dispersiontimerui'

    def as_updateTimerTextS(self, text):
        return self._sendChanged('as_updateTimerText', text)
