# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_OPTIONS, GLOBAL
from Driftkings.settings.template_schema import color, control, slider
from Driftkings.settings.templates.base import ComponentSettings


class BattleOptionsSettings(ComponentSettings):
    COMPONENT = BATTLE_OPTIONS.ID

    TRANSLATED_TITLE = False

    def getControlColumns(self):
        colorLabel = color(GLOBAL.COLOR, 'colorCheck')

        return (
            [
                control(BATTLE_OPTIONS.SHOW_BATTLE_HINT),
                control(BATTLE_OPTIONS.SHOW_POSTMORTEM_DOG_TAG),
                control(BATTLE_OPTIONS.STUN_SOUND),
                control(BATTLE_OPTIONS.SHOW_ANONYMOUS),
                control(BATTLE_OPTIONS.HIDE_CLAN_NAME),
                control(BATTLE_OPTIONS.HIDE_BADGES),
                control(BATTLE_OPTIONS.HIDE_BATTLE_PRESTIGE),
                slider(BATTLE_OPTIONS.MAX_CHAT_LINES, 1, 15, 1, '{{value}} Lines'),
                control(BATTLE_OPTIONS.MUTE_TEAM_BASE_SOUND),
                control(BATTLE_OPTIONS.POSTMORTEM_TIPS)
            ],
            [
                colorLabel,
                control(BATTLE_OPTIONS.SHOW_PLAYER_SATISFACTION_WIDGET),
                control(BATTLE_OPTIONS.ADD_ENEMY_NAME),
                control(BATTLE_OPTIONS.IN_BATTLE),
                control(BATTLE_OPTIONS.DISABLE_SOUND_COMMANDER),
                control(BATTLE_OPTIONS.DIRECTIVES_ONLY_FROM_STORAGE),
                control(BATTLE_OPTIONS.SHOW_FRIENDS),
                control(BATTLE_OPTIONS.CLIP_LOAD),
                control(BATTLE_OPTIONS.HIDE_HINT),
                control(BATTLE_OPTIONS.LOAD_TXT, 'TextInput', 300)
            ]
        )
