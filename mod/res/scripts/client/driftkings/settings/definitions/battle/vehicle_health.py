# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, VEHICLE_HEALTH
from driftkings.settings.controls_schema import field, options, slider
from driftkings.settings.definitions.base import SectionDefinition


class VehicleHealthSettings(SectionDefinition):
    NAME = VEHICLE_HEALTH.NAME

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            slider(GLOBAL.X, -2000, 2000, 1, '{{value}}%s' % ' px'),
            slider(GLOBAL.Y, -2000, 2000, 1, '{{value}}%s' % ' px'),
        ),
        (
        ),
    )

    def getControlColumns(self):
        labels = self.i18n
        columns = [list(column) for column in self.COLUMNS]
        columns[0].insert(0, options(VEHICLE_HEALTH.STYLE,
                                   [labels['UI_health_' + name] for name in VEHICLE_HEALTH.STYLES]))
        for key in ('saturation', 'brightness'):
            columns[1].append(field([VEHICLE_HEALTH.AVG_COLOR, key], labels['UI_health_' + key],
                                    'Slider', 0.0, 1.0, step=0.05,
                                    tooltip=labels['UI_health_color_tooltip']))
        return columns

    def normalize_loaded(self, values):
        style = values.get(VEHICLE_HEALTH.STYLE, 0)
        if type(style) is not int or not 0 <= style < len(VEHICLE_HEALTH.STYLES):
            style = 0
        values[VEHICLE_HEALTH.STYLE] = style
        return values

    def normalize_changes(self, values, changes):
        style = values.get(VEHICLE_HEALTH.STYLE, 0)
        if type(style) is not int or not 0 <= style < len(VEHICLE_HEALTH.STYLES):
            raise ValueError('Unknown vehicle health style')
        return values
