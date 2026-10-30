# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import partial
import math

from adisp import adisp_process
from Avatar import PlayerAvatar
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
import CommandMapping
from comp7_core.gui.battle_control.controllers.sound_ctrls.comp7_battle_sounds import _EquipmentZoneSoundPlayer
from gui.battle_control.arena_info.arena_vos import VehicleTypeInfoVO
from gui.battle_control.arena_visitor import _ClientArenaVisitor
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.battle_control.controllers.arena_border_ctrl import ArenaBorderController
from gui.battle_control.controllers.team_bases_ctrl import BattleTeamsBasesController
from gui.doc_loaders import GuiColorsLoader
from gui.game_control.special_sound_ctrl import SpecialSoundCtrl
from gui.Scaleform.daapi.view.battle.shared.timers_panel import TimersPanel
from gui.shared.gui_items.processors.vehicle import VehicleAutoBattleBoosterEquipProcessor
from messenger.gui.Scaleform.data.contacts_data_provider import _ContactsCategories
from messenger.storage import MessengerStorageDescriptor, UsersStorage
from PlayerEvents import g_playerEvents

from driftkings._constants import BATTLE_ALIASES, BATTLE_PREFERENCES, GLOBAL
from driftkings.common.utils.formatting import hexToDecimal
from driftkings.common.utils.wgutils import getPlayer, isReplay, square_position
from driftkings.core.callbacks import callback
from driftkings.core.fog_package import FogPackageController
from driftkings.core.hooks import override
from driftkings.flash.battle.debug_panel import DebugPanelView
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.battle_preferences import BattlePreferencesSettings as Settings
from driftkings.settings.service import settings_service
from driftkings.ui import g_events

LOG = get_logger('driftkings.battle.battle_preferences')

_cache = set()
config = Settings()
fog_package = FogPackageController(config)


def getBattleViews():
    return ((BATTLE_ALIASES.DEBUG_PANEL, DebugPanelView, config),)


# disable battle hints


# disable commander voices
@override(SpecialSoundCtrl, '__setSpecialVoiceByTankmen')
@override(SpecialSoundCtrl, '__setSpecialVoiceByCommanderSkinID')
def new_setSoundMode(func, *args, **kwargs):
    settings = settings_service.getComponentDict(config)
    if settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.DISABLE_SOUND_COMMANDER]:
        return False
    return func(*args, **kwargs)


# disable dogTag
@override(_ClientArenaVisitor, 'hasDogTag')
def new_hasDogTag(func, *args, **kwargs):
    settings = settings_service.getComponentDict(config)
    if settings[GLOBAL.ENABLED] and not settings.get(BATTLE_PREFERENCES.SHOW_POSTMORTEM_DOG_TAG, True):
        return False
    return func(*args, **kwargs)


# disable battle hints


# postmortemTips


# force update quests in FullStats


# disable battle artillery_stun_effect sound
@override(TimersPanel, '__playStunSoundIfNeed')
def new_playStunSoundIfNeed(func, *args, **kwargs):
    settings = settings_service.getComponentDict(config)
    if settings[GLOBAL.ENABLED] and settings.get(BATTLE_PREFERENCES.STUN_SOUND, False):
        return None
    return func(*args, **kwargs)


@override(_EquipmentZoneSoundPlayer, '_onVehicleStateUpdated')
def new_onVehicleStateUpdated(func, self, state, value):
    settings = settings_service.getComponentDict(config)
    if state == VEHICLE_VIEW_STATE.STUN and settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.STUN_SOUND]:
        return
    return func(self, state, value)


# mute battle bases
@override(BattleTeamsBasesController, '__playCaptureSound')
def new_muteCaptureSound(func, *args):
    settings = settings_service.getComponentDict(config)
    if not settings[GLOBAL.ENABLED] or not settings[BATTLE_PREFERENCES.MUTE_TEAM_BASE_SOUND]:
        return func(*args)


# border color
@override(ArenaBorderController, '_ArenaBorderController__getCurrentColor')
def new_getBorderColor(func, self, colorBlind):
    settings = settings_service.getComponentDict(config)
    result = func(self, colorBlind)
    if not settings[GLOBAL.ENABLED]:
        colors = GuiColorsLoader.load()
        scheme = colors.getSubScheme('areaBorder', 'color_blind' if colorBlind else 'default')
        color = scheme['rgba'] / 255
        return color
    elif settings[GLOBAL.ENABLED]:
        color = hexToDecimal(settings[GLOBAL.COLOR])
        alpha = int(100)
        red = ((color & 0xff0000) >> 16) / 255.0
        green = ((color & 0x00ff00) >> 8) / 255.0
        blue = (color & 0x0000ff) / 255.0
        alpha = (alpha / 100.0)
        return red, green, blue, alpha
    return result


# Friends
def showFriends():
    settings = settings_service.getComponentDict(config)
    return settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.SHOW_FRIENDS] and not isReplay()


