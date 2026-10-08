# -*- coding: utf-8 -*-
import gui.shared.tooltips.vehicle as tooltips
from CurrentVehicle import g_currentVehicle
from HeroTank import HeroTank
from gui.Scaleform.daapi.view.lobby.rankedBattles.ranked_battles_results import RankedBattlesResults
from gui.Scaleform.daapi.view.lobby.techtree.techtree_dp import _TechTreeDataProvider
from gui.Scaleform.daapi.view.login.LoginView import LoginView
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.RES_ICONS import RES_ICONS
from gui.Scaleform.locale.STORAGE import STORAGE
from gui.game_control.AwardController import ProgressiveItemsRewardHandler
from gui.game_control.PromoController import PromoController
from gui.game_control.achievements_earning_controller import EarningAnimationCommand, RewardScreenCommand
from gui.impl.lobby.hangar.presenters.user_missions_presenter import UserMissionsPresenter
from gui.impl.lobby.page.session_stats_presenter import SessionStatsPresenter
from gui.impl.lobby.user_missions.hangar_widget.presenters.battle_pass_presenter import BattlePassPresenter
from gui.impl.lobby.user_missions.hangar_widget.services import IBattlePassService, IUserMissionWidgetService
from gui.prb_control.entities.base.actions_validator import CurrentVehicleActionsValidator
from gui.prb_control.items import ValidationResult
from gui.prb_control.settings import PREBATTLE_RESTRICTION
from gui.promo.hangar_teaser_widget import TeaserViewer
from gui.shared.gui_items.Vehicle import Vehicle
from gui.shared.tooltips import getUnlockPrice
from helpers import dependency, i18n
from messenger.gui.Scaleform.data.ChannelsCarouselHandler import ChannelsCarouselHandler
from messenger.gui.Scaleform.lobby_entry import LobbyEntry
from notification.NotificationListView import NotificationListView
from vehicle_systems.tankStructure import ModelStates

from Driftkings._constants import GLOBAL, HANGAR_OPTIONS
from Driftkings.common import isReplay, logDebug, logError, find_attr_name
from Driftkings.core.callbacks import callback
from Driftkings.core.hooks import override, overrideMethod
from Driftkings.settings.service import settings_service, affects
from Driftkings.settings.templates.lobby.hangar_options import HangarOptionsSettings as ConfigInterface
from Driftkings.views.hangar.hangar_options import ClockController
from Driftkings.views.hangar.hangar_options import install_clock_gameface


class HangarOptionsController(object):
    def __init__(self):
        self.active = False

    def start(self):
        if self.active:
            return
        self.active = True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, HANGAR_OPTIONS)

    def stop(self):
        if self.active:
            self.active = False
            settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)

    def onSettingsChanged(self, component, changes):
        if not affects(changes, GLOBAL.ENABLED, HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET):
            return
        visible = dependency.instance(IBattlePassService).isVisible()
        data = settings_service.getComponentDict(config)
        if data[GLOBAL.ENABLED] and not data[HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET]:
            visible = False
        dependency.instance(IUserMissionWidgetService).setGroupVisibility(BattlePassPresenter.GROUP, visible)



config = ConfigInterface()
controller = HangarOptionsController()


def _cfg(key, default=None):
    return settings_service.getComponentDict(config).get(key, default)


def _isSpecialBattleVehicle(target):
    for attr_name in ('isOnlyForEventBattles', 'isOnlyForBattleRoyaleBattles'):
        attr = getattr(target, attr_name, None)
        try:
            if attr() if callable(attr) else attr:
                return True
        except Exception:
            continue
    return False


def _overrideIfAvailable(target, prop):
    if target is None:
        return lambda handler: handler
    real_prop = prop if hasattr(target, prop) else find_attr_name(target, prop, True)
    if real_prop is None and not hasattr(target, prop):
        return lambda handler: handler
    return override(target, real_prop or prop)


# low ammo => configurable ready threshold
@overrideMethod(Vehicle, 'isAmmoFull')
def new_isAmmoFull(base, self):
    original = base.fget if isinstance(base, property) else base
    if not _cfg(GLOBAL.ENABLED, True):
        return original(self)
    try:
        if _isSpecialBattleVehicle(self):
            mult = 0.2
        else:
            mult = max(0.0, float(_cfg(HANGAR_OPTIONS.LOW_AMMO_PERCENTAGE, 20))) / 100.0
        return sum(shell.count for shell in self.shells.installed.getItems()) >= self.ammoMaxSize * mult
    except Exception:
        logError(config.ID, 'Vehicle.isAmmoFull', 'fallback to base')
        return original(self)


# low ammo => vehicle not ready in prebattle
@override(Vehicle, 'isReadyToPrebattle')
def new_isReadyToPrebattle(func, self, *args, **kwargs):
    result = func(self, *args, **kwargs)
    if _isSpecialBattleVehicle(self):
        return result
    try:
        if _cfg(GLOBAL.ENABLED, True) and _cfg(HANGAR_OPTIONS.BLOCK_VEHICLE_IF_LOW_AMMO, False) and not self.hasLockMode() and not self.isAmmoFull:
            return False
    except Exception as err:
        logError(config.ID, 'Vehicle.isReadyToPrebattle', str(err))
    return result


