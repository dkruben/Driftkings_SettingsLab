# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import partial

from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from gui.Scaleform.daapi.view.battle.shared.indicators import SixthSenseIndicator
from SoundGroups import SoundGroups

from driftkings._constants import BATTLE_ALIASES, GLOBAL, SIXTH_SENSE_ALERT
from driftkings.common.utils.chat import sendChatMessage
from driftkings.common.utils.wgutils import getPlayer, square_position
from driftkings.core.callbacks import callback
from driftkings.core.hooks import override
from driftkings.flash.battle.sixth_sense_alert import set_native_visible, SixthSense
from driftkings.settings.definitions.battle.sixth_sense_alert import SixthSenseAlertSettings
from driftkings.settings.service import settings_service

AS_BATTLE = BATTLE_ALIASES.SIXTH_SENSE_ALERT
sixth_sense_alert_settings = SixthSenseAlertSettings()


class MessagesSpotted(object):
    def __init__(self):
        self.macro = defaultdict(lambda: 'macros not found')
        self.__time = 0.5
        self.last_position = None

    def sendMessage(self):
        settings = settings_service.getComponentDict(sixth_sense_alert_settings)
        self.macro['pos'] = square_position.getSquarePosition()
        if self.macro['pos'] != self.last_position:
            message = settings[SIXTH_SENSE_ALERT.SPOTTED_TEXT] % self.macro
            if message:
                sendChatMessage(message, 1, settings[SIXTH_SENSE_ALERT.DELAY])
                self.last_position = self.macro['pos']

    def helpMessage(self):
        def message(avatar):
            avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.SOS)
        if settings_service.getComponentDict(sixth_sense_alert_settings)[SIXTH_SENSE_ALERT.HELP_MESSAGE]:
            callback(self.__time, partial(message, getPlayer()))


g_messages = MessagesSpotted()
g_view = None


@override(SoundGroups, 'prepareMP3')
def prepare_sixth_sense_mp3(func, self, event):
    # The native indicator prepares its custom MP3 independently of our Wwise
    # event. Leave all other MP3 events and the disabled-mod fallback intact.
    if event == 'sixthSense' and g_view is not None:
        settings = settings_service.getComponentDict(sixth_sense_alert_settings)
        if (settings[GLOBAL.ENABLED] and settings[SIXTH_SENSE_ALERT.USER_SOUND]
                and not settings[SIXTH_SENSE_ALERT.PLAY_TICK_SOUND]):
            return
    return func(self, event)


@override(SixthSenseIndicator, '_sixthSenseToggle')
def new__sixthSenseToggle(func, self, isVisible, force):
    settings = settings_service.getComponentDict(sixth_sense_alert_settings)
    func(self, isVisible, force)
    # Never suppress the game's alert unless our replacement has loaded its icon.
    replacement = (g_view is not None and getattr(g_view, 'iconReady', False) and settings[GLOBAL.ENABLED])
    set_native_visible(self, not replacement)
    if not isVisible:
        return
    player = getPlayer()
    if player and player.isVehicleAlive:
        if settings[GLOBAL.ENABLED]:
            if settings[SIXTH_SENSE_ALERT.SPOTTED_MESSAGE]:
                g_messages.sendMessage()
            if settings[SIXTH_SENSE_ALERT.HELP_MESSAGE]:
                g_messages.helpMessage()


def getBattleViews():
    return ((AS_BATTLE, SixthSense, sixth_sense_alert_settings),)
