# -*- coding: utf-8 -*-
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from gui.battle_control.controllers.personal_efficiency_ctrl import (_AGGREGATED_DAMAGE_EFFICIENCY_TYPES,
                                                                     _createEfficiencyInfoFromFeedbackEvent)
from gui.shared.gui_items.Vehicle import getContourIconPath, getIconPath

from driftkings._constants import ENEMY_SPOTTING_STATUS, GLOBAL
from driftkings.common.utils.game import sendPanelMessage
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.battle_events import battleEvents
from driftkings.core.hooks import on_event
from driftkings.core.vehicle_images import resolve_vehicle_images
from driftkings.settings.definitions.battle.enemy_spotting_status import EnemySpottingStatusSettings as Settings
from driftkings.settings.service import settings_service

SOUND_LIST = (ENEMY_SPOTTING_STATUS.SOUND_SPOTTED, ENEMY_SPOTTING_STATUS.SOUND_ASSIST)
GENERATOR = {
    BATTLE_EVENT_TYPE.SPOTTED: ['UI_setting_Spotted_text', ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_SPOTTED, ENEMY_SPOTTING_STATUS.SPOTTED],
    BATTLE_EVENT_TYPE.RADIO_ASSIST: ['UI_setting_AssistRadio_text', ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_ASSIST_RADIO, ENEMY_SPOTTING_STATUS.ASSIST_RADIO],
    BATTLE_EVENT_TYPE.TRACK_ASSIST: ['UI_setting_AssistTrack_text', ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_ASSIST_TRACK, ENEMY_SPOTTING_STATUS.ASSIST_TRACK],
    BATTLE_EVENT_TYPE.STUN_ASSIST: ['UI_setting_AssistStun_text', ENEMY_SPOTTING_STATUS.MESSAGE_COLOR_ASSIST_STUN, ENEMY_SPOTTING_STATUS.ASSIST_STUN]
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
        return any(macros in settings_service.getComponentDict(self.config)[text_type] for text_type in [ENEMY_SPOTTING_STATUS.SPOTTED, ENEMY_SPOTTING_STATUS.ASSIST_RADIO, ENEMY_SPOTTING_STATUS.ASSIST_TRACK, ENEMY_SPOTTING_STATUS.ASSIST_STUN])

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
        settings = settings_service.getComponentDict(self.config)
        textKey, colorKey, macrosKey = GENERATOR[event]
        formatted_text = settings[macrosKey].format(**self.format_str)
        message = '%s %s' % (self.config.i18n[textKey], formatted_text) if formatted_text else self.config.i18n[textKey]
        color = settings[colorKey]
        return message, color

    def postMessage(self, events):
        settings = settings_service.getComponentDict(self.config)
        if not settings[GLOBAL.ENABLED]:
            return
        player = getPlayer()
        guiSessionProvider = player.guiSessionProvider
        if guiSessionProvider.shared.vehicleState.getControllingVehicleID() != player.playerVehicleID:
            return
        for feedbackEvent in events:
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
            icon = '<img src=\'img://%s\' width=\'%s\' height=\'%s\' />' % (vehicleInfo.vehicleType.iconPath.replace('..', 'gui'), settings[ENEMY_SPOTTING_STATUS.ICON_SIZE_X], settings[ENEMY_SPOTTING_STATUS.ICON_SIZE_Y])
            icon = resolve_vehicle_images(icon, getIconPath, getContourIconPath)
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
            if settings[ENEMY_SPOTTING_STATUS.SOUND]:
                self.sound(0 if eventID == BATTLE_EVENT_TYPE.SPOTTED else 1)
            message, color = self.textGenerator(eventID)
            sendPanelMessage("<font color='%s'>%s</font>" % (color, message))


config = Settings()
controller = SpottedLightController(config)


@on_event(battleEvents.feedback)
def new__onBattleEvents(*args):
    controller.postMessage(args[1])