# low ammo => vehicle not ready for battle button/property
@overrideMethod(Vehicle, 'isReadyToFight')
def new_isReadyToFight(base, self, *args, **kwargs):
    result = base.fget(self, *args, **kwargs)
    if _isSpecialBattleVehicle(self):
        return result
    try:
        if _cfg(GLOBAL.ENABLED, True) and _cfg(HANGAR_OPTIONS.BLOCK_VEHICLE_IF_LOW_AMMO, False) and not self.hasLockMode() and not self.isAmmoFull:
            return False
    except Exception as err:
        logError(config.ID, 'Vehicle.isReadyToFight', str(err))
    return result


# low ammo => disable battle button validator
@override(CurrentVehicleActionsValidator, '_validate')
def new_validateCurrentVehicle(func, self):
    res = func(self)
    if _isSpecialBattleVehicle(g_currentVehicle):
        return res
    if not res or res[0] is True:
        try:
            item = getattr(g_currentVehicle, 'item', None)
            if _cfg(GLOBAL.ENABLED, True) and _cfg(HANGAR_OPTIONS.BLOCK_VEHICLE_IF_LOW_AMMO, False) and item and not item.isAmmoFull and not g_currentVehicle.isReadyToFight():
                return ValidationResult(False, PREBATTLE_RESTRICTION.VEHICLE_NOT_READY)
        except Exception as err:
            logError(config.ID, 'CurrentVehicleActionsValidator._validate', str(err))
    return res


# low ammo => show carousel text
@override(i18n, 'makeString')
def new_makeString(func, key, *args, **kwargs):
    if key == MENU.TANKCAROUSEL_VEHICLESTATES_AMMONOTFULL:
        return func(MENU.TANKCAROUSEL_VEHICLESTATES_AMMONOTFULLEVENTS, *args, **kwargs) or func('#dialogs:lowAmmo/title')
    return func(key, *args, **kwargs)


# hide shared chat button
@override(LobbyEntry, '_LobbyEntry__handleLazyChannelCtlInited')
def new__handleLazyChannelCtlInited(func, self, event):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_GENERAL_CHAT_BUTTON, True):
        ctx = event.ctx
        controller = ctx.get('controller')
        if controller is None:
            logDebug(config.ID, True, 'Controller is not defined {}', ctx)
            return
        else:
            ctx.clear()
            return
    return func(self, event)


@_overrideIfAvailable(LobbyEntry, '_LobbyEntry__updateCommonChatVisibility')
def new__updateCommonChatVisibility(func, self, *args, **kwargs):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_GENERAL_CHAT_BUTTON, True):
        return
    return func(self, *args, **kwargs)


# hide premium vehicle on the background in the hangar
@override(HeroTank, 'recreateVehicle')
def new__recreateVehicle(func, self, typeDescriptor=None, state=ModelStates.UNDAMAGED, _callback=None, outfit=None):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_PROMO_PREM_VEHICLE, True):
        return
    func(self, typeDescriptor, state, _callback, outfit)


# hide display pop-up messages in the hangar
@override(TeaserViewer, 'show')
def new__show(func, self, teaserData, promoCount):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_POP_UP_MESSAGES, True):
        return
    func(self, teaserData, promoCount)


# hide display unread notifications counter in the menu
@override(PromoController, 'getPromoCount')
def new__getPromoCount(func, self):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_UNREAD_COUNTER, True):
        return 0
    return func(self)


# disable field mail tips
@override(PromoController, '__tryToShowTeaser')
def new__tryToShowTeaser(func, *args):
    return None if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.FIELD_MAIL, True) else func(*args)


@override(PromoController, '__needToGetTeasersInfo')
def new__needToGetTeasersInfo(func, *args):
    return False if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and not settings_service.getComponentDict(config)[HANGAR_OPTIONS.FIELD_MAIL] else func(*args)


# hide ranked battle results window
@override(RankedBattlesResults, '_populate')
def new__populate(func, self):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_RANKED_BATTLE_RESULTS, True):
        return
    func(self)


# hide display session statistics button
@_overrideIfAvailable(SessionStatsPresenter, '_SessionStatsPresenter__updateSessionStats')
def new__updateSessionStats(func, self):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_BUTTON, True):
        return
    return func(self)


@_overrideIfAvailable(SessionStatsPresenter, '_SessionStatsPresenter__updateBattleCount')
def new__updateBattleCountPresenter(func, self, model):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_BATTLE_COUNT, True):
        model.setBattleCount(0)
        return
    return func(self, model)


