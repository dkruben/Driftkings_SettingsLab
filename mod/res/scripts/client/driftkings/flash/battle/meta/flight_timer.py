# -*- coding: utf-8 -*-
from driftkings.flash.battle.meta.base import CrosshairMeta


class FlightTimeMeta(CrosshairMeta):
    FLASH_CLASS = 'driftkings.battle.components.flight_timer.flighttimerui'

    def as_flightTimeS(self, text):
        return self._sendChanged('as_flightTime', text)
