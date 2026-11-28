# -*- coding: utf-8 -*-
from driftkings._constants import BATTLE_PREFERENCES, GLOBAL
from driftkings.settings.controls_schema import color, control, slider
from driftkings.settings.definitions.base import SectionDefinition


class BattlePreferencesSettings(SectionDefinition):
    NAME = BATTLE_PREFERENCES.NAME

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        colorLabel = color(GLOBAL.COLOR, 'colorCheck')

        return (
            [
                control(BATTLE_PREFERENCES.REMOVE_FOG),
                control(BATTLE_PREFERENCES.SHOW_BATTLE_HINT),
                control(BATTLE_PREFERENCES.SHOW_POSTMORTEM_DOG_TAG),
                control(BATTLE_PREFERENCES.STUN_SOUND),
                slider(BATTLE_PREFERENCES.MAX_CHAT_LINES, 1, 15, 1, '{{value}} Lines'),
                control(BATTLE_PREFERENCES.MUTE_TEAM_BASE_SOUND),
                control(BATTLE_PREFERENCES.POSTMORTEM_TIPS)
            ],
            [
                colorLabel,
                control(BATTLE_PREFERENCES.SHOW_PLAYER_SATISFACTION_WIDGET),
                control(BATTLE_PREFERENCES.ADD_ENEMY_NAME),
                control(BATTLE_PREFERENCES.IN_BATTLE),
                control(BATTLE_PREFERENCES.DISABLE_SOUND_COMMANDER),
                control(BATTLE_PREFERENCES.DIRECTIVES_ONLY_FROM_STORAGE),
                control(BATTLE_PREFERENCES.SHOW_FRIENDS),
                control(BATTLE_PREFERENCES.CLIP_LOAD),
                control(BATTLE_PREFERENCES.HIDE_HINT)
            ]
        )