@_overrideIfAvailable(UserMissionsPresenter, '_updateMissions')
def new__updateMissions(func, self, vm):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_DAILY_QUEST_WIDGET, True):
        self._addChild(self._WIDGET_ALIAS.Quests(), False)
        vm.setAreMissionsActive(False)
        return
    return func(self, vm)


# hide display pop-up window when receiving progressive decals
@override(ProgressiveItemsRewardHandler, '_showAward')
def new__showAward(func, self, ctx):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_PROGRESSIVE_DECALS_WINDOW, True):
        return
    func(self, ctx)


@_overrideIfAvailable(UserMissionsPresenter, '_updateEntryPoints')
def new__updateEntryPoints(func, self, vm):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_EVENT_BANNER, True):
        self._addChild(self._WIDGET_ALIAS.Events(), False)
        vm.setIsAnyEntryPointAvailable(False)
        return
    return func(self, vm)


# hide counters in service channel
@override(NotificationListView, '_NotificationListView__updateCounters')
def new__updateCounters(func, self):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_BUTTON_COUNTERS, True):
        return
    return func(self)


# hide achievement popups
@override(EarningAnimationCommand, 'execute')
def new__execute(base, self):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_ACHIEVEMENT_POPUPS, True):
        self.release()
        return
    base(self)


@override(RewardScreenCommand, 'execute')
def new__rewardScreenExecute(base, self):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_ACHIEVEMENT_REWARD_WINDOW, True):
        self.release()
        return
    return base(self)


@_overrideIfAvailable(UserMissionsPresenter, '_updateBattlePass')
def new__updateBattlePass(func, self, vm):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET, True):
        self._addChild(self._WIDGET_ALIAS.BattlePass(), False)
        vm.setIsBattlePassActive(False)
        return
    return func(self, vm)


# Auto-Login
class AutoLoginHandler:
    def __init__(self):
        self.firstTime = False

    def auto_login(self, login):
        if not self.firstTime:
            self.firstTime = True
            if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[HANGAR_OPTIONS.AUTO_LOGIN]:
                callback(0, login.as_doAutoLoginS)


autoLogin = AutoLoginHandler()


@override(LoginView, '_populate')
def new__LoginViewPopulate(func, self):
    func(self)
    if not isReplay() and not getattr(self.loginManager, 'wgcAvailable', False):
        autoLogin.auto_login(self)


# Show Xp To Unlock Veh.
@override(tooltips.StatusBlockConstructor, 'construct')
def new__construct(func, self):
    result = func(self)
    if result and settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[HANGAR_OPTIONS.SHOW_XP_TO_UNLOCK_VEH]:
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


@override(_TechTreeDataProvider, 'getAllVehiclePossibleXP')
def new__getAllVehiclePossibleXP(func, self, nodeCD, unlockStats):
    try:
        if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.ALLOW_EXCHANGE_XPIN_TECH_TREE, True):
            return unlockStats.getVehTotalXP(nodeCD)
    except Exception as err:
        logError(config.ID, '_TechTreeDataProvider_getAllVehiclePossibleXP', str(err))
    return func(self, nodeCD, unlockStats)


# The current hangar renders Battle Pass through the user missions presenter.
@override(BattlePassPresenter, 'isVisible')
def new__battlePassIsVisible(func, self):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET, True):
        return False
    return func(self)


@override(UserMissionsPresenter, '_onGroupVisibilityChanged')
def new__missionGroupVisibility(func, self, groupName, isVisible):
    if groupName == BattlePassPresenter.GROUP and settings_service.getComponentDict(config)[GLOBAL.ENABLED] and not settings_service.getComponentDict(config)[HANGAR_OPTIONS.SHOW_BATTLE_PASS_WIDGET]:
        isVisible = False
    return func(self, groupName, isVisible)


# Handlers
@override(ChannelsCarouselHandler, 'addChannel')
def new__addChannel(func, self, channel, lazy=False, isNotified=False):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.ALLOW_CHANNEL_BUTTON_BLINKING, True):
        isNotified = False
    return func(self, channel, lazy, isNotified)


@override(ChannelsCarouselHandler, '_ChannelsCarouselHandler__setItemField')
def new__setItemField(func, self, clientID, key, value):
    if settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(config).get(HANGAR_OPTIONS.ALLOW_CHANNEL_BUTTON_BLINKING, True) and key == 'isNotified':
        value = False
    return func(self, clientID, key, value)


# Hangar clock: one Gameface child per hangar, no global Flash timer.
FEATURE = 'DriftkingsHangarClock'
RESOURCE = 'mods/Driftkings/HangarClock/model'
ASSETS = 'coui://gui/gameface/mods/Driftkings/HangarClock/'


g_clockController = ClockController()
def init():
    controller.start()
    try:
        install_clock_gameface()
        g_clockController.start()
    except Exception:
        logError(config.ID, 'Gameface clock integration unavailable; rebuild the Driftkings UI resources')


def fini():
    controller.stop()
    g_clockController.stop()


# Import registers the presentation hooks with the current component owner.
from Driftkings.views.hangar import hangar_options_hooks