@override(VehicleTypeInfoVO, '__init__')
def new_VehicleTypeInfoVO(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and showFriends():
        self.isPremiumIGR |= kwargs.get('accountDBID') in _cache


@override(VehicleTypeInfoVO, 'update')
def new_VehicleTypeInfoVO_update(func, self, *args, **kwargs):
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and showFriends():
        result = func(self, *args, **kwargs)
        if hasattr(self, 'isPremiumIGR'):
            self.isPremiumIGR |= kwargs.get('accountDBID') in _cache
        return result
    return func(self, *args, **kwargs)


# Battle Messages
def onReload(avatar):
    macro = defaultdict(lambda: 'Macros not found')
    if not avatar.isVehicleAlive:
        return
    ammo = avatar.guiSessionProvider.shared.ammo
    if ammo is None:
        return
    reloadingState = ammo.getGunReloadingState()
    macro['pos'] = square_position.getSquarePosition()
    macro['load'] = '0'
    if reloadingState:
        macro['load'] = str(int(math.ceil(reloadingState.getTimeLeft())))
    template = settings_service.getComponentDict(config)[BATTLE_PREFERENCES.LOAD_TXT]
    try:
        message = template % macro if '%(' in template else template.format(**macro)
    except (IndexError, KeyError, ValueError):
        try:
            message = template % macro
        except (TypeError, ValueError, KeyError):
            message = template
    if len(message) > 0:
        avatar.guiSessionProvider.shared.chatCommands.proto.arenaChat.broadcast(message, 0)
    else:
        avatar.guiSessionProvider.shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.RELOADINGGUN)


@override(PlayerAvatar, 'handleKey')
def new__handleKey(func, self, isDown, key, mods):
    settings = settings_service.getComponentDict(config)
    result = func(self, isDown, key, mods)
    if settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.CLIP_LOAD]:
        cmdMap = CommandMapping.g_instance
        if cmdMap.isFired(CommandMapping.CMD_RELOAD_PARTIAL_CLIP, key) and isDown and self.isVehicleAlive:
            callback(0.5, partial(onReload, self))
    return result


# limit of lines in battle


# PlayerSatisfactionWidget/ShowRateSatisfactionCmp


def _iterVehicleNames(vehicleType):
    if vehicleType is None:
        return
    typeDescr = getattr(vehicleType, 'type', vehicleType)
    for attr in ('shortUserString', 'shortNameWithPrefix', 'shortName', 'userString'):
        name = getattr(typeDescr, attr, None)
        if name:
            yield name


def _getAttackerName(vehicleName):
    player = getPlayer()
    arena = getattr(player, 'arena', None)
    if arena is None:
        return 'Unknown'
    for _, vData in arena.vehicles.items():
        for candidate in _iterVehicleNames(vData.get('vehicleType')):
            if candidate == vehicleName:
                return vData.get('name', 'Unknown')
    return 'Unknown'


# add enemy name to damage log


# Vehicle Boosters
@adisp_process
def changeValue(vehicle, value):
    yield VehicleAutoBattleBoosterEquipProcessor(vehicle, value).request()


def isSpecialVehicle(vehicle):
    flags = ('isOnlyForFunRandomBattles', 'isOnlyForBattleRoyaleBattles', 'isOnlyForMapsTrainingBattles', 'isOnlyForClanWarsBattles', 'isOnlyForComp7Battles', 'isOnlyForEventBattles', 'isOnlyForEpicBattles')
    return any(getattr(vehicle, f, False) for f in flags)


def onVehicleChanged(vehicle):
    settings = settings_service.getComponentDict(config)
    if not settings[GLOBAL.ENABLED] or not settings[BATTLE_PREFERENCES.DIRECTIVES_ONLY_FROM_STORAGE]:
        return
    if vehicle is None or vehicle.isLocked or isSpecialVehicle(vehicle):
        return
    if not hasattr(vehicle, 'battleBoosters') or vehicle.battleBoosters is None:
        LOG.info(('No battle boosters available for this vehicle: {}').format(vehicle.userName))
        return
    isAuto = vehicle.isAutoBattleBoosterEquip()
    boosters = vehicle.battleBoosters.installed.getItems()
    for battleBooster in boosters:
        value = battleBooster.inventoryCount > GLOBAL.ZERO
        if value != isAuto:
            changeValue(vehicle, value)
            LOG.info(('VehicleAutoBattleBoosterEquipProcessor: value={} vehicle={}, booster={}').format(value, vehicle.userName, battleBooster.userName))


def __onGuiCacheSyncCompleted(_):
    _cache.clear()
    users = MessengerStorageDescriptor(UsersStorage).get().getList(_ContactsCategories().getCriteria())
    _cache.update(user._userID for user in users if not user.isIgnored())


def init():
    try:
        fog_package.start()
    except Exception as error:
        LOG.info(('Fog package unavailable: {}').format(error))
    g_playerEvents.onGuiCacheSyncCompleted += __onGuiCacheSyncCompleted
    g_events.onVehicleChangedDelayed += onVehicleChanged


def fini():
    fog_package.stop()
    g_playerEvents.onGuiCacheSyncCompleted -= __onGuiCacheSyncCompleted
    g_events.onVehicleChangedDelayed -= onVehicleChanged


from driftkings.flash.battle.preferences_hooks import install as install_flash_preferences

install_flash_preferences(config, _getAttackerName)
