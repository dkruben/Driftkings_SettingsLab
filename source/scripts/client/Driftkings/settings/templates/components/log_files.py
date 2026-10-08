# -*- coding: utf-8 -*-
from Driftkings._constants import LOGS_SWAPPER
from Driftkings.settings.template_schema import control
from Driftkings.settings.templates.base import ComponentSettings


class LogsSwapperSettings(ComponentSettings):
    COMPONENT = LOGS_SWAPPER.ID

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            control(LOGS_SWAPPER.LOG_SWAPPER),
            control(LOGS_SWAPPER.WG_LOG_HIDE_CRITICS),
            control(LOGS_SWAPPER.WG_LOG_HIDE_BLOCK),
            control(LOGS_SWAPPER.WG_LOG_HIDE_ASSIST),
        ),
        (
        ),
    )
