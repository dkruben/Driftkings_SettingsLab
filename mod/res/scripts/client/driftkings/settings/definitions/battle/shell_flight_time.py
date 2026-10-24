# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, SHELL_FLIGHT_TIME
from driftkings.settings.controls_schema import control, slider
from driftkings.settings.definitions.base import SectionDefinition


class ShellFlightTimeSettings(SectionDefinition):
    NAME = SHELL_FLIGHT_TIME.NAME

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            control(SHELL_FLIGHT_TIME.TEMPLATE, 'TextInput', 400),
            control(SHELL_FLIGHT_TIME.SPG_ONLY),
        ),
        (
            slider(GLOBAL.X, -2000, 2000, 1, '{{value}}%s' % ' X'),
            slider(GLOBAL.Y, -2000, 2000, 1, '{{value}}%s' % ' Y'),
        ),
    )
