# -*- coding: utf-8 -*-
from Driftkings._constants import MAIN_GUN
from Driftkings.settings.template_schema import control
from Driftkings.settings.templates.base import ComponentSettings


class MainGunSettings(ComponentSettings):
    COMPONENT = MAIN_GUN.ID

    TRANSLATED_TITLE = False
    COLUMNS = (
        (
            control(MAIN_GUN.BACK_GROUND_ENABLED),
            control(MAIN_GUN.TEXT_LOCK),
        ),
        (
        ),
    )
