# -*- coding: utf-8 -*-
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from gui.battle_control.controllers import feedback_events
from gui.battle_control.controllers.personal_efficiency_ctrl import _AGGREGATED_DAMAGE_EFFICIENCY_TYPES, _createEfficiencyInfoFromFeedbackEvent

from Driftkings._constants import GLOBAL, SPOTTED_EXTENDED_LIGHT
from Driftkings.common import sendPanelMessage, getPlayer
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.spotted_light import SpottedExtendedLightSettings as Settings

SOUND_LIST = (SPOTTED_EXTENDED_LIGHT.SOUND_SPOTTED, SPOTTED_EXTENDED_LIGHT.SOUND_ASSIST)
GENERATOR = {
    BATTLE_EVENT_TYPE.SPOTTED: ['UI_setting_Spotted_text', SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_SPOTTED, SPOTTED_EXTENDED_LIGHT.SPOTTED],
    BATTLE_EVENT_TYPE.RADIO_ASSIST: ['UI_setting_AssistRadio_text', SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_RADIO, SPOTTED_EXTENDED_LIGHT.ASSIST_RADIO],
    BATTLE_EVENT_TYPE.TRACK_ASSIST: ['UI_setting_AssistTrack_text', SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_TRACK, SPOTTED_EXTENDED_LIGHT.ASSIST_TRACK],
    BATTLE_EVENT_TYPE.STUN_ASSIST: ['UI_setting_AssistStun_text', SPOTTED_EXTENDED_LIGHT.MESSAGE_COLOR_ASSIST_STUN, SPOTTED_EXTENDED_LIGHT.ASSIST_STUN]
}
SUPPORTED_EVENTS = (
    BATTLE_EVENT_TYPE.SPOTTED,
    BATTLE_EVENT_TYPE.RADIO_ASSIST,
    BATTLE_EVENT_TYPE.TRACK_ASSIST,
    BATTLE_EVENT_TYPE.STUN_ASSIST
)


class SpottedLightController(object):
    def __init__(self, config):
        self.config = config
        self.format_str = {}
        self.format_recreate()


    def check_macros(self, macros):
        return any(macros in settings_service.getComponentDict(self.config)[text_type] for text_type in [SPOTTED_EXTENDED_LIGHT.SPOTTED, SPOTTED_EXTENDED_LIGHT.ASSIST_RADIO, SPOTTED_EXTENDED_LIGHT.ASSIST_TRACK, SPOTTED_EXTENDED_LIGHT.ASSIST_STUN])

    def format_recreate(self):
        self.format_str = {
            'icons': '',
            'names': '',
            'vehicles': '',
            'icons_names': '',
            'icons_vehicles': '',
            'full': '',
            'damage': ''
        }

    @staticmethod
    def _getFullTargetLabel(targetInfo):
        parts = []
        if targetInfo.playerName:
            parts.append(targetInfo.playerName)
        if targetInfo.vehicleName:
            parts.append(targetInfo.vehicleName)
        return ' - '.join(parts)

    def sound(self, assist_type):
        soundID = settings_service.getComponentDict(self.config)[SOUND_LIST[assist_type]]
        getPlayer().soundNotifications.play(soundID)

    def textGenerator(self, event):
        textKey, colorKey, macrosKey = GENERATOR[event]
        formatted_text = settings_service.getComponentDict(self.config)[macrosKey].format(**self.format_str)
        message = '%s %s' % (self.config.i18n[textKey], formatted_text) if formatted_text else self.config.i18n[textKey]
        color = settings_service.getComponentDict(self.config)[colorKey]
        return message, color

    def postMessage(self, events):
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]:
            return
        player = getPlayer()
        guiSessionProvider = player.guiSessionProvider
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() != player.playerVehicleID:
            return
        for data in events:
            feedbackEvent = feedback_events.PlayerFeedbackEvent.fromDict(data)
            if feedbackEvent is None:
                continue
            eventID = feedbackEvent.getBattleEventType()
            if eventID not in SUPPORTED_EVENTS:
                continue
            self.format_recreate()
            vehicleID = feedbackEvent.getTargetID()
            vehicleInfo = guiSessionProvider.getArenaDP().getVehicleInfo(vehicleID)
            if not vehicleInfo:
                continue
            icon = '<img src=\'img://%s\' width=\'%s\' height=\'%s\' />' % (vehicleInfo.vehicleType.iconPath.replace('..', 'gui'), settings_service.getComponentDict(self.config)[SPOTTED_EXTENDED_LIGHT.ICON_SIZE_X], settings_service.getComponentDict(self.config)[SPOTTED_EXTENDED_LIGHT.ICON_SIZE_Y])
            targetInfo = guiSessionProvider.getCtx().getPlayerFullNameParts(vID=vehicleID)
            if self.check_macros('{icons}'):
                self.format_str['icons'] += icon
            if self.check_macros('{names}'):
                self.format_str['names'] += '[<b>%s</b>]' % targetInfo.playerName if targetInfo.playerName else icon
            if self.check_macros('{vehicles}'):
                self.format_str['vehicles'] += '[<b>%s</b>]' % targetInfo.vehicleName if targetInfo.vehicleName else icon
            if self.check_macros('{icons_names}'):
                self.format_str['icons_names'] += '%s[<b>%s</b>]' % (icon, targetInfo.playerName) if targetInfo.playerName else icon
            if self.check_macros('{icons_vehicles}'):
                self.format_str['icons_vehicles'] += '%s[<b>%s</b>]' % (icon, targetInfo.vehicleName) if targetInfo.vehicleName else icon
            if self.check_macros('{full}'):
                fullLabel = self._getFullTargetLabel(targetInfo)
                self.format_str['full'] += '%s[<b>%s</b>]' % (icon, fullLabel) if fullLabel else icon
            if self.check_macros('{damage}'):
                extra = _createEfficiencyInfoFromFeedbackEvent(feedbackEvent)
                if extra and extra.getType() in _AGGREGATED_DAMAGE_EFFICIENCY_TYPES:
                    damage = extra.getDamage()
                    if damage:
                        self.format_str['damage'] += '<b> +%s</b>' % damage
            if settings_service.getComponentDict(self.config)[SPOTTED_EXTENDED_LIGHT.SOUND]:
                self.sound(0 if eventID == BATTLE_EVENT_TYPE.SPOTTED else 1)
            message, color = self.textGenerator(eventID)
            sendPanelMessage("<font color='#%s'>%s</font>" % (color, message))


config = Settings()
controller = SpottedLightController(config)


@override(PlayerAvatar, 'onBattleEvents')
def new__onBattleEvents(func, *args):
    func(*args)
    controller.postMessage(args[1])
