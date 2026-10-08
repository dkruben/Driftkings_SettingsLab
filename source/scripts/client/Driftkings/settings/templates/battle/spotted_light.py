# -*- coding: utf-8 -*-
from Driftkings._constants import SPOTTED_EXTENDED_LIGHT
from Driftkings.settings.template_schema import color, control, slider
from Driftkings.settings.templates.base import ComponentSettings


class SpottedExtendedLightSettings(ComponentSettings):
    COMPONENT = SPOTTED_EXTENDED_LIGHT.ID

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        xColorSpotted = color(SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_SPOTTED, 'messageColorSpottedCheck')
        xColorAssistRadio = color(SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_RADIO, 'messageColorAssistRadioCheck')
        xColorAssistTrack = color(SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_TRACK, 'messageColorAssistTrackCheck')
        xColorAssistStun = color(SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_STUN, 'messageColorAssistStunCheck')
        return (
            [
                control(SPOTTED_EXTENDED_LIGHT.SOUND),
                slider(SPOTTED_EXTENDED_LIGHT.ICON_SIZE_X, 5.0, 150.0, 1.0, '{{value}}%s' % self.i18n['UI_setting_iconSizeX_value']),
                slider(SPOTTED_EXTENDED_LIGHT.ICON_SIZE_Y, 5.0, 150.0, 1.0, '{{value}}%s' % self.i18n['UI_setting_iconSizeY_value'])
            ],
            [
                xColorSpotted,
                control(SPOTTED_EXTENDED_LIGHT.SPOTTED, 'TextInput', 300),
                xColorAssistRadio,
                control(SPOTTED_EXTENDED_LIGHT.ASSIST_RADIO, 'TextInput', 300),
                xColorAssistTrack,
                control(SPOTTED_EXTENDED_LIGHT.ASSIST_TRACK, 'TextInput', 300),
                xColorAssistStun,
                control(SPOTTED_EXTENDED_LIGHT.ASSIST_STUN, 'TextInput', 300)
            ]
        )
