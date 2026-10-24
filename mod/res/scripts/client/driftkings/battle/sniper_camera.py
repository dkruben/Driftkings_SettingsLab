# -*- coding: utf-8 -*-
from aih_constants import CTRL_MODE_NAME
from AvatarInputHandler.control_modes import SniperControlMode
from AvatarInputHandler.DynamicCameras.SniperCamera import SniperCamera
from helpers.bound_effects import ModelBoundEffects
from PlayerEvents import g_playerEvents
import TriggersManager

from driftkings._constants import GLOBAL, SNIPER_CAMERA
from driftkings.common.utils.wgutils import getPlayer, isReplay
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.core.hooks import override
from driftkings.settings.definitions.battle.sniper_camera import SniperCameraSettings as Settings
from driftkings.settings.service import settings_service

MIN_ZOOM = 2.0
SMALL_CALIBER_THRESHOLD = 60
config = Settings()


@override(SniperCamera, '_readConfigs')
def new__readConfigs(func, self, data):
    settings = settings_service.getComponentDict(config)
    for cfg in (self._baseCfg, self._userCfg, self._cfg):
        cfg.clear()
    func(self, data)
    if not settings[GLOBAL.ENABLED] or isReplay():
        return
    if settings[SNIPER_CAMERA.NO_SNIPER_DYNAMIC] and self.isCameraDynamic():
        self.enableDynamicCamera(False)
    if settings[SNIPER_CAMERA.ZOOM_STEPS]['enabled']:
        steps = [step for step in settings[SNIPER_CAMERA.ZOOM_STEPS]['steps'] if step >= MIN_ZOOM]
        if len(steps) > 3:
            steps.sort()
            for cfg in (self._cfg, self._userCfg, self._baseCfg):
                cfg['increasedZoom'] = True
                cfg['zooms'] = steps
            exposure = self._SniperCamera__dynamicCfg['zoomExposure']
            while len(steps) > len(exposure):
                exposure.insert(0, exposure[0] + 0.1)


class ZoomController(TriggersManager.ITriggerListener):

    def __init__(self, config):
        self.config = config
        self.latency = 0
        self.skip_clip = False
        self.subscribed = False
        self.avatar = None
        self._listening = False
        self._pending = set()
        self.__trigger_type = TriggersManager.TRIGGER_TYPE.PLAYER_DISCRETE_SHOOT
        self.updateSettings()
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, SNIPER_CAMERA)

    def onSettingsChanged(self, component, changes):
        self.updateSettings()

    def updateSettings(self):
        settings = settings_service.getComponentDict(self.config)
        enabled = settings[SNIPER_CAMERA.DISABLE_CAM_AFTER_SHOT] and settings[GLOBAL.ENABLED]
        self.latency = float(settings[SNIPER_CAMERA.DISABLE_CAM_AFTER_SHOT_LATENCY])
        self.skip_clip = settings[SNIPER_CAMERA.DISABLE_CAM_AFTER_SHOT_SKIP_CLIP]
        if not self.subscribed and enabled:
            g_playerEvents.onAvatarReady += self.onStart
            g_playerEvents.onAvatarBecomeNonPlayer += self.onFinish
            self.subscribed = True
        elif self.subscribed and not enabled:
            self.dispose()

    def onStart(self):
        avatar = getPlayer()
        if not self.subscribed or avatar is None or self._listening and self.avatar is avatar:
            return
        self.onFinish()
        self.avatar = avatar
        TriggersManager.g_manager.addListener(self)
        self._listening = True

    def onFinish(self):
        self.avatar = None
        for token in self._pending:
            cancelCallback(token)
        self._pending.clear()
        if self._listening:
            TriggersManager.g_manager.delListener(self)
            self._listening = False

    def dispose(self):
        self.onFinish()
        if self.subscribed:
            g_playerEvents.onAvatarReady -= self.onStart
            g_playerEvents.onAvatarBecomeNonPlayer -= self.onFinish
            self.subscribed = False

    def onTriggerActivated(self, params):
        if self._listening and params.get('type') == self.__trigger_type:
            avatar = self.avatar
            token = [None]
            def change():
                self._pending.discard(token[0])
                if self.avatar is avatar:
                    self.changeControlMode()
            token[0] = callback(max(self.latency, 0), change)
            self._pending.add(token[0])

    def changeControlMode(self):
        if self.avatar is None:
            return
        input_handler = self.avatar.inputHandler
        if input_handler is None or input_handler.ctrlModeName != CTRL_MODE_NAME.SNIPER:
            return
        v_desc = self.avatar.getVehicleDescriptor()
        caliber_skip = v_desc.shot.shell.caliber <= SMALL_CALIBER_THRESHOLD
        if caliber_skip or (self.skip_clip and 'clip' in v_desc.gun.tags):
            return
        aiming_system = input_handler.ctrl.camera.aimingSystem
        input_handler.onControlModeChanged(CTRL_MODE_NAME.ARCADE, prevModeName=input_handler.ctrlModeName, preferredPos=aiming_system.getDesiredShotPoint(), turretYaw=aiming_system.turretYaw, gunPitch=aiming_system.gunPitch, aimingMode=input_handler.ctrl._aimingMode, closesDist=False, curVehicleID=self.avatar.playerVehicleID)


controller = ZoomController(config)


@override(SniperControlMode, '__setupBinoculars')
def new__setupBinoculars(func, self, optDevices):
    settings = settings_service.getComponentDict(config)
    result = func(self, optDevices)
    if settings[GLOBAL.ENABLED] and settings[SNIPER_CAMERA.NO_BINOCULARS]:
        self._binoculars.resetTextures()
    return result


@override(ModelBoundEffects, 'addNewToNode')
def new__effectsListPlayer(func, *args, **kwargs):
    settings = settings_service.getComponentDict(config)
    if settings[GLOBAL.ENABLED] and kwargs.get('isPlayerVehicle', False):
        if settings[SNIPER_CAMERA.NO_FLASH_BANG] and 'showFlashBang' in kwargs:
            kwargs['showFlashBang'] = False
        if settings[SNIPER_CAMERA.NO_SHOCK_WAVE] and 'showShockWave' in kwargs:
            kwargs['showShockWave'] = False
    return func(*args, **kwargs)


def fini():
    settings_service.onModSettingsChanged.disconnect(controller.onSettingsChanged)
    controller.dispose()
