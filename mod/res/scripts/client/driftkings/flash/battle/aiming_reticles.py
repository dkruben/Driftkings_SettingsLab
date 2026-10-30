# -*- coding: utf-8 -*-
"""Native Flash crosshair containers, AS3 linkages and marker factories."""
from account_helpers.settings_core.settings_constants import GRAPHICS, SPGAim
from gui.battle_control.battle_constants import CROSSHAIR_VIEW_ID
from gui.Scaleform.daapi.view.battle.shared import SharedPage
from gui.Scaleform.daapi.view.battle.shared.crosshair import CrosshairPanelContainer, gm_factory
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_components import (DefaultGunMarkerComponent,
                                                                            GunMarkersComponents, SPGGunMarkerComponent)
from gui.Scaleform.daapi.view.battle.shared.crosshair.gm_factory import _GunMarkersFactory
from gui.Scaleform.daapi.view.battle.shared.crosshair.plugins import (_SETTINGS_KEY_TO_VIEW_ID, _SETTINGS_KEYS,
                                                                      _SETTINGS_VIEWS)
from gui.Scaleform.genConsts.GUN_MARKER_VIEW_CONSTANTS import GUN_MARKER_VIEW_CONSTANTS
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from driftkings.core.hooks import override
from driftkings.game_constants import GUN_MARKER_TYPE
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Flash.Reticles')


def set_state(state):
    global reticle
    reticle = state


def get_linkages():
    return gm_factory._GUN_MARKER_LINKAGES


def set_linkages(value):
    gm_factory._GUN_MARKER_LINKAGES = value


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


class CustomCrosshairContainer(CrosshairPanelContainer):
    def __init__(self, createMarkers, overrideMarkers, customSettings, enableSpgStrategicReticle):
        super(CustomCrosshairContainer, self).__init__()
        self.createMarkers = createMarkers
        self.overrideMarkers = overrideMarkers
        self.customSettings = customSettings
        self.enableSpgStrategicReticle = enableSpgStrategicReticle

    def createGunMarkers(self, markersInfo, vehicleInfo):
        if self._CrosshairPanelContainer__gunMarkers is not None:
            LOG.warning('Set of gun markers is already created.')
            return
        else:
            self._CrosshairPanelContainer__setGunMarkers(self.createMarkers(markersInfo, vehicleInfo, self.enableSpgStrategicReticle))
            return

    def invalidateGunMarkers(self, markersInfo, vehicleInfo):
        if self._CrosshairPanelContainer__gunMarkers is None:
            LOG.warning('Set of gun markers is not created')
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


@override(SharedPage, '__init__')
def new_SharedPage_init(func, self, components=None, external=None):
    func(self, components, external)
    if reticle.showClientAndServerReticle is True:
        reticle.ensureServerAiming()
        self._external.append(GetCustomServerCrosshair(reticle.customServerReticleSettings, reticle.enableSpgStrategicReticle))


