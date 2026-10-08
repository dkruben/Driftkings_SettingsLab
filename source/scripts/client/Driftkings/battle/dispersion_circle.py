# -*- coding: utf-8 -*-
import AvatarInputHandler
import BattleReplay
import BigWorld
import Math
import VehicleGunRotator
import aih_constants
from account_helpers.settings_core.settings_constants import GRAPHICS, SPGAim
from aih_constants import CTRL_MODE_NAME, GUN_MARKER_FLAG, GUN_MARKER_TYPE
from constants import AIMING_MODE, ARENA_PERIOD, SERVER_TICK_LENGTH
from gui.Scaleform.daapi.view.battle.shared import SharedPage
from gui.Scaleform.daapi.view.battle.shared.crosshair import CrosshairPanelContainer, gm_factory
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_components import DefaultGunMarkerComponent, SPGGunMarkerComponent
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_components import GunMarkersComponents
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_factory import _GunMarkersFactory
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import _SETTINGS_KEYS, _SETTINGS_VIEWS, _SETTINGS_KEY_TO_VIEW_ID
from gui.Scaleform.genConsts.GUN_MARKER_VIEW_CONSTANTS import GUN_MARKER_VIEW_CONSTANTS
from gui.battle_control.battle_constants import CROSSHAIR_VIEW_ID
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCache, ISettingsCore

from Driftkings._constants import DISPERSION_CIRCLE, GLOBAL
from Driftkings.common import logWarning, getPlayer
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service, affects
from Driftkings.settings.templates.battle.dispersion_circle import DispersionCircleSettings as Settings

CUSTOM_ARCADE_GUN_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.ARCADE_GUN_MARKER_NAME + '-SERVER'
CUSTOM_SNIPER_GUN_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.SNIPER_GUN_MARKER_NAME + '-SERVER'
CUSTOM_DUAL_GUN_ARCADE_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_ARCADE_MARKER_NAME + '-SERVER'
CUSTOM_DUAL_GUN_SNIPER_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_SNIPER_MARKER_NAME + '-SERVER'
CUSTOM_TWIN_GUN_ARCADE_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.TWIN_GUN_ARCADE_MARKER_NAME + '-SERVER'
CUSTOM_TWIN_GUN_SNIPER_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.TWIN_GUN_SNIPER_MARKER_NAME + '-SERVER'
CUSTOM_SPG_MARKER_NAME = GUN_MARKER_VIEW_CONSTANTS.SPG_GUN_MARKER_NAME + '-SERVER'

CUSTOM_GUN_MARKER_LINKAGES = {
   CUSTOM_ARCADE_GUN_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.GUN_MARKER_LINKAGE,
   CUSTOM_SNIPER_GUN_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.GUN_MARKER_LINKAGE,
   CUSTOM_DUAL_GUN_ARCADE_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_ARCADE_MARKER_LINKAGE,
   CUSTOM_DUAL_GUN_SNIPER_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.DUAL_GUN_SNIPER_MARKER_LINKAGE,
   CUSTOM_TWIN_GUN_ARCADE_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.TWIN_GUN_MARKER_LINKAGE,
   CUSTOM_TWIN_GUN_SNIPER_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.TWIN_GUN_MARKER_LINKAGE,
   CUSTOM_SPG_MARKER_NAME: GUN_MARKER_VIEW_CONSTANTS.GUN_MARKER_SPG_LINKAGE
}


