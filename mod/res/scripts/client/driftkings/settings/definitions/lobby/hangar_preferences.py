# -*- coding: utf-8 -*-
from driftkings._constants import HANGAR_PREFERENCES
from driftkings.settings.controls_schema import control, slider
from driftkings.settings.definitions.base import SectionDefinition


class HangarPreferencesSettings(SectionDefinition):
    NAME = HANGAR_PREFERENCES.NAME

    TRANSLATED_TITLE = True

    def normalize_loaded(self, values):
        # Retired presets and the clock, which moved to the main section.
        for key in ('clockStyle', 'clockSeconds', 'clock24Hour', 'customClockFormat', 'text', 'panel',
                    'clock', 'clockBackground', 'clockX', 'clockY', 'clockScale', 'customClockText'):
            values.pop(key, None)
        return values

    def normalize_changes(self, values, changes):
        return self.normalize_loaded(values)

    def getControlColumns(self):
        return (
            [
                control(HANGAR_PREFERENCES.AUTO_LOGIN),
                control(HANGAR_PREFERENCES.ALLOW_EXCHANGE_XPIN_TECH_TREE),
                control(HANGAR_PREFERENCES.ALLOW_CHANNEL_BUTTON_BLINKING),
                control(HANGAR_PREFERENCES.SHOW_XP_TO_UNLOCK_VEH),
                control(HANGAR_PREFERENCES.BLOCK_VEHICLE_IF_LOW_AMMO),
                slider(HANGAR_PREFERENCES.LOW_AMMO_PERCENTAGE, 0, 100, 1, '{{value}}%'),
                control(HANGAR_PREFERENCES.SHOW_BATTLE_COUNT),
                control(HANGAR_PREFERENCES.SHOW_BUTTON),
                control(HANGAR_PREFERENCES.SHOW_GENERAL_CHAT_BUTTON),
                control(HANGAR_PREFERENCES.SHOW_POP_UP_MESSAGES),
                control(HANGAR_PREFERENCES.LOOT_BOXES_WIDGET),
                control(HANGAR_PREFERENCES.SHOW_DAILY_QUEST_WIDGET),
                control(HANGAR_PREFERENCES.SHOW_EVENT_BANNER),
                control(HANGAR_PREFERENCES.SHOW_EVENT_TOURNAMENT_WIDGET),
                control(HANGAR_PREFERENCES.SHOW_PROGRESSIVE_DECALS_WINDOW),
                control(HANGAR_PREFERENCES.SHOW_BATTLE_PASS_WIDGET)
            ],
            [
                control(HANGAR_PREFERENCES.SHOW_PROMO_PREM_VEHICLE),
                control(HANGAR_PREFERENCES.SHOW_UNREAD_COUNTER),
                control(HANGAR_PREFERENCES.SHOW_BUTTON_COUNTERS),
                control(HANGAR_PREFERENCES.HIDE_BTN_COUNTERS),
                control(HANGAR_PREFERENCES.SHOW_RANKED_BATTLE_RESULTS),
                control(HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET),
                control(HANGAR_PREFERENCES.SHOW_PROFILE_PRESTIGE_WIDGET),
                control(HANGAR_PREFERENCES.SHOW_ACHIEVEMENT_POPUPS),
                control(HANGAR_PREFERENCES.SHOW_ACHIEVEMENT_REWARD_WINDOW),
                control(HANGAR_PREFERENCES.FIELD_MAIL),
                control('showBuyPremiumButton'),
                control('showPremiumShopButton'),
                control('showReferralButton'),
                control('showWotPlusButton'),
                control('premiumTime'),
            ]
        )
