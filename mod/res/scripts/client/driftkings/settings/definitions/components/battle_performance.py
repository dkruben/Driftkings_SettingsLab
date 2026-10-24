# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_PERFORMANCE
from driftkings.settings.controls_schema import control, options
from driftkings.settings.definitions.base import SectionDefinition


class BattlePerformanceSettings(SectionDefinition):
    NAME = BATTLE_PERFORMANCE.NAME

    TRANSLATED_TITLE = True


    def getControlColumns(self):
        x_color_key = 'UI_setting_colorRatting_'
        x_color_list = ('NoobMeter', 'XVM', 'WotLabs')
        return (
            [
                control(BATTLE_PERFORMANCE.TEXT_LOCK),
                options(BATTLE_PERFORMANCE.COLOR_RATTING, [self.i18n[x_color_key + x] for x in x_color_list]),
                control(BATTLE_PERFORMANCE.FORMAT, 'TextInput', 400)
            ],
            [
                control(BATTLE_PERFORMANCE.BATTLE_RESULTS_WINDOW),
                control(BATTLE_PERFORMANCE.BATTLE_RESULTS_FORMAT, 'TextInput', 400)
            ]
        )