class ReticleState(object):
    def __init__(self, config):
        self.config = config
        self.active = False
        self._settingsCache = None
        self.reticleScaleFactor = 1
        self.showClientAndServerReticle = False
        self.customServerReticleSettings = {}
        self.enableSpgStrategicReticle = False

    def start(self):
        if self.active:
            return
        self._originalMinSize = aih_constants.GUN_MARKER_MIN_SIZE
        self._originalLinkages = gm_factory._GUN_MARKER_LINKAGES
        self._customLinkages = dict(CUSTOM_GUN_MARKER_LINKAGES)
        self._customLinkages.update(self._originalLinkages)
        self.active = True
        try:
            self.applySettings()
            settings_service.onModSettingsChanged.connect(self.onModSettingsChanged, DISPERSION_CIRCLE)
        except Exception:
            self.stop()
            raise

    def stop(self):
        if not self.active:
            return
        self.active = False
        settings_service.onModSettingsChanged.disconnect(self.onModSettingsChanged)
        self.cancelServerAiming()
        aih_constants.GUN_MARKER_MIN_SIZE = self._originalMinSize
        gm_factory._GUN_MARKER_LINKAGES = self._originalLinkages
        self.reticleScaleFactor = 1
        self.showClientAndServerReticle = False
        self.enableSpgStrategicReticle = False

    def onModSettingsChanged(self, component, changes):
        self.applySettings(changes)

    def applySettings(self, changes=None):
        if not self.active:
            return
        data = settings_service.getComponentDict(self.config)
        enabled = data[GLOBAL.ENABLED]
        full = changes is None or affects(changes, GLOBAL.ENABLED)
        if full or affects(changes, DISPERSION_CIRCLE.GUN_MARKER_MINIMUM_SIZE):
            aih_constants.GUN_MARKER_MIN_SIZE = data[DISPERSION_CIRCLE.GUN_MARKER_MINIMUM_SIZE] if enabled else self._originalMinSize
        if full or affects(changes, DISPERSION_CIRCLE.PERCENT_CORRECTION):
            correction = data[DISPERSION_CIRCLE.PERCENT_CORRECTION] / 100.0 if enabled else 0
            self.reticleScaleFactor = 1.71 * correction + (1 - correction)
        if full or affects(changes, DISPERSION_CIRCLE.SHOW_CLIENT_AND_SERVER_RETICLE_BETA):
            self.showClientAndServerReticle = bool(enabled and data[DISPERSION_CIRCLE.SHOW_CLIENT_AND_SERVER_RETICLE_BETA])
            gm_factory._GUN_MARKER_LINKAGES = self._customLinkages if self.showClientAndServerReticle else self._originalLinkages
            if not self.showClientAndServerReticle:
                self.cancelServerAiming()
        for field, key in (('gunTag', DISPERSION_CIRCLE.SERVER_RETICLE_GUN_MARKER_OPACITY),
                           ('gunTagType', DISPERSION_CIRCLE.SERVER_RETICLE_GUN_MARKER_SHAPE),
                           ('mixing', DISPERSION_CIRCLE.SERVER_RETICLE_AIMING_CIRCLE_OPACITY),
                           ('mixingType', DISPERSION_CIRCLE.SERVER_RETICLE_AIMING_CIRCLE_SHAPE)):
            if full or affects(changes, key):
                self.customServerReticleSettings[field] = data[key]
        if full or affects(changes, DISPERSION_CIRCLE.SHOW_SERVER_SPG_STRATEGIC_RETICLE):
            self.enableSpgStrategicReticle = bool(enabled and data[DISPERSION_CIRCLE.SHOW_SERVER_SPG_STRATEGIC_RETICLE])

    def ensureServerAiming(self):
        if not self.active or not self.showClientAndServerReticle:
            return
        cache = dependency.instance(ISettingsCache)
        if cache.isSynced():
            self.cancelServerAiming()
            enableServerAiming()
        elif self._settingsCache is not cache:
            self.cancelServerAiming()
            self._settingsCache = cache
            cache.onSyncCompleted += self.onSettingsSynced

    def cancelServerAiming(self):
        cache = self._settingsCache
        self._settingsCache = None
        if cache is not None:
            cache.onSyncCompleted -= self.onSettingsSynced

    def onSettingsSynced(self):
        if self._settingsCache is None:
            return
        self.cancelServerAiming()
        if self.active and self.showClientAndServerReticle:
            enableServerAiming()


config = Settings()
reticle = ReticleState(config)


def init():
    reticle.start()


def fini():
    reticle.stop()


