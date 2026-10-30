# -*- coding: utf-8 -*-
from driftkings._constants import HANGAR_MARKS_OF_EXCELLENCE
from driftkings.common.utils.colorratting import color_tables
from driftkings.settings.controls_schema import control, field, options, slider
from driftkings.settings.definitions.base import SectionDefinition


class HangarMarksOfExcellenceSettings(SectionDefinition):
    NAME = HANGAR_MARKS_OF_EXCELLENCE.NAME

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        x_color_key = 'UI_setting_colorRating_'
        x_color_list = [table['ScaleColor'] for table in color_tables]
        # The card follows the native mission column, so it has no position, scale or colour settings;
        # the gameface.* switches choose what the "show more" panel lists.
        return (
            [
                control(HANGAR_MARKS_OF_EXCELLENCE.SHOW_IN_HANGAR),
                control(HANGAR_MARKS_OF_EXCELLENCE.SHOW_IN_STATISTIC),
                control(HANGAR_MARKS_OF_EXCELLENCE.SHOW_TOOLTIP_TARGETS),
                options(HANGAR_MARKS_OF_EXCELLENCE.GOAL_SELECTION, [self.i18n['UI_panel_' + key] for key in ('automatic', 'goal1', 'goal2', 'goal3')]),
                options(HANGAR_MARKS_OF_EXCELLENCE.COLOR_RATING, [self.i18n.get(x_color_key + x, x) for x in x_color_list]),
                slider(HANGAR_MARKS_OF_EXCELLENCE.HISTORY_BATTLES, 1, 20, 1)
            ],
            [
                field([HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE, 'showVehicleInfo'], self.i18n['UI_mog_vehicle']),
                field([HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE, 'showProgress'], self.i18n['UI_mog_progress']),
                field([HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE, 'showMilestones'], self.i18n['UI_mog_milestones']),
                field([HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE, 'showDamageStatistics'], self.i18n['UI_mog_damage']),
                field([HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE, 'showHistory'], self.i18n['UI_mog_history']),
                field([HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE, 'showAdvancedStatistics'], self.i18n['UI_mog_advanced'])
            ]
        )
