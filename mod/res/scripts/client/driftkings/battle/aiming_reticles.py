# -*- coding: utf-8 -*-
import aih_constants
from aih_constants import GUN_MARKER_FLAG
import AvatarInputHandler
from AvatarInputHandler.gun_marker_ctrl import _SPGGunMarkerController
import BattleReplay
import BigWorld
from constants import AIMING_MODE, SERVER_TICK_LENGTH
from gui.Scaleform.daapi.view.battle.shared.crosshair import gm_factory
from helpers import dependency
import Math
from skeletons.account_helpers.settings_core import ISettingsCache, ISettingsCore
import VehicleGunRotator

from driftkings._constants import AIMING_RETICLES, GLOBAL
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.hooks import override
from driftkings.game_constants import ARENA_PERIOD, CTRL_MODE_NAME, GUN_MARKER_TYPE
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.aiming_reticles import AimingReticlesSettings
from driftkings.settings.service import affects, settings_service

LOG = get_logger('driftkings.battle.aiming_reticles')

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
        self._originalLinkages = get_linkages()
        self._customLinkages = dict(CUSTOM_GUN_MARKER_LINKAGES)
        self._customLinkages.update(self._originalLinkages)
        self.active = True
        try:
            self.applySettings()
            settings_service.onModSettingsChanged.connect(self.onModSettingsChanged, AIMING_RETICLES)
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
        set_linkages(self._originalLinkages)
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
        if full or affects(changes, AIMING_RETICLES.GUN_MARKER_MINIMUM_SIZE):
            aih_constants.GUN_MARKER_MIN_SIZE = data[AIMING_RETICLES.GUN_MARKER_MINIMUM_SIZE] if enabled else self._originalMinSize
        if full or affects(changes, AIMING_RETICLES.PERCENT_CORRECTION):
            correction = data[AIMING_RETICLES.PERCENT_CORRECTION] / 100.0 if enabled else 0
            self.reticleScaleFactor = 1.71 * correction + (1 - correction)
        if full or affects(changes, AIMING_RETICLES.SHOW_CLIENT_AND_SERVER_RETICLE_BETA):
            self.showClientAndServerReticle = bool(enabled and data[AIMING_RETICLES.SHOW_CLIENT_AND_SERVER_RETICLE_BETA])
            set_linkages(self._customLinkages if self.showClientAndServerReticle else self._originalLinkages)
            if not self.showClientAndServerReticle:
                self.cancelServerAiming()
        for field, key in (('gunTag', AIMING_RETICLES.SERVER_RETICLE_GUN_MARKER_OPACITY),
                           ('gunTagType', AIMING_RETICLES.SERVER_RETICLE_GUN_MARKER_SHAPE),
                           ('mixing', AIMING_RETICLES.SERVER_RETICLE_AIMING_CIRCLE_OPACITY),
                           ('mixingType', AIMING_RETICLES.SERVER_RETICLE_AIMING_CIRCLE_SHAPE)):
            if full or affects(changes, key):
                self.customServerReticleSettings[field] = data[key]
        if full or affects(changes, AIMING_RETICLES.SHOW_SERVER_SPG_STRATEGIC_RETICLE):
            self.enableSpgStrategicReticle = bool(enabled and data[AIMING_RETICLES.SHOW_SERVER_SPG_STRATEGIC_RETICLE])

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


from driftkings.flash.battle.aiming_reticles import CUSTOM_GUN_MARKER_LINKAGES, get_linkages, set_linkages, set_state

aiming_reticles_settings = AimingReticlesSettings()
reticle = ReticleState(aiming_reticles_settings)
set_state(reticle)


def init():
    reticle.start()


def fini():
    reticle.stop()


def _scaleGunMarkerInfo(gunMarkerInfo):
    if gunMarkerInfo is None or reticle.reticleScaleFactor == 1:
        return gunMarkerInfo
    return gunMarkerInfo._replace(
        size=gunMarkerInfo.size / reticle.reticleScaleFactor,
        dualAccSize=gunMarkerInfo.dualAccSize / reticle.reticleScaleFactor)


@override(_SPGGunMarkerController, '_updateDispersionData')
def new_SPGGunMarkerController_updateDispersionData(original, self):
    # Let the client retain its replay recording and playback side effects.
    result = original(self)
    if reticle.reticleScaleFactor != 1:
        dispersionAngle = self._gunRotator.dispersionAngle
        replay = BattleReplay.g_replayCtrl
        if replay.isPlaying and replay.isClientReady:
            recordedAngle, recordedSize = replay.getSPGGunMarkerParams()
            if recordedAngle != -1.0 and recordedSize != -1.0:
                dispersionAngle = recordedAngle
        # SPG contours are projected from a ballistic cone, not only from the
        # marker diameter. Both must use the same correction on sloped terrain.
        self._dataProvider.setupConicDispersion(dispersionAngle / reticle.reticleScaleFactor)
    return result


@override(AvatarInputHandler.AvatarInputHandler, 'updateClientGunMarker')
def new_AvatarInputHandler_updateClientGunMarker(func, self, gunMarkerInfo, supportMarkersInfo, relaxTime):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.ARTY, CTRL_MODE_NAME.SNIPER):
        gunMarkerInfo = _scaleGunMarkerInfo(gunMarkerInfo)
    return func(self, gunMarkerInfo, supportMarkersInfo, relaxTime)


@override(AvatarInputHandler.AvatarInputHandler, 'updateServerGunMarker')
def new_AvatarInputHandler_updateServerGunMarker(func, self, gunMarkerInfo, supportMarkersInfo, relaxTime):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.ARTY, CTRL_MODE_NAME.SNIPER):
        gunMarkerInfo = _scaleGunMarkerInfo(gunMarkerInfo)
    return func(self, gunMarkerInfo, supportMarkersInfo, relaxTime)


@override(AvatarInputHandler.AvatarInputHandler, 'updateDualAccGunMarker')
def new_AvatarInputHandler_updateDualAccGunMarker(func, self, gunMarkerInfo, supportMarkersInfo, relaxTime):
    if self.ctrlModeName in (CTRL_MODE_NAME.ARCADE, CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.ARTY, CTRL_MODE_NAME.SNIPER):
        gunMarkerInfo = _scaleGunMarkerInfo(gunMarkerInfo)
    func(self, gunMarkerInfo, supportMarkersInfo, relaxTime)


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
