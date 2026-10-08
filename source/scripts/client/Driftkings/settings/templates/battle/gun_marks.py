# -*- coding: utf-8 -*-
from Driftkings._constants import MARKS_ON_GUN_BATTLE
from Driftkings.common import color_tables
from Driftkings.settings.template_schema import control, hotkey, options
from Driftkings.settings.templates.base import ComponentSettings


class MarksOnGunBattleSettings(ComponentSettings):
    COMPONENT = MARKS_ON_GUN_BATTLE.ID

    TRANSLATED_TITLE = False

    def onApplySettings(self, settings):
        panel = settings.get(MARKS_ON_GUN_BATTLE.PANEL)
        if panel is not None:
            panel.pop('text', None)
            for key in ('x', 'y', 'alpha', 'height', 'width'):
                if key in panel:
                    panel[key] = float(panel[key])
        super(MarksOnGunBattleSettings, self).onApplySettings(settings)

    def getControlColumns(self):
        UIKey = 'UI_menu_'
        UIList = ('UIConfig', 'UIskill4ltu', 'UIMyp', 'UIspoter', 'UIcircon', 'UIReplay', 'UIReplayDamage', 'UIReplayColor', 'UIReplayColorDamage', 'UIoldskool', 'UIspoterNew', 'UIkorbenDallasNoMercy')
        return (
            [
                options(MARKS_ON_GUN_BATTLE.COLOR_RATING, [table['ScaleColor'] for table in color_tables]),
                control(MARKS_ON_GUN_BATTLE.SHOW_IN_STATISTIC),
                control(MARKS_ON_GUN_BATTLE.SHOW_IN_REPLAY),
                control(MARKS_ON_GUN_BATTLE.SHOW_IN_BATTLE),
                control(MARKS_ON_GUN_BATTLE.BACKGROUND),
                options(MARKS_ON_GUN_BATTLE.UI, [self.i18n[UIKey + x] for x in UIList]),
            ],
            [
                hotkey(MARKS_ON_GUN_BATTLE.BUTTON_SHOW),
                hotkey(MARKS_ON_GUN_BATTLE.BUTTON_RESET),
                hotkey(MARKS_ON_GUN_BATTLE.BUTTON_SIZE_UP),
                hotkey(MARKS_ON_GUN_BATTLE.BUTTON_SIZE_DOWN)
            ]
        )
