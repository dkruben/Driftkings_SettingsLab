# -*- coding: utf-8 -*-
from Driftkings._constants import ARMOR_CALCULATOR
from Driftkings.settings.template_schema import control
from Driftkings.settings.templates.base import ComponentSettings


class ArmorCalculatorSettings(ComponentSettings):
    COMPONENT = ARMOR_CALCULATOR.ID

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            control(ARMOR_CALCULATOR.DISPLAY_ON_ALLIES),
        ),
        (
        ),
    )