class CustomCrosshairContainer(CrosshairPanelContainer):
    def __init__(self, createMarkers, overrideMarkers, customSettings, enableSpgStrategicReticle):
        super(CustomCrosshairContainer, self).__init__()
        self.createMarkers = createMarkers
        self.overrideMarkers = overrideMarkers
        self.customSettings = customSettings
        self.enableSpgStrategicReticle = enableSpgStrategicReticle

    def createGunMarkers(self, markersInfo, vehicleInfo):
        if self._CrosshairPanelContainer__gunMarkers is not None:
            logWarning(config.ID, 'Set of gun markers is already created.')
            return
        else:
            self._CrosshairPanelContainer__setGunMarkers(self.createMarkers(markersInfo, vehicleInfo, self.enableSpgStrategicReticle))
            return

    def invalidateGunMarkers(self, markersInfo, vehicleInfo):
        if self._CrosshairPanelContainer__gunMarkers is None:
            logWarning(config.ID, 'Set of gun markers is not created')
            return
        else:
            newSet = self.overrideMarkers(self._CrosshairPanelContainer__gunMarkers, markersInfo, vehicleInfo, self.enableSpgStrategicReticle)
            self._CrosshairPanelContainer__clearGunMarkers()
            self._CrosshairPanelContainer__setGunMarkers(newSet)
            return

    def setSettings(self, _):
        self.as_setSettingsS(self.getSettingsVo())

    def getSettingsVo(self):
        settingsCore = dependency.instance(ISettingsCore)
        getter = settingsCore.getSetting
        data = {}
        for mode in _SETTINGS_KEYS:
            data[_SETTINGS_KEY_TO_VIEW_ID[mode]] = {
                'centerAlphaValue': 0,
                'centerType': 0,
                'netAlphaValue': 0,
                'netType': 0,
                'reloaderAlphaValue': 0,
                'conditionAlphaValue': 0,
                'cassetteAlphaValue': 0,
                'reloaderTimerAlphaValue': 0,
                'zoomIndicatorAlphaValue': 0,
                'gunTagAlpha': self.customSettings['gunTag'] / 100.0,
                'gunTagType': self.customSettings['gunTagType'],
                'mixingAlpha': self.customSettings['mixing'] / 100.0,
                'mixingType': self.customSettings['mixingType']
            }
        for view in _SETTINGS_VIEWS:
            commonSettings = data.get(view, None)
            if commonSettings is None:
                commonSettings = {}
                data[view] = commonSettings
            commonSettings.update({
                'spgScaleWidgetEnabled': getter(SPGAim.SPG_SCALE_WIDGET),
                'isColorBlind': settingsCore.getSetting(GRAPHICS.COLOR_BLIND)
            })
        return data


class _CustomServerControlMarkersFactory(_GunMarkersFactory):
    def create(self, enableSpgStrategicReticle):
        if self._vehicleInfo.isSPG():
            markers = self._createSPGMarkers(enableSpgStrategicReticle)
        elif self._vehicleInfo.isDualGunVehicle():
            markers = self._createDualGunMarkers()
        elif self._vehicleInfo.isTwinGunVehicle():
            markers = self._createTwinGunMarkers()
        else:
            markers = self._createDefaultMarkers()
        return markers

    def _createDualGunMarkers(self):
        return (
         self._createArcadeMarker(CUSTOM_DUAL_GUN_ARCADE_MARKER_NAME),
         self._createSniperMarker(CUSTOM_DUAL_GUN_SNIPER_MARKER_NAME))

    def _createDefaultMarkers(self):
        return (
         self._createArcadeMarker(CUSTOM_ARCADE_GUN_MARKER_NAME),
         self._createSniperMarker(CUSTOM_SNIPER_GUN_MARKER_NAME))

    def _createTwinGunMarkers(self):
        return (
         self._createArcadeMarker(CUSTOM_TWIN_GUN_ARCADE_MARKER_NAME),
         self._createSniperMarker(CUSTOM_TWIN_GUN_SNIPER_MARKER_NAME))

    def _createSPGMarkers(self, enableSpgStrategicReticle):
        if enableSpgStrategicReticle:
            return (self._createArcadeMarker(CUSTOM_ARCADE_GUN_MARKER_NAME), self._createSPGMarker(CUSTOM_SPG_MARKER_NAME))
        else:
            return (self._createArcadeMarker(CUSTOM_ARCADE_GUN_MARKER_NAME),)

    def _createArcadeMarker(self, name):
        dataProvider = self._getMarkerDataProvider(GUN_MARKER_TYPE.SERVER)
        return self._createMarker(DefaultGunMarkerComponent, CROSSHAIR_VIEW_ID.ARCADE, GUN_MARKER_TYPE.SERVER, dataProvider, name)

    def _createSniperMarker(self, name):
        dataProvider = self._getMarkerDataProvider(GUN_MARKER_TYPE.SERVER)
        return self._createMarker(DefaultGunMarkerComponent, CROSSHAIR_VIEW_ID.SNIPER, GUN_MARKER_TYPE.SERVER, dataProvider, name)

    def _createSPGMarker(self, name):
        dataProvider = self._getSPGDataProvider(GUN_MARKER_TYPE.SERVER)
        return self._createMarker(SPGGunMarkerComponent, CROSSHAIR_VIEW_ID.STRATEGIC, GUN_MARKER_TYPE.SERVER, dataProvider, name)


