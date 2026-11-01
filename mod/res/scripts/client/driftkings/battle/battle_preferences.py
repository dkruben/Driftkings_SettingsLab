# -*- coding: utf-8 -*-
from functools import partial

from adisp import adisp_process
from Avatar import PlayerAvatar
import BigWorld
from chat_commands_consts import BATTLE_CHAT_COMMAND_NAMES
import CommandMapping
from comp7_core.gui.battle_control.controllers.sound_ctrls.comp7_battle_sounds import _EquipmentZoneSoundPlayer
from CurrentVehicle import g_currentVehicle
from gui.battle_control.arena_info.arena_vos import VehicleTypeInfoVO
from gui.battle_control.arena_visitor import _ClientArenaVisitor
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE
from gui.battle_control.controllers.arena_border_ctrl import ArenaBorderController
from gui.battle_control.controllers.team_bases_ctrl import BattleTeamsBasesController
from gui.doc_loaders import GuiColorsLoader
from gui.game_control.special_sound_ctrl import SpecialSoundCtrl
from gui.Scaleform.daapi.view.battle.shared.timers_panel import TimersPanel
from gui.shared.gui_items.processors.vehicle import VehicleAutoBattleBoosterEquipProcessor
from gui.shared.personality import ServicesLocator
from messenger.gui.Scaleform.data.contacts_data_provider import _ContactsCategories
from messenger.storage import MessengerStorageDescriptor, UsersStorage
from PlayerEvents import g_playerEvents

from driftkings._constants import BATTLE_ALIASES, BATTLE_PREFERENCES, GLOBAL
from driftkings.common.utils.formatting import hexToDecimal
from driftkings.common.utils.wgutils import isReplay
from driftkings.core.callbacks import callback
from driftkings.core.fog_package import FogPackageController
from driftkings.core.hooks import override
from driftkings.flash.battle.debug_panel import DebugPanelView
from driftkings.flash.battle.preferences_hooks import install as install_flash_preferences
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.battle_preferences import BattlePreferencesSettings
from driftkings.settings.service import settings_service

LOG = get_logger('driftkings.battle.battle_preferences')

_cache = set()
battle_preferences_settings = BattlePreferencesSettings()
fog_package = FogPackageController(battle_preferences_settings)
_itemsCache = None


# Declara o painel de depuração usado pelas opções de batalha.
def getBattleViews():
    return ((BATTLE_ALIASES.DEBUG_PANEL, DebugPanelView, battle_preferences_settings),)


# Suprime as vozes do comandante quando a opção está ativa.
@override(SpecialSoundCtrl, '__setSpecialVoiceByTankmen')
@override(SpecialSoundCtrl, '__setSpecialVoiceByCommanderSkinID')
def new_setSoundMode(func, *args, **kwargs):
    settings = settings_service.getComponentDict(battle_preferences_settings)
    if settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.DISABLE_SOUND_COMMANDER]:
        return False
    return func(*args, **kwargs)


# Respeita a opção de mostrar a identificação do adversário após a destruição.
@override(_ClientArenaVisitor, 'hasDogTag')
def new_hasDogTag(func, *args, **kwargs):
    settings = settings_service.getComponentDict(battle_preferences_settings)
    if settings[GLOBAL.ENABLED] and not settings.get(BATTLE_PREFERENCES.SHOW_POSTMORTEM_DOG_TAG, True):
        return False
    return func(*args, **kwargs)


# Suprime o som de atordoamento quando configurado.
@override(TimersPanel, '__playStunSoundIfNeed')
def new_playStunSoundIfNeed(func, *args, **kwargs):
    settings = settings_service.getComponentDict(battle_preferences_settings)
    if settings[GLOBAL.ENABLED] and settings.get(BATTLE_PREFERENCES.STUN_SOUND, False):
        return None
    return func(*args, **kwargs)


# Impede o som de atordoamento do equipamento de zona quando configurado.
@override(_EquipmentZoneSoundPlayer, '_onVehicleStateUpdated')
def new_onVehicleStateUpdated(func, self, state, value):
    settings = settings_service.getComponentDict(battle_preferences_settings)
    if state == VEHICLE_VIEW_STATE.STUN and settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.STUN_SOUND]:
        return
    return func(self, state, value)


# Suprime os sons de captura de base quando configurado.
@override(BattleTeamsBasesController, '__playCaptureSound')
def new_muteCaptureSound(func, *args):
    settings = settings_service.getComponentDict(battle_preferences_settings)
    if not settings[GLOBAL.ENABLED] or not settings[BATTLE_PREFERENCES.MUTE_TEAM_BASE_SOUND]:
        return func(*args)


# Aplica a cor e a opacidade configuradas ao limite da arena.
@override(ArenaBorderController, '_ArenaBorderController__getCurrentColor')
def new_getBorderColor(func, self, colorBlind):
    settings = settings_service.getComponentDict(battle_preferences_settings)
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


# Verifica se a identificação de amigos deve estar ativa nesta sessão.
def showFriends():
    settings = settings_service.getComponentDict(battle_preferences_settings)
    return settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.SHOW_FRIENDS] and not isReplay()


