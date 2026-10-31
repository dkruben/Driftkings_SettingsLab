# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_STATISTICS
from driftkings.common.utils.colorratting import color_tables
from driftkings.settings.controls_schema import control, options
from driftkings.settings.definitions.base import SectionDefinition


class BattleStatisticsSettings(SectionDefinition):
    NAME = BATTLE_STATISTICS.NAME

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            control(BATTLE_STATISTICS.TEXT_LOCK),
            options(BATTLE_STATISTICS.COLOR_RATING, [table['ScaleColor'] for table in color_tables]),
            control(BATTLE_STATISTICS.FORMAT, 'TextInput', width=300),
        ),
        (
        ),
    )