def _createComponents(markersInfo, vehiclesInfo, enableSpgStrategicReticle):
    return GunMarkersComponents(_CustomServerControlMarkersFactory(markersInfo, vehiclesInfo, None).create(enableSpgStrategicReticle))


def _overrideComponents(components, markersInfo, vehiclesInfo, enableSpgStrategicReticle):
    return GunMarkersComponents(_CustomServerControlMarkersFactory(markersInfo, vehiclesInfo, components).create(enableSpgStrategicReticle))


def GetCustomServerCrosshair(customSettings, enableSpgStrategicReticle):
    return CustomCrosshairContainer(_createComponents, _overrideComponents, customSettings, enableSpgStrategicReticle)


def _scaleGunMarkerInfo(gunMarkerInfo):
    if gunMarkerInfo is None or reticle.reticleScaleFactor == 1:
        return gunMarkerInfo
    return gunMarkerInfo._replace(
        size=gunMarkerInfo.size / reticle.reticleScaleFactor,
        dualAccSize=gunMarkerInfo.dualAccSize / reticle.reticleScaleFactor)


@override(AvatarInputHandler.AvatarInputHandler, 'updateClientGunMarker')
def new_AvatarInputHandler_updateClientGunMarker(func, self, gunMarkerInfo, supportMarkersInfo, relaxTime):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.SNIPER):
        gunMarkerInfo = _scaleGunMarkerInfo(gunMarkerInfo)
    return func(self, gunMarkerInfo, supportMarkersInfo, relaxTime)


@override(AvatarInputHandler.AvatarInputHandler, 'updateServerGunMarker')
def new_AvatarInputHandler_updateServerGunMarker(func, self, gunMarkerInfo, supportMarkersInfo, relaxTime):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.SNIPER):
        gunMarkerInfo = _scaleGunMarkerInfo(gunMarkerInfo)
    return func(self, gunMarkerInfo, supportMarkersInfo, relaxTime)


@override(AvatarInputHandler.AvatarInputHandler, 'updateDualAccGunMarker')
def new_AvatarInputHandler_updateDualAccGunMarker(func, self, gunMarkerInfo, supportMarkersInfo, relaxTime):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.SNIPER):
        gunMarkerInfo = _scaleGunMarkerInfo(gunMarkerInfo)
    func(self, gunMarkerInfo, supportMarkersInfo, relaxTime)


@override(SharedPage, '__init__')
def new_SharedPage_init(func, self, components=None, external=None):
    func(self, components, external)
    if reticle.showClientAndServerReticle is True:
        reticle.ensureServerAiming()
        self._external.append(GetCustomServerCrosshair(reticle.customServerReticleSettings, reticle.enableSpgStrategicReticle))


def enableServerAiming():
    settingsCore = dependency.instance(ISettingsCore)
    if settingsCore.getSetting('useServerAim') == 0:
        settingsCore.isChangesConfirmed = True
        settingsCore.applySettings({'useServerAim': True})
        confirmators = settingsCore.applyStorages(True)
        settingsCore.confirmChanges(confirmators)
        settingsCore.clearStorages()


@override(AvatarInputHandler.AvatarInputHandler, 'showClientGunMarkers')
def new_AvatarInputHandler_showClientGunMarkers(func, self, isShown):
    if reticle.showClientAndServerReticle is True:
        self.ctrl.setGunMarkerFlag(isShown, GUN_MARKER_FLAG.CLIENT_MODE_ENABLED)
        self.ctrl.setGunMarkerFlag(isShown, GUN_MARKER_FLAG.SERVER_MODE_ENABLED)
    else:
        func(self, isShown)


@override(AvatarInputHandler.AvatarInputHandler, 'showServerGunMarker')
def new_AvatarInputHandler_showServerGunMarker(func, self, isShown):
    if reticle.showClientAndServerReticle is True:
        if not BattleReplay.isPlaying():
            BattleReplay.g_replayCtrl.setUseServerAim(False)
            self.ctrl.setGunMarkerFlag(isShown, GUN_MARKER_FLAG.SERVER_MODE_ENABLED)
    else:
        func(self, isShown)


