# -*- coding: utf-8 -*-
from driftkings._constants import ENEMY_SPOTTING_STATUS
from driftkings.settings.controls_schema import color, control, slider
from driftkings.settings.definitions.base import SectionDefinition


class EnemySpottingStatusSettings(SectionDefinition):
    NAME = ENEMY_SPOTTING_STATUS.NAME

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        xColorSpotted = color(ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_SPOTTED, 'messageColorSpottedCheck')
        xColorAssistRadio = color(ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_ASSIST_RADIO, 'messageColorAssistRadioCheck')
        xColorAssistTrack = color(ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_ASSIST_TRACK, 'messageColorAssistTrackCheck')
        xColorAssistStun = color(ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_ASSIST_STUN, 'messageColorAssistStunCheck')
        return (
            [
                control(ENEMY_SPOTTING_STATUS.SOUND),
                slider(ENEMY_SPOTTING_STATUS.ICON_SIZE_X, 5.0, 150.0, 1.0,
                       '{{value}}%s' % self.i18n['UI_setting_iconSizeX_value']),
                slider(ENEMY_SPOTTING_STATUS.ICON_SIZE_Y, 5.0, 150.0, 1.0,
                       '{{value}}%s' % self.i18n['UI_setting_iconSizeY_value'])
            ],
            [
                xColorSpotted,
                control(ENEMY_SPOTTING_STATUS.SPOTTED, 'TextInput', 300),
                xColorAssistRadio,
                control(ENEMY_SPOTTING_STATUS.ASSIST_RADIO, 'TextInput', 300),
                xColorAssistTrack,
                control(ENEMY_SPOTTING_STATUS.ASSIST_TRACK, 'TextInput', 300),
                xColorAssistStun,
                control(ENEMY_SPOTTING_STATUS.ASSIST_STUN, 'TextInput', 300)
            ]
        )
