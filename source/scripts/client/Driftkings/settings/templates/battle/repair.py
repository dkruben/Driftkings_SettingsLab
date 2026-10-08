# -*- coding: utf-8 -*-
from Driftkings._constants import REPAIR_EXTENDED
from Driftkings.settings.template_schema import control, hotkey, slider
from Driftkings.settings.templates.base import ComponentSettings


class RepairExtendedSettings(ComponentSettings):
    COMPONENT = REPAIR_EXTENDED.ID

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        xMin = self.i18n['UI_setting_timerMin_format']
        xMax = self.i18n['UI_setting_timerMax_format']
        return (
            [
                hotkey(REPAIR_EXTENDED.BUTTON_CHASSIS),
                hotkey(REPAIR_EXTENDED.BUTTON_REPAIR),
                control(REPAIR_EXTENDED.USE_GOLD_KITS),
                control(REPAIR_EXTENDED.AUTO_REPAIR),
                slider(REPAIR_EXTENDED.TIMER_MIN, 0.1, 0.5, 0.1, '{{value}}%s' % xMin),
                slider(REPAIR_EXTENDED.TIMER_MAX, 0.6, 3.0, 0.1, '{{value}}%s' % xMax)
            ],
            [
                control(REPAIR_EXTENDED.RESTORE_CHASSIS),
                control(REPAIR_EXTENDED.REMOVE_STUN),
                control(REPAIR_EXTENDED.EXTINGUISH_FIRE),
                control(REPAIR_EXTENDED.HEAL_CREW),
                control(REPAIR_EXTENDED.REPAIR_DEVICES)
            ]
        )
