# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import partial

from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
from gui.Scaleform.daapi.view.battle.shared.indicators import SixthSenseIndicator
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE

from Driftkings._constants import BATTLE_ALIASES
from Driftkings._constants import GLOBAL, SIXTH_SENSE
from Driftkings.common import getPlayer, square_position, sendChatMessage
from Driftkings.core.callbacks import callback
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.sixth_sense import SixthSenseSettings as ConfigInterface
from Driftkings.views.battle.sixth_sense import SixthSense

AS_BATTLE = BATTLE_ALIASES.SIXTH_SENSE
_STATES_TO_HIDE = {
    VEHICLE_VIEW_STATE.SWITCHING, VEHICLE_VIEW_STATE.RESPAWNING,
    VEHICLE_VIEW_STATE.DESTROYED, VEHICLE_VIEW_STATE.CREW_DEACTIVATED
}

MESSAGES = (
    'Detected: <font color=\'#daff8f\'>{}</font> sec.',
    'Hide: <font color=\'#daff8f\'>{}</font> sec.',
    'Run: <font color=\'#daff8f\'>{}</font> sec.',
    'Alert: <font color=\'#ff7f7f\'>{}</font> sec.',
    'Danger: <font color=\'#ff5555\'>{}</font> sec.'
)
config = ConfigInterface()


class MessagesSpotted(object):
    def __init__(self):
        self.macro = defaultdict(lambda: 'macros not found')
        self.__time = 0.5
        self.last_position = None

    def sendMessage(self):
        self.macro['pos'] = square_position.getSquarePosition()
        if self.macro['pos'] != self.last_position:
            message = settings_service.getComponentDict(config)[SIXTH_SENSE.SPOTTED_TEXT] % self.macro
            if message:
                sendChatMessage(message, 1, settings_service.getComponentDict(config)[SIXTH_SENSE.DELAY])
                self.last_position = self.macro['pos']

    def helpMessage(self):
        def message(avatar):
            avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.SOS)
        if settings_service.getComponentDict(config)[SIXTH_SENSE.HELP_MESSAGE]:
            callback(self.__time, partial(message, getPlayer()))


g_messages = MessagesSpotted()


@override(SixthSenseIndicator, '_sixthSenseToggle')
def new__sixthSenseToggle(func, self, isVisible, force):
    func(self, isVisible, force)
    if not isVisible:
        return
    player = getPlayer()
    if player and player.isVehicleAlive:
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            if settings_service.getComponentDict(config)[SIXTH_SENSE.SPOTTED_MESSAGE]:
                g_messages.sendMessage()
            if settings_service.getComponentDict(config)[SIXTH_SENSE.HELP_MESSAGE]:
                g_messages.helpMessage()


@override(SixthSenseIndicator, '_populate')
def new_populate(func, self):
    func(self)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and (settings_service.getComponentDict(config)[SIXTH_SENSE.USER_ICON] or settings_service.getComponentDict(config)[SIXTH_SENSE.DEFAULT_ICON]):
        self.flashObject.visible = False


def getBattleViews():
    return ((AS_BATTLE, SixthSense, config),)
