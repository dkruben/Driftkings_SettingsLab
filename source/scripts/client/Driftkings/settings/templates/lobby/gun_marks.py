# -*- coding: utf-8 -*-
from Driftkings._constants import MARKS_ON_GUN_HANGAR
from Driftkings.settings.template_schema import control, metadata, options, slider
from Driftkings.settings.templates.base import ComponentSettings


class MarksOnGunHangarSettings(ComponentSettings):
    COMPONENT = MARKS_ON_GUN_HANGAR.ID

    TRANSLATED_TITLE = False

    def onApplySettings(self, settings):
        settings = dict(settings)
        panel = dict(settings.get(MARKS_ON_GUN_HANGAR.PANEL, self.data[MARKS_ON_GUN_HANGAR.PANEL]))
        for setting, axis in (('positionX', 'x'), ('positionY', 'y')):
            if setting in settings:
                panel[axis] = float(settings.pop(setting))
        settings[MARKS_ON_GUN_HANGAR.PANEL] = panel
        super(MarksOnGunHangarSettings, self).onApplySettings(settings)

    def getControlColumns(self):
        x_color_key = 'UI_setting_colorRating_'
        x_color_list = ('NoobMeter', 'XVM', 'WotLabs')
        return (
            [
                control(MARKS_ON_GUN_HANGAR.SHOW_IN_HANGAR),
                control(MARKS_ON_GUN_HANGAR.SHOW_IN_STATISTIC),
                options(MARKS_ON_GUN_HANGAR.GOAL_SELECTION, [self.i18n['UI_panel_' + key] for key in ('automatic', 'goal1', 'goal2', 'goal3')]),
                control(MARKS_ON_GUN_HANGAR.COMPACT_MODE),
                options(MARKS_ON_GUN_HANGAR.COLOR_RATING, [self.i18n[x_color_key + x] for x in x_color_list])
            ],
            [
                control(MARKS_ON_GUN_HANGAR.SHOW_TOOLTIP_TARGETS),
                control(MARKS_ON_GUN_HANGAR.TEXT_LOCK),
                slider(MARKS_ON_GUN_HANGAR.HISTORY_BATTLES, 1, 20, 1),
                metadata(slider('positionX', -7680, 7680, 1, value=self.data[MARKS_ON_GUN_HANGAR.PANEL]['x']), path=[MARKS_ON_GUN_HANGAR.PANEL, 'x']),
                metadata(slider('positionY', -4320, 4320, 1, value=self.data[MARKS_ON_GUN_HANGAR.PANEL]['y']), path=[MARKS_ON_GUN_HANGAR.PANEL, 'y'])
            ]
        )
