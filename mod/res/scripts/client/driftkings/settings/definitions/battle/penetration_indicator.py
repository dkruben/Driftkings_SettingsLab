# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, PENETRATION_INDICATOR
from driftkings.settings.controls_schema import control, metadata, slider
from driftkings.settings.definitions.base import SectionDefinition

# Offset of the text from the crosshair, in interface units; the battle text can also be dragged with Ctrl.
POSITION_SLIDERS = (('positionX', GLOBAL.X), ('positionY', GLOBAL.Y))


class PenetrationIndicatorSettings(SectionDefinition):
    NAME = PENETRATION_INDICATOR.NAME

    TRANSLATED_TITLE = True

    def normalize_changes(self, values, changes):
        position = values[PENETRATION_INDICATOR.POSITION]
        for setting, axis in POSITION_SLIDERS:
            if setting in changes:
                position[axis] = int(values.pop(setting))
        return values

    def getControlColumns(self):
        # The panel reads and writes each slider through its path inside the position object.
        return (
            [
                control(PENETRATION_INDICATOR.DISPLAY_ON_ALLIES),
                control(PENETRATION_INDICATOR.TEMPLATE, 'TextInput', 400)
            ],
            [metadata(slider(setting, -2000, 2000, 1, '{{value}} ' + axis.upper()),
                      path=[PENETRATION_INDICATOR.POSITION, axis])
             for setting, axis in POSITION_SLIDERS]
        )
