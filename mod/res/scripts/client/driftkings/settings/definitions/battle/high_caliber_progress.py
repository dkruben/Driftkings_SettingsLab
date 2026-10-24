# -*- coding: utf-8 -*-
from driftkings._constants import HIGH_CALIBER_PROGRESS
from driftkings.settings.controls_schema import control, field
from driftkings.settings.definitions.base import SectionDefinition


class HighCaliberProgressSettings(SectionDefinition):
    NAME = HIGH_CALIBER_PROGRESS.NAME

    TRANSLATED_TITLE = True


    def getControlColumns(self):
        labels = self.i18n
        return ([
            field(['mainGun', 'dynamic'], labels['UI_hc_dynamic']),
            control(HIGH_CALIBER_PROGRESS.BACK_GROUND_ENABLED),
            field(['textLock'], labels['UI_hc_lock']),
            field(['textPosition', 'x'], 'X', 'Slider', -7680, 7680),
            field(['textPosition', 'y'], 'Y', 'Slider', -4320, 4320),
        ], [
            field(['gameface', 'scale'], labels['UI_hc_scale'], 'Slider', 0.5, 3.0, step=0.05),
            field(['background', 'alpha'], labels['UI_hc_opacity'], 'Slider', 0, 100),
            field(['gameface', 'accentColor'], labels['UI_hc_accent'], 'ColorChoice'),
            field(['gameface', 'showPercentage'], labels['UI_hc_percentage']),
            field(['gameface', 'showProgress'], labels['UI_hc_bar']),
            field(['gameface', 'showSecondary'], labels['UI_hc_secondary']),
        ])
