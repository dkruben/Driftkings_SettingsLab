# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_MARKS_OF_EXCELLENCE
from driftkings.common.utils.colorratting import color_tables
from driftkings.settings.controls_schema import control, hotkey, options, field
from driftkings.settings.definitions.base import SectionDefinition


class BattleMarksOfExcellenceSettings(SectionDefinition):
    NAME = BATTLE_MARKS_OF_EXCELLENCE.NAME

    TRANSLATED_TITLE = True

    def normalize_changes(self, values, changes):
        panel = values.get(BATTLE_MARKS_OF_EXCELLENCE.PANEL)
        if panel is not None:
            for key in ('x', 'y', 'alpha', 'height', 'width'):
                if key in panel:
                    panel[key] = float(panel[key])
        return values

    def getControlColumns(self):
        return (
            [
                options(BATTLE_MARKS_OF_EXCELLENCE.COLOR_RATING, [table['ScaleColor'] for table in color_tables]),
                field([BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, 'enabled'], self.i18n['UI_mog_enableBattle']),
                field([BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, 'miniMode'], self.i18n['UI_mog_miniMode']),
                control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_MARKS), control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_DELTA), control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_DAMAGE),
                control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_PROGRESS), control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_TARGETS),
                control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_STATISTIC),
                control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_REPLAY),
                field([BATTLE_MARKS_OF_EXCELLENCE.REPLAY_BASE_PERCENT], self.i18n['UI_mog_replayBasePercent'], 'Slider', 0.0, 100.0, step=0.5),
                field([BATTLE_MARKS_OF_EXCELLENCE.REPLAY_BASE_DAMAGE], self.i18n['UI_mog_replayBaseDamage'], 'Slider', 100, 15000, step=50),
                control(BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_BATTLE),
                control(BATTLE_MARKS_OF_EXCELLENCE.BACKGROUND),
            ],
            [
                field([BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, 'locked'], self.i18n['UI_mog_lockPosition']),
                field(['panel', 'x'], 'X', 'Slider', -7680.0, 7680.0, step=1.0),
                field(['panel', 'y'], 'Y', 'Slider', -4320.0, 4320.0, step=1.0),
                field([BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT], self.i18n['UI_mog_scale'], 'Slider', 10, 1000, step=10),
                field([BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, 'backgroundOpacity'], self.i18n['UI_mog_opacity'], 'Slider', 0.0, 1.0, step=0.05),
                field([BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, 'accentColor'], self.i18n['UI_mog_accent'], 'ColorChoice'),
                field([BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, 'showTargetDamage'], self.i18n['UI_mog_target']),
                field([BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, 'showRequiredDamage'], self.i18n['UI_mog_needed']),
                hotkey(BATTLE_MARKS_OF_EXCELLENCE.BUTTON_RESET),
                hotkey(BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_UP),
                hotkey(BATTLE_MARKS_OF_EXCELLENCE.BUTTON_SIZE_DOWN)
            ]
        )
