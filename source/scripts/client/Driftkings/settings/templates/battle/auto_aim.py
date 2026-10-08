# -*- coding: utf-8 -*-
from Driftkings._constants import AUTO_AIM_OPTIMIZE
from Driftkings.settings.template_schema import control, slider
from Driftkings.settings.templates.base import ComponentSettings


class AutoAimOptimizeSettings(ComponentSettings):
    COMPONENT = AUTO_AIM_OPTIMIZE.ID

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        return (
            [
                slider(AUTO_AIM_OPTIMIZE.ANGLE, 0, 90.0, 0.1, '{{value}}%s' % self.i18n['UI_setting_angle_value'])
            ],
            [
                control(AUTO_AIM_OPTIMIZE.CATCH_HIDDEN_TARGET),
                control(AUTO_AIM_OPTIMIZE.DISABLE_ARTY_MODE)
            ]
        )
