# -*- coding: utf-8 -*-
from .base import CrosshairMeta


class FlightTimeMeta(CrosshairMeta):
    FLASH_CLASS = 'driftkings.battle.components.flight_timer.FlightTimerUI'

    def as_flightTimeS(self, text):
        if self._isDAAPIInited():
            return self.flashObject.as_flightTime(text)