# Assinala os amigos conhecidos ao criar os dados do veículo.
@override(VehicleTypeInfoVO, '__init__')
def new_VehicleTypeInfoVO(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if settings_service.getComponentDict(battle_preferences_settings)[GLOBAL.ENABLED] and showFriends():
        self.isPremiumIGR |= kwargs.get('accountDBID') in _cache


# Atualiza a identificação de amigos nos dados do veículo.
@override(VehicleTypeInfoVO, 'update')
def new_VehicleTypeInfoVO_update(func, self, *args, **kwargs):
    if settings_service.getComponentDict(battle_preferences_settings)[GLOBAL.ENABLED] and showFriends():
        result = func(self, *args, **kwargs)
        if hasattr(self, 'isPremiumIGR'):
            self.isPremiumIGR |= kwargs.get('accountDBID') in _cache
        return result
    return func(self, *args, **kwargs)


# Envia apenas o comando nativo do F8 após a recarga manual.
def onReload(avatar):
    settings = settings_service.getComponentDict(battle_preferences_settings)
    if (not settings[GLOBAL.ENABLED] or not settings[BATTLE_PREFERENCES.CLIP_LOAD]
            or BigWorld.player() is not avatar or isReplay() or not avatar.isVehicleAlive):
        return
    shared = avatar.guiSessionProvider.shared
    if shared.ammo is None or shared.chatCommands is None:
        return
    # The F8 command owns localization, reload variants, minimap effects and cooldown.
    shared.chatCommands.handleChatCommand(BATTLE_CHAT_COMMAND_NAMES.RELOADINGGUN)


# Mantém a recarga nativa e agenda a notificação pela tecla configurada.
@override(PlayerAvatar, 'handleKey')
def new__handleKey(func, self, isDown, key, mods):
    settings = settings_service.getComponentDict(battle_preferences_settings)
    result = func(self, isDown, key, mods)
    if settings[GLOBAL.ENABLED] and settings[BATTLE_PREFERENCES.CLIP_LOAD]:
        cmdMap = CommandMapping.g_instance
        if cmdMap.isFired(CommandMapping.CMD_RELOAD_PARTIAL_CLIP, key) and isDown and self.isVehicleAlive:
            callback(0.5, partial(onReload, self))
    return result


# Percorre os nomes disponíveis no descritor de um veículo.
def _iterVehicleNames(vehicleType):
    if vehicleType is None:
        return
    typeDescr = getattr(vehicleType, 'type', vehicleType)
    for attr in ('shortUserString', 'shortNameWithPrefix', 'shortName', 'userString'):
        name = getattr(typeDescr, attr, None)
        if name:
            yield name


# Procura o nome do atacante a partir do nome do veículo.
def _getAttackerName(vehicleName):
    player = BigWorld.player()
    arena = getattr(player, 'arena', None)
    if arena is None:
        return 'Unknown'
    for _, vData in arena.vehicles.items():
        for candidate in _iterVehicleNames(vData.get('vehicleType')):
            if candidate == vehicleName:
                return vData.get('name', 'Unknown')
    return 'Unknown'


# Pede ao cliente a alteração da reposição automática de diretivas.
@adisp_process
def changeValue(vehicle, value):
    yield VehicleAutoBattleBoosterEquipProcessor(vehicle, value).request()


# Identifica veículos exclusivos de modos especiais.
def isSpecialVehicle(vehicle):
    flags = ('isOnlyForFunRandomBattles', 'isOnlyForBattleRoyaleBattles', 'isOnlyForMapsTrainingBattles', 'isOnlyForClanWarsBattles', 'isOnlyForComp7Battles', 'isOnlyForEventBattles', 'isOnlyForEpicBattles')
    return any(getattr(vehicle, f, False) for f in flags)


# Ajusta a reposição de diretivas à quantidade disponível no depósito.
def onVehicleChanged(vehicle):
    settings = settings_service.getComponentDict(battle_preferences_settings)
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


# Reaplica as opções de diretivas ao veículo selecionado.
def _onCurrentVehicleChanged(*_):
    if g_currentVehicle.isPresent():
        onVehicleChanged(g_currentVehicle.item)


# Atualiza a cache de contactos usados na identificação de amigos.
def __onGuiCacheSyncCompleted(_):
    _cache.clear()
    users = MessengerStorageDescriptor(UsersStorage).get().getList(_ContactsCategories().getCriteria())
    _cache.update(user._userID for user in users if not user.isIgnored())


# Inicia as opções de nevoeiro e subscreve as alterações do hangar e dos contactos.
def init():
    global _itemsCache
    if _itemsCache is not None:
        return
    try:
        fog_package.start()
    except Exception as error:
        LOG.info(('Fog package unavailable: {}').format(error))
    g_playerEvents.onGuiCacheSyncCompleted += __onGuiCacheSyncCompleted
    g_currentVehicle.onChanged += _onCurrentVehicleChanged
    _itemsCache = ServicesLocator.itemsCache
    _itemsCache.onSyncCompleted += _onCurrentVehicleChanged
    _onCurrentVehicleChanged()


# Encerra as opções de nevoeiro e remove as subscrições do módulo.
def fini():
    global _itemsCache
    if _itemsCache is None:
        return
    fog_package.stop()
    g_playerEvents.onGuiCacheSyncCompleted -= __onGuiCacheSyncCompleted
    g_currentVehicle.onChanged -= _onCurrentVehicleChanged
    _itemsCache.onSyncCompleted -= _onCurrentVehicleChanged
    _itemsCache = None

install_flash_preferences(battle_preferences_settings, _getAttackerName)
