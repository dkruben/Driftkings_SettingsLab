# -*- coding: utf-8 -*-
from Driftkings._constants import HANGAR_OPTIONS
from Driftkings.settings.template_schema import control, options, slider
from Driftkings.settings.templates.base import ComponentSettings


class HangarOptionsSettings(ComponentSettings):
    COMPONENT = HANGAR_OPTIONS.ID

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        return (
            [
                control(HANGAR_OPTIONS.AUTO_LOGIN),
                control(HANGAR_OPTIONS.CLOCK),
                options(HANGAR_OPTIONS.CLOCK_STYLE, [self.i18n['UI_clock_' + key] for key in ('minimal', 'digital', 'analog', 'flip', HANGAR_OPTIONS.PANEL)]),
                slider(HANGAR_OPTIONS.CLOCK_X, -3840, 3840, 1),
                slider(HANGAR_OPTIONS.CLOCK_Y, -2160, 2160, 1),
                slider(HANGAR_OPTIONS.CLOCK_SCALE, 50, 200, 5),
                control(HANGAR_OPTIONS.CLOCK_SECONDS),
                control(HANGAR_OPTIONS.CLOCK24_HOUR),
                control(HANGAR_OPTIONS.ALLOW_EXCHANGE_XPIN_TECH_TREE),
                control(HANGAR_OPTIONS.ALLOW_CHANNEL_BUTTON_BLINKING),
                control(HANGAR_OPTIONS.SHOW_XP_TO_UNLOCK_VEH),
                control(HANGAR_OPTIONS.BLOCK_VEHICLE_IF_LOW_AMMO),
                slider(HANGAR_OPTIONS.LOW_AMMO_PERCENTAGE, 0, 100, 1, '{{value}}%'),
                control(HANGAR_OPTIONS.SHOW_BATTLE_COUNT),
                control(HANGAR_OPTIONS.SHOW_BUTTON),
                control(HANGAR_OPTIONS.SHOW_GENERAL_CHAT_BUTTON),
                control(HANGAR_OPTIONS.SHOW_POP_UP_MESSAGES),
                control(HANGAR_OPTIONS.LOOT_BOXES_WIDGET),
                control(HANGAR_OPTIONS.SHOW_DAILY_QUEST_WIDGET),
                control(HANGAR_OPTIONS.SHOW_EVENT_BANNER),
                control(HANGAR_OPTIONS.SHOW_EVENT_TOURNAMENT_WIDGET),
                control(HANGAR_OPTIONS.SHOW_PROGRESSIVE_DECALS_WINDOW),
                control(HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET)
            ],
            [
                control(HANGAR_OPTIONS.SHOW_PROMO_PREM_VEHICLE),
                control(HANGAR_OPTIONS.SHOW_UNREAD_COUNTER),
                control(HANGAR_OPTIONS.SHOW_BUTTON_COUNTERS),
                control(HANGAR_OPTIONS.HIDE_BTN_COUNTERS),
                control(HANGAR_OPTIONS.SHOW_RANKED_BATTLE_RESULTS),
                control(HANGAR_OPTIONS.SHOW_HANGAR_PRESTIGE_WIDGET),
                control(HANGAR_OPTIONS.SHOW_PROFILE_PRESTIGE_WIDGET),
                control(HANGAR_OPTIONS.SHOW_ACHIEVEMENT_POPUPS),
                control(HANGAR_OPTIONS.SHOW_ACHIEVEMENT_REWARD_WINDOW),
                control(HANGAR_OPTIONS.FIELD_MAIL),
            ]
        )
