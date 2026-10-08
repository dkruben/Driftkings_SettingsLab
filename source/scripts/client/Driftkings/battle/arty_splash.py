# -*- coding: utf-8 -*-
import BigWorld
import Math
from Avatar import PlayerAvatar
from AvatarInputHandler.aih_global_binding import CTRL_MODE_NAME
from VehicleGunRotator import VehicleGunRotator
from gui.shared.gui_items import Vehicle
from gui.shared.gui_items.Vehicle import VEHICLE_CLASS_NAME

from Driftkings._constants import ARTY_SPLASH, GLOBAL
from Driftkings.common import checkKeys, getPlayer, sendPanelMessage, logException
from Driftkings.core.hooks import override
from Driftkings.core.keyboard import keyboard
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.arty_splash import ArtySplashSettings as Settings
from Driftkings.ui.common.markers import StaticWorldObjectMarker3D


class ArtySplashController(object):
    def __init__(self, config):
        self.config = config
        self._started = False
        if hasattr(BigWorld.Model, 'sacle') and not hasattr(BigWorld.Model, 'scale'):
            BigWorld.Model.scale = BigWorld.Model.sacle
        self.modelSplash = None
        self.modelDot = None
        self.modelSplashCircle = None
        self.modelSplashVisible = False
        self.modelDotVisible = False
        self.modelSplashKeyPressed = False
        self.modelDotKeyPressed = False
        self.scaleSplash = None
        self.player = None

    def _getVehicleDescriptor(self):
        if self.player is None or not hasattr(self.player, 'getVehicleDescriptor'):
            return None
        return self.player.getVehicleDescriptor()

    def _getMarkerPosition(self):
        gunRotator = getattr(self.player, 'gunRotator', None)
        markerInfo = getattr(gunRotator, 'markerInfo', None)
        if not markerInfo:
            return None
        try:
            return markerInfo[0]
        except (IndexError, TypeError):
            return None

    def startBattle(self):
        if self._started:
            return
        self._started = True
        if settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]:
            keyboard.subscribe(self.injectButton)
            self.player = getPlayer()
            self.modelSplashVisible = settings_service.getComponentDict(self.config)[ARTY_SPLASH.SHOW_SPLASH_ON_DEFAULT]
            self.modelDotVisible = settings_service.getComponentDict(self.config)[ARTY_SPLASH.SHOW_DOT_ON_DEFAULT]
            self.scaleSplash = None
            self.modelSplash = StaticWorldObjectMarker3D({'path': settings_service.getComponentDict(self.config)[ARTY_SPLASH.MODEL_PATH_SPLASH]}, (0, 0, 0))
            self.modelDot = StaticWorldObjectMarker3D({'path': settings_service.getComponentDict(self.config)[ARTY_SPLASH.MODEL_PATH_DOT]}, (0, 0, 0))
            self.modelDot.model.scale = (0.1, 0.1, 0.1)
            vehicleTypeDescriptor = getattr(self.player, 'vehicleTypeDescriptor', None)
            if vehicleTypeDescriptor is not None and Vehicle.getVehicleClassTag(vehicleTypeDescriptor.type.tags) == VEHICLE_CLASS_NAME.SPG:
                self.modelDot.model.scale = (0.5, 0.5, 0.5)
            self.modelSplash.model.visible = False
            self.modelDot.model.visible = False
            self.modelSplashCircle = BigWorld.PyTerrainSelectedArea()
            player = BigWorld.player()
            if player is not None:
                self.modelSplashCircle.setup('content/Interface/CheckPoint/CheckPoint_yellow_black.model', Math.Vector2(2.0, 2.0), 0.5, 0xFFFFFFFF, player.spaceID)
            self.modelSplash.model.root.attach(self.modelSplashCircle)
            self.modelSplashCircle.enableAccurateCollision(False)

    def stopBattle(self):
        keyboard.unsubscribe(self.injectButton)
        self._started = False
        self.modelSplashVisible = False
        self.modelDotVisible = False
        self.modelSplashKeyPressed = False
        self.modelDotKeyPressed = False
        if self.modelSplash is not None:
            if self.modelSplashCircle is not None and self.modelSplashCircle.attached:
                self.modelSplash.model.root.detach(self.modelSplashCircle)
            self.modelSplash.clear()
        if self.modelDot is not None:
            self.modelDot.clear()
        self.modelSplash = None
        self.modelDot = None
        self.scaleSplash = None
        self.modelSplashCircle = None
        self.player = None

    def working(self):
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] or self.player is None:
            self.hideVisible()
            return
        if not hasattr(self.player, 'vehicleTypeDescriptor') or not hasattr(self.player, 'gunRotator'):
            self.hideVisible()
            return
        vehicleDescriptor = self._getVehicleDescriptor()
        if vehicleDescriptor is None:
            self.hideVisible()
            return
        if Vehicle.getVehicleClassTag(vehicleDescriptor.type.tags) != VEHICLE_CLASS_NAME.SPG:
            self.hideVisible()
            return
        shell = getattr(getattr(vehicleDescriptor, 'shot', None), 'shell', None)
        if shell is None:
            self.hideVisible()
            return
        if 'HIGH_EXPLOSIVE' not in shell.kind:
            self.hideVisible()
            return
        inputHandler = getattr(self.player, 'inputHandler', None)
        ctrlModeName = getattr(inputHandler, 'ctrlModeName', None)
        if ctrlModeName is None:
            self.hideVisible()
            return
        if not settings_service.getComponentDict(self.config)[ARTY_SPLASH.SHOW_MODE_ARCADE] and ctrlModeName == CTRL_MODE_NAME.ARCADE:
            self.hideVisible()
            return
        if not settings_service.getComponentDict(self.config)[ARTY_SPLASH.SHOW_MODE_SNIPER] and ctrlModeName == CTRL_MODE_NAME.SNIPER:
            self.hideVisible()
            return
        artyModes = [CTRL_MODE_NAME.STRATEGIC]
        artyMode = getattr(CTRL_MODE_NAME, 'ARTY', None)
        if artyMode is not None:
            artyModes.append(artyMode)
        if not settings_service.getComponentDict(self.config)[ARTY_SPLASH.SHOW_MODE_ARTY] and ctrlModeName in artyModes:
            self.hideVisible()
            return
        markerPosition = self._getMarkerPosition()
        if markerPosition is None:
            self.hideVisible()
            return
        if self.modelSplash is not None and self.modelSplash.model:
            if self.scaleSplash is None or self.scaleSplash != shell.type.explosionRadius:
                self.scaleSplash = shell.type.explosionRadius
                self.modelSplash.model.scale = (self.scaleSplash, self.scaleSplash, self.scaleSplash)
            if not self.modelSplashKeyPressed:
                self.modelSplashVisible = settings_service.getComponentDict(self.config)[ARTY_SPLASH.SHOW_SPLASH_ON_DEFAULT]
            self.modelSplash.model.position = markerPosition
            if self.modelSplashCircle is not None:
                self.modelSplashCircle.updateHeights()
        if self.modelDot is not None and self.modelDot.model:
            if not self.modelDotKeyPressed:
                self.modelDotVisible = settings_service.getComponentDict(self.config)[ARTY_SPLASH.SHOW_DOT_ON_DEFAULT]
            self.modelDot.model.position = markerPosition
        self.setVisible()

    def setVisible(self):
        if self.modelSplash is not None and self.modelSplash.model:
            if self.modelSplash.model.visible != self.modelSplashVisible:
                self.modelSplash.model.visible = self.modelSplashVisible
        if self.modelDot is not None and self.modelDot.model:
            if self.modelDot.model.visible != self.modelDotVisible:
                self.modelDot.model.visible = self.modelDotVisible

    def hideVisible(self):
        if self.modelSplash is not None and self.modelSplash.model and self.modelSplash.model.visible:
            self.modelSplash.model.visible = False
        if self.modelDot is not None and self.modelDot.model and self.modelDot.model.visible:
            self.modelDot.model.visible = False

    @logException
    def injectButton(self, event):
        if not self._started or not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]:
            return
        if checkKeys(settings_service.getComponentDict(self.config)[ARTY_SPLASH.BUTTON_SHOW_SPLASH]) and event.isKeyDown():
            self.modelSplashKeyPressed = True
            self.modelSplashVisible = not self.modelSplashVisible
            sendPanelMessage(self.config.i18n['UI_artySplash_messageSplashOn'] if self.modelSplashVisible else self.config.i18n['UI_artySplash_messageSplashOff'], 'Green' if self.modelSplashVisible else 'Red')
            self.setVisible()
        if checkKeys(settings_service.getComponentDict(self.config)[ARTY_SPLASH.BUTTON_SHOW_DOT]) and event.isKeyDown():
            self.modelDotKeyPressed = True
            self.modelDotVisible = not self.modelDotVisible
            sendPanelMessage(self.config.i18n['UI_artySplash_messageDotOn'] if self.modelDotVisible else self.config.i18n['UI_artySplash_messageDotOff'], 'Green' if self.modelDotVisible else 'Red')
            self.setVisible()


config = Settings()
controller = ArtySplashController(config)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    controller.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    controller.stopBattle()


@override(VehicleGunRotator, '_VehicleGunRotator__updateGunMarker')
def new_updateMarkerPos(func, *args):
    func(*args)
    controller.working()


def fini():
    controller.stopBattle()
