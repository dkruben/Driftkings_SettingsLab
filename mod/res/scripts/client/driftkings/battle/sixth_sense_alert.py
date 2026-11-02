# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import partial

import BigWorld
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from gui.Scaleform.daapi.view.battle.shared.indicators import SixthSenseIndicator
from SoundGroups import SoundGroups

from driftkings._constants import BATTLE_ALIASES, GLOBAL, SIXTH_SENSE_ALERT
from driftkings.common.utils import events
from driftkings.common.utils.chat import sendChatMessage
from driftkings.common.utils.wgutils import square_position
from driftkings.core.callbacks import callback
from driftkings.core.hooks import on_event, override
from driftkings.flash.battle.sixth_sense_alert import set_native_visible, SixthSense
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.sixth_sense_alert import SixthSenseAlertSettings
from driftkings.settings.service import settings_service

LOG = get_logger('driftkings.battle.sixth_sense_alert')
AS_BATTLE = BATTLE_ALIASES.SIXTH_SENSE_ALERT
sixth_sense_alert_settings = SixthSenseAlertSettings()


class MessagesSpotted(object):
    def __init__(self):
        self.macro = defaultdict(lambda: 'macros not found')
        self.__time = 0.5
        self.last_position = None

    def reset(self):
        self.last_position = None

    def sendMessage(self):
        settings = settings_service.getComponentDict(sixth_sense_alert_settings)
        self.macro['pos'] = square_position.getSquarePosition()
        if self.macro['pos'] != self.last_position:
            # The text is user-editable: a stray '%' must not break the native alert.
            try:
                message = settings[SIXTH_SENSE_ALERT.SPOTTED_TEXT] % self.macro
            except (TypeError, ValueError):
                LOG.warning('Invalid spotted message template %r', settings[SIXTH_SENSE_ALERT.SPOTTED_TEXT])
                return
            if message:
                sendChatMessage(message, 1, settings[SIXTH_SENSE_ALERT.DELAY])
                self.last_position = self.macro['pos']

    def helpMessage(self):
        def message(avatar):
            avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.SOS)
        if settings_service.getComponentDict(sixth_sense_alert_settings)[SIXTH_SENSE_ALERT.HELP_MESSAGE]:
            callback(self.__time, partial(message, BigWorld.player()))


g_messages = MessagesSpotted()
g_view = None


@on_event(events.PlayerAvatar.startGUI.after)
def new_startGUI(*args):
    g_messages.reset()


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
    player = BigWorld.player()
    if player and player.isVehicleAlive:
        if settings[GLOBAL.ENABLED]:
            if settings[SIXTH_SENSE_ALERT.SPOTTED_MESSAGE]:
                g_messages.sendMessage()
            if settings[SIXTH_SENSE_ALERT.HELP_MESSAGE]:
                g_messages.helpMessage()


def getBattleViews():
    return ((AS_BATTLE, SixthSense, sixth_sense_alert_settings),)