@override(AvatarInputHandler.AvatarInputHandler, '_AvatarInputHandler__onArenaStarted')
def new_AvatarInputHandler_onArenaStarted(func, self, period, *args):
    if reticle.showClientAndServerReticle is True:
        isBattle = period == ARENA_PERIOD.BATTLE
        self._AvatarInputHandler__isArenaStarted = isBattle
        self.ctrl.setGunMarkerFlag(isBattle, GUN_MARKER_FLAG.CONTROL_ENABLED)
        self.showServerGunMarker(isBattle)
        self.showClientGunMarkers(isBattle)
    else:
        func(self, period, *args)


@override(gm_factory._ControlMarkersFactory, '_getMarkerType')
def new_ControlMarkersFactory_getMarkerType(func, self):
    if reticle.showClientAndServerReticle is True:
        return GUN_MARKER_TYPE.CLIENT
    else:
        return func(self)


def new_VehicleGunRotator_clientMode_setter(func, self, value):
    if reticle.showClientAndServerReticle is True:
        if self.clientMode == value:
            return
        self._VehicleGunRotator__clientMode = value
        if not self._VehicleGunRotator__isStarted:
            return
        if self.clientMode:
            self._VehicleGunRotator__time = BigWorld.time()
            self.stopTrackingOnServer()
    else:
        return func(self, value)


override(VehicleGunRotator.VehicleGunRotator, 'clientMode', setter=new_VehicleGunRotator_clientMode_setter)


@override(VehicleGunRotator.VehicleGunRotator, 'setShotPosition')
def new_VehicleGunRotator_setShotPosition(func, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
    if reticle.showClientAndServerReticle is True:
        if self.clientMode and not self.showServerMarker and not forceValueRefresh:
            return
        else:
            dispersionAngles = self._VehicleGunRotator__dispersionAngles[:]
            dispersionAngles[0] = dispersionAngle
            if not self.clientMode and VehicleGunRotator.VehicleGunRotator.USE_LOCK_PREDICTION:
                lockEnabled = getPlayer().inputHandler.getAimingMode(AIMING_MODE.TARGET_LOCK)
                if lockEnabled:
                    predictedTargetPos = self.predictLockedTargetShotPoint()
                    if predictedTargetPos is None:
                        return
                    dirToTarget = predictedTargetPos - shotPos
                    dirToTarget.normalise()
                    shotDir = Math.Vector3(shotVec)
                    shotDir.normalise()
                    if shotDir.dot(dirToTarget) > 0.0:
                        return
            gunMarkerInfo = self._VehicleGunRotator__getGunMarkerInfo(
                shotPos,
                shotVec,
                dispersionAngles,
                self._VehicleGunRotator__gunIndex)
            supportMarkersInfo = self._VehicleGunRotator__getSupportMarkersInfo()
            if self.clientMode and self.showServerMarker:
                self._avatar.inputHandler.updateServerGunMarker(gunMarkerInfo, supportMarkersInfo, SERVER_TICK_LENGTH)
            return
    else:
        func(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)
    return


@override(VehicleGunRotator.VehicleGunRotator, 'updateRotationAndGunMarker')
def new_VehicleGunRotator_updateRotationAndGunMarker(func, self, shotPoint, timeDiff):
    func(self, shotPoint, timeDiff)
    if reticle.showClientAndServerReticle and not self.clientMode:
        shotPos, shotVec = self.getCurShotPosition()
        gunMarkerInfo = self._VehicleGunRotator__getGunMarkerInfo(
            shotPos,
            shotVec,
            self._VehicleGunRotator__dispersionAngles,
            self._VehicleGunRotator__gunIndex)
        supportMarkersInfo = self._VehicleGunRotator__getSupportMarkersInfo()
        relaxTime = 0.001
        if not (BattleReplay.g_replayCtrl.isPlaying and BattleReplay.g_replayCtrl.isUpdateGunOnTimeWarp):
            relaxTime = self._VehicleGunRotator__ROTATION_TICK_LENGTH
        self._avatar.inputHandler.updateServerGunMarker(gunMarkerInfo, supportMarkersInfo, relaxTime)
