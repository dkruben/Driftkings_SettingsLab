# -*- coding: utf-8 -*-
from adisp import adisp_process
from gui import SystemMessages
from gui.clans.clan_cache import g_clanCache
from gui.clans.data_wrapper.clan_supply import DataNames, PointStatus, QuestStatus
from gui.impl import backport
from gui.impl.gen import R
from gui.shared.money import Currency
from gui.wgcg.clan_supply.contexts import ClaimRewardsCtx, PurchaseProgressionStageCtx
from gui.wgnc import g_wgncEvents
from gui.wgnc.settings import WGNC_DATA_PROXY_TYPE
from helpers import dependency
from skeletons.gui.app_loader import GuiGlobalSpaceID
from skeletons.gui.shared import IItemsCache
from skeletons.gui.shared.utils import IHangarSpace
from skeletons.gui.web import IWebController

from Driftkings._constants import AUTO_CLAIM_CLAN, GLOBAL
from Driftkings.common import logWarning
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.lobby.auto_claim_clan import AutoClaimClanSettings as Settings

REWARD_STATUS_OK = (QuestStatus.REWARD_AVAILABLE, QuestStatus.REWARD_PENDING)
SKIP_LEVELS = (5, 10, 15, 20)


class AutoClaimClanReward(object):
    __webController = dependency.descriptor(IWebController)
    __itemsCache = dependency.descriptor(IItemsCache)
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self, config):
        self.config = config
        self._subscribed = False
        self.__cachedProgressData = None
        self.__cachedQuestsData = None
        self.__cachedSettingsData = None
        self.__claim_started = False
        self.__enabled = False


    def onModSettingsChanged(self, component, settings):
        self.__enabled = settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]

    def onCreate(self):
        self.updateCache()
        if self.__enabled and g_clanCache.isInClan and self.__cachedQuestsData is not None and self.__cachedProgressData is not None and self.__cachedSettingsData is not None:
            self.parseQuests(self.__cachedQuestsData)
            self.parseProgression(self.__cachedProgressData)

    def subscribe(self):
        if self._subscribed:
            return
        self._subscribed = True
        self.__enabled = settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]
        settings_service.onModSettingsChanged.connect(self.onModSettingsChanged, AUTO_CLAIM_CLAN, (GLOBAL.ENABLED,))
        self.__hangarSpace.onSpaceCreate += self.onCreate
        g_wgncEvents.onProxyDataItemShowByDefault += self.__onProxyDataItemShow
        g_clanCache.clanSupplyProvider.onDataReceived += self.__onDataReceived

    def unsubscribe(self):
        if not self._subscribed:
            return
        self._subscribed = False
        self.__enabled = False
        settings_service.onModSettingsChanged.disconnect(self.onModSettingsChanged)
        self.__hangarSpace.onSpaceCreate -= self.onCreate
        g_wgncEvents.onProxyDataItemShowByDefault -= self.__onProxyDataItemShow
        g_clanCache.clanSupplyProvider.onDataReceived -= self.__onDataReceived

    def updateCache(self):
        self.__cachedQuestsData = g_clanCache.clanSupplyProvider.getQuestsInfo().data
        self.__cachedSettingsData = g_clanCache.clanSupplyProvider.getProgressionSettings().data
        self.__cachedProgressData = g_clanCache.clanSupplyProvider.getProgressionProgress().data

    def __onProxyDataItemShow(self, _, item):
        if self.__enabled and g_clanCache.isInClan and item.getType() == WGNC_DATA_PROXY_TYPE.CLAN_SUPPLY_QUEST_UPDATE:
            status = item.getStatus()
            if not self.__claim_started and status in REWARD_STATUS_OK:
                self.__claimRewards()
            elif status == QuestStatus.COMPLETE and self.__cachedProgressData and self.__cachedSettingsData:
                self.parseProgression(self.__cachedProgressData)

    @adisp_process
    def __claimRewards(self):
        self.__claim_started = True
        try:
            response = yield self.__webController.sendRequest(ctx=ClaimRewardsCtx())
            if not response.isSuccess():
                SystemMessages.pushMessage('Battle Observer: Auto Claim Clan Reward - ' + backport.text(R.strings.clan_supply.messages.claimRewards.error()), type=SystemMessages.SM_TYPE.Error)
                logWarning(self.config.ID, 'Failed to claim rewards. Code: {}', response.getCode())
        finally:
            self.__claim_started = False

    @adisp_process
    def __claimProgression(self, stageID, price):
        response = yield self.__webController.sendRequest(ctx=PurchaseProgressionStageCtx(stageID, price))
        if not response.isSuccess():
            SystemMessages.pushMessage(self.config.ID + 'Auto Claim Clan Reward - Failed to claim Progression.', type=SystemMessages.SM_TYPE.Error)
            logWarning(self.config.ID, 'Failed to claim Progression. Code: {}', response.getCode())

    def parseQuests(self, data):
        if data is not None and not self.__claim_started and any(q.status in REWARD_STATUS_OK for q in data.quests):
            self.__claimRewards()

    @staticmethod
    def isMaximumLevelPurchased(data):
        if not getattr(data, 'points', None):
            return False
        maximum_level = data.points.get(str(max(map(int, data.points.keys()))), None)
        return maximum_level and maximum_level.status == PointStatus.PURCHASED

    def parseProgression(self, data):
        if data is None or self.__cachedSettingsData is None or not self.__cachedSettingsData.enabled:
            return
        if not getattr(data, 'points', None):
            return
        maximum_level_purchased = self.isMaximumLevelPurchased(data)
        available_levels = [int(stateID) for stateID, stageProgress in data.points.items() if stageProgress.status == PointStatus.AVAILABLE and (int(stateID) not in SKIP_LEVELS or maximum_level_purchased)]
        if not available_levels:
            return
        next_level = min(available_levels)
        next_point = self.__cachedSettingsData.points.get(str(next_level))
        currency = self.__itemsCache.items.stats.dynamicCurrencies.get(Currency.TOUR_COIN, 0)
        if next_point and currency >= next_point.price:
            self.__claimProgression(next_level, next_point.price)

    def __onDataReceived(self, dataName, data):
        if dataName in (DataNames.QUESTS_INFO, DataNames.QUESTS_INFO_POST):
            self.__cachedQuestsData = data
            if self.__enabled and g_clanCache.isInClan:
                self.parseQuests(data)
        elif dataName == DataNames.PROGRESSION_PROGRESS:
            self.__cachedProgressData = data
            if self.__enabled and g_clanCache.isInClan:
                self.parseProgression(data)
        elif dataName == DataNames.PROGRESSION_SETTINGS:
            self.__cachedSettingsData = data
            if self.__enabled and g_clanCache.isInClan and self.__cachedProgressData is not None:
                self.parseProgression(self.__cachedProgressData)


# Create global instance
config = Settings()
g_autoClaimClanReward = AutoClaimClanReward(config)


def fini():
    g_autoClaimClanReward.unsubscribe()


def onContextEntered(spaceID):
    if spaceID == GuiGlobalSpaceID.LOBBY:
        g_autoClaimClanReward.subscribe()
        g_autoClaimClanReward.onCreate()


def onContextLeft(spaceID):
    if spaceID == GuiGlobalSpaceID.LOBBY:
        g_autoClaimClanReward.unsubscribe()
