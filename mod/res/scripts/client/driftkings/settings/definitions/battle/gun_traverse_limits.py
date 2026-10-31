# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, GUN_TRAVERSE_LIMITS
from driftkings.settings.controls_schema import options
from driftkings.settings.definitions.base import SectionDefinition


class GunTraverseLimitsSettings(SectionDefinition):
    NAME = GUN_TRAVERSE_LIMITS.NAME

    TRANSLATED_TITLE = True

    def normalize_loaded(self, values):
        if not values.get(GUN_TRAVERSE_LIMITS.HORIZONTAL) and not values.get(GUN_TRAVERSE_LIMITS.VERTICAL):
            values[GLOBAL.ENABLED] = False
        return values

    def normalize_changes(self, values, changes):
        return self.normalize_loaded(values)

    def getControlColumns(self):
        columns = (
            [
                options(GUN_TRAVERSE_LIMITS.HORIZONTAL, [self.i18n['UI_setting_horizontal_%s' % i] for i in xrange(7)], 'RadioButtonGroup')
            ],
            [
                options(GUN_TRAVERSE_LIMITS.VERTICAL, [self.i18n['UI_setting_vertical_%s' % i] for i in xrange(7)], 'RadioButtonGroup')
            ]
        )
        for column, direction in zip(columns, ('left', 'top')):
            item = column[0]
            item['previewImage'] = True
            for index, option in enumerate(item['options']):
                option['image'] = 'gui/aimingangles/%s/%s.png' % (index, direction) if index else ''
        return columns
