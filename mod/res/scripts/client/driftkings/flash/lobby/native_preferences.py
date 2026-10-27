# -*- coding: utf-8 -*-
"""Native Scaleform hangar presentation; business state stays in its component."""
from gui.Scaleform.daapi.view.lobby.rankedBattles.ranked_battles_results import RankedBattlesResults
from gui.Scaleform.locale.RES_ICONS import RES_ICONS
from gui.Scaleform.locale.STORAGE import STORAGE
from gui.shared.tooltips import getUnlockPrice
import gui.shared.tooltips.vehicle as tooltips
from helpers import i18n
from messenger.gui.Scaleform.data.ChannelsCarouselHandler import ChannelsCarouselHandler
from messenger.gui.Scaleform.lobby_entry import LobbyEntry

from driftkings._constants import GLOBAL, HANGAR_PREFERENCES
from driftkings.core.hooks import override
from driftkings.settings.service import settings_service


def install(config, _overrideIfAvailable, LOG):
    @override(LobbyEntry, '_LobbyEntry__handleLazyChannelCtlInited')
    def new__handleLazyChannelCtlInited(func, self, event):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_GENERAL_CHAT_BUTTON, True):
            ctx = event.ctx
            controller = ctx.get('controller')
            if controller is None:
                LOG.debug(('Controller is not defined {}').format(ctx))
                return
            else:
                ctx.clear()
                return
        return func(self, event)


    @_overrideIfAvailable(LobbyEntry, '_LobbyEntry__updateCommonChatVisibility')
    def new__updateCommonChatVisibility(func, self, *args, **kwargs):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_GENERAL_CHAT_BUTTON, True):
            return
        return func(self, *args, **kwargs)


    @override(RankedBattlesResults, '_populate')
    def new__populate(func, self):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_RANKED_BATTLE_RESULTS, True):
            return
        func(self)


    @override(tooltips.StatusBlockConstructor, 'construct')
    def new__construct(func, self):
        settings = settings_service.getComponentDict(config)
        result = func(self)
        if result and settings[GLOBAL.ENABLED] and settings[HANGAR_PREFERENCES.SHOW_XP_TO_UNLOCK_VEH]:
            techTreeNode = self.configuration.node
            vehicle = self.vehicle
            isUnlocked = vehicle.isUnlocked
            parentCD = int(techTreeNode.unlockProps.parentID) if techTreeNode is not None else None
            if parentCD is not None:
                isAvailable, cost, need, defCost, discount = getUnlockPrice(vehicle.intCD, parentCD, vehicle.level)
                if isAvailable and not isUnlocked and need > 0 and techTreeNode is not None:
                    icon = '<img src=\'{}\' vspace=\'{}\'>'.format(
                        RES_ICONS.MAPS_ICONS_LIBRARY_XPCOSTICON_1.replace('..', 'img://gui'), -3)
                    template = '<font face=\'$TitleFont\' size=\'14\'><font color=\'#ff2717\'>{}</font> {}</font> {}'
                    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict) and 'data' in result[0] and isinstance(result[0]['data'], dict):
                        result[0]['data']['text'] = template.format(i18n.makeString(STORAGE.BLUEPRINTS_CARD_CONVERTREQUIRED), need, icon)
        return result


    @override(ChannelsCarouselHandler, 'addChannel')
    def new__addChannel(func, self, channel, lazy=False, isNotified=False):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.ALLOW_CHANNEL_BUTTON_BLINKING, True):
            isNotified = False
        return func(self, channel, lazy, isNotified)


    @override(ChannelsCarouselHandler, '_ChannelsCarouselHandler__setItemField')
    def new__setItemField(func, self, clientID, key, value):
        settings = settings_service.getComponentDict(config)
        if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.ALLOW_CHANNEL_BUTTON_BLINKING, True) and key == 'isNotified':
            value = False
        return func(self, clientID, key, value)

