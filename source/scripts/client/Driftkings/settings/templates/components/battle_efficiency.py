# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_EFFICIENCY
from Driftkings.settings.template_schema import control, options
from Driftkings.settings.templates.base import ComponentSettings


class BattleEfficiencySettings(ComponentSettings):
    COMPONENT = BATTLE_EFFICIENCY.ID

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        x_color_key = 'UI_setting_colorRatting_'
        x_color_list = ('NoobMeter', 'XVM', 'WotLabs')
        return (
            [
                control(BATTLE_EFFICIENCY.TEXT_LOCK),
                options(BATTLE_EFFICIENCY.COLOR_RATTING, [self.i18n[x_color_key + x] for x in x_color_list]),
                control(BATTLE_EFFICIENCY.FORMAT, 'TextInput', 400)
            ],
            [
                control(BATTLE_EFFICIENCY.BATTLE_RESULTS_WINDOW),
                control(BATTLE_EFFICIENCY.BATTLE_RESULTS_FORMAT, 'TextInput', 400)
            ]
        )
