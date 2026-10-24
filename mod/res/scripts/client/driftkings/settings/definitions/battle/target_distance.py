# -*- coding: utf-8 -*-
import copy

from driftkings._constants import TARGET_DISTANCE
from driftkings.settings.controls_schema import control, options, slider
from driftkings.settings.definitions.base import SectionDefinition


class TargetDistanceSettings(SectionDefinition):
    NAME = TARGET_DISTANCE.NAME

    TRANSLATED_TITLE = True
    COLUMNS = (
        (
            options(TARGET_DISTANCE.DISPLAY_MODE, ['always', 'onAltPressed']),
            options(TARGET_DISTANCE.MARKER_TARGET, ['allyAndEnemy', 'onlyEnemy']),
            options(TARGET_DISTANCE.ANCHOR_POSITION, ['tankMarker', 'tankCenter', 'tankBottom']),
            control(TARGET_DISTANCE.LOCK_POSITION_OFFSETS),
            slider(TARGET_DISTANCE.ANCHOR_HORIZONTAL_OFFSET, -150, 150, 1),
            slider(TARGET_DISTANCE.ANCHOR_VERTICAL_OFFSET, -150, 150, 1),
        ),
        (
            slider(TARGET_DISTANCE.DECIMAL_PRECISION, 0, 3, 1),
            slider(TARGET_DISTANCE.TEXT_SIZE, 6, 24, 1),
            control(TARGET_DISTANCE.TEXT_COLOR, 'ColorChoice'),
            slider(TARGET_DISTANCE.TEXT_ALPHA, 0.0, 1.0, 0.01),
            control(TARGET_DISTANCE.DRAW_TEXT_SHADOW),
        ),
    )

    def getControlColumns(self):
        columns = copy.deepcopy(self.COLUMNS)
        for column in columns:
            for item in column:
                for option in item.get('options', []):
                    key = 'UI_setting_' + item['varName'] + '_' + option['label']
                    option['label'] = self.i18n[key]
        return columns
