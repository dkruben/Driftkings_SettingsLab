# -*- coding: utf-8 -*-
from Driftkings._constants import FLIGHT_TIMER, GLOBAL
from Driftkings.settings.template_schema import control, slider
from Driftkings.settings.templates.base import ComponentSettings


class FlightTimerSettings(ComponentSettings):
    COMPONENT = FLIGHT_TIMER.ID

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            control(FLIGHT_TIMER.TEMPLATE, 'TextInput', 400),
            control(FLIGHT_TIMER.SPG_ONLY),
        ),
        (
            slider(GLOBAL.X, -2000, 2000, 1, '{{value}}%s' % ' X'),
            slider(GLOBAL.Y, -2000, 2000, 1, '{{value}}%s' % ' Y'),
        ),
    )
