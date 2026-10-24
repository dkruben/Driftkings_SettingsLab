# -*- coding: utf-8 -*-
from driftkings.common.utils.colorratting import color_tables
from driftkings.core.profile_ratings import parse_thresholds
from driftkings.settings.controls_schema import control, options
from driftkings.settings.definitions.base import SectionDefinition


class ProfileRatingsSettings(SectionDefinition):
    NAME = 'profile_ratings'

    def normalize_loaded(self, values):
        for key, limit, fallback in (('survivalThresholds', 100, '20, 30, 40, 50, 60'),
                                     ('receivedDamageThresholds', 500, '25, 50, 75, 100, 125')):
            try:
                parse_thresholds(values[key], limit)
            except (ValueError, TypeError):
                values[key] = fallback
        values['colorScale'] = max(0, min(len(color_tables) - 1, int(values['colorScale'])))
        return values

    def normalize_changes(self, values, changes):
        for key, limit in (('survivalThresholds', 100), ('receivedDamageThresholds', 500)):
            if key in changes:
                parse_thresholds(values[key], limit)
        return self.normalize_loaded(values)

    def getControlColumns(self):
        return ([control('summaryColors'), control('statisticsColors'), control('vehicleColors'),
                 options('colorScale', [table['ScaleColor'] for table in color_tables]),
                 control('colorSurvival'), control('survivalThresholds', 'TextInput', 260)],
                [control('showPlayerWN8'), control('showVehicleWN8'), control('showUnavailableWN8'),
                 control('colorReceivedDamage'), control('receivedDamageThresholds', 'TextInput', 260)])
