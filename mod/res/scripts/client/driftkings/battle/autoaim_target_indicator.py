# -*- coding: utf-8 -*-
"""Display a box for the native locked target; never acquire or steer aim."""
import math

from AvatarInputHandler import cameras
import BigWorld
import Math
from Vehicle import Vehicle

from driftkings._constants import AUTOAIM_TARGET_INDICATOR, GLOBAL, ScreenBounds
from driftkings.core.battle_events import battleEvents
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.flash.core import Align, ElementType, overlays
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.autoaim_target_indicator import AutoaimTargetIndicatorSettings
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.AutoAimOptimize')
BOX_COLOR = '#F98600'
BOX_THICKNESS = 2
UPDATE_INTERVAL = 0.05


class AutoAimController(object):
    def __init__(self, config):
        self.config = config
        # Compatibility state is inert; input and targeting belong to WoT.
        self.lockRequest = False
        self.lockRelease = False
        self.optimizedTargetID = None
        self.running = False
        self.pending = None
        self.created = False
        self.initialized = False
        self.errorReported = False

    def findTarget(self, player):
        """Legacy API retained without assisted acquisition."""
        return None

    def handleKey(self, original, mode, isDown, key, *args, **kwargs):
        return original(mode, isDown, key, *args, **kwargs)

    @staticmethod
    def calc_radian(target_position, angle, cameraDir, cameraPos):
        # Retained pure compatibility helper; never used for acquisition.
        cameraToTarget = target_position - cameraPos
        if cameraToTarget.lengthSquared <= 0.0:
            return
        dot = cameraToTarget.dot(cameraDir)
        if dot < 0:
            return
        cosine = dot / math.sqrt(cameraToTarget.lengthSquared)
        radian = math.acos(max(-1.0, min(1.0, cosine)))
        if radian > angle:
            return
        return radian

    def init(self):
        if self.initialized:
            return
        self.initialized = True
        battleEvents.started.connect(self.startBattle)
        battleEvents.loaded.connect(self.startBattle)
        battleEvents.ended.connect(self.endBattle)
        battleEvents.acquire(self)

    def fini(self):
        self.endBattle()
        if self.initialized:
            self.initialized = False
            battleEvents.started.disconnect(self.startBattle)
            battleEvents.loaded.disconnect(self.startBattle)
            battleEvents.ended.disconnect(self.endBattle)
            battleEvents.release(self)

    def startBattle(self, *args):
        if not self.running:
            self.running = True
            self.tick()

    def endBattle(self, *args):
        self.running = False
        if self.pending is not None:
            cancelCallback(self.pending)
            self.pending = None
        self.hideBox()
        self.errorReported = False

    def tick(self):
        self.pending = None
        if not self.running:
            return
        try:
            self.updateBox()
            self.errorReported = False
        except Exception:
            self.hideBox()
            if not self.errorReported:
                LOG.exception('Native target box could not be updated')
                self.errorReported = True
        finally:
            if self.running:
                self.pending = callback(UPDATE_INTERVAL, self.tick)

    def hideBox(self):
        if self.created or self.config.NAME in overlays.elements:
            overlays.remove(self.config.NAME)
            self.created = False

    def targetBounds(self, player):
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED]:
            return None
        if player is None or player.isObserver() or not player.isVehicleAlive:
            return None
        vehicle = player.autoAimVehicle
        if (not isinstance(vehicle, Vehicle) or not vehicle.isStarted or
                not vehicle.inWorld or vehicle.isHidden or not vehicle.isAlive()):
            return None
        public_info = vehicle.publicInfo
        if public_info is None:
            return None
        try:
            # WoT exposes a PyFixedDictDataInstance, which has no dict.get().
            team = public_info['team']
        except (KeyError, TypeError):
            return None
        if team is None or team == player.team:
            return None
        # Inspect only the already locked, currently rendered entity.
        descriptor = vehicle.typeDescriptor
        hull = getattr(descriptor, 'hull', None)
        hit_tester = getattr(hull, 'hitTester', None)
        bounds = getattr(hit_tester, 'bbox', None)
        if bounds is None or len(bounds) < 2:
            return None
        bottom, top = bounds[:2]
        world = Math.Matrix(vehicle.matrix)
        projection = cameras.getViewProjectionMatrix()
        camera = cameras.getWorldRayAndPoint(0, 0)[1]
        center = world.applyPoint(descriptor.chassis.hullPosition + (bottom + top) * 0.5)
        if BigWorld.wg_collideSegment(player.spaceID, camera, center, 128) is not None:
            return None
        points = []
        for x in (bottom.x, top.x):
            for y in (bottom.y, top.y):
                for z in (bottom.z, top.z):
                    point = world.applyPoint(descriptor.chassis.hullPosition + Math.Vector3(x, y, z))
                    # Conservative visibility: hide if cover blocks any sample.
                    if BigWorld.wg_collideSegment(player.spaceID, camera, point, 128) is not None:
                        return None
                    clip = projection.applyV4Point(Math.Vector4(point.x, point.y, point.z, 1))
                    if clip.w <= 0:
                        return None
                    sx, sy = clip.x / clip.w, clip.y / clip.w
                    if (math.isnan(sx) or math.isinf(sx) or math.isnan(sy) or math.isinf(sy) or not -1 <= sx <= 1 or not -1 <= sy <= 1):
                        return None
                    points.append(((sx + 1) * BigWorld.screenWidth() * 0.5, (1 - sy) * BigWorld.screenHeight() * 0.5))
        left, right = min(p[0] for p in points), max(p[0] for p in points)
        top_y, bottom_y = min(p[1] for p in points), max(p[1] for p in points)
        if right - left <= BOX_THICKNESS or bottom_y - top_y <= BOX_THICKNESS:
            return None
        return ScreenBounds(left, top_y, right - left, bottom_y - top_y)

    def updateBox(self):
        bounds = self.targetBounds(BigWorld.player())
        if bounds is None:
            self.hideBox()
            return
        x, y, width, height = bounds
        color = settings_service.getComponentDict(self.config).get(AUTOAIM_TARGET_INDICATOR.COLOR, BOX_COLOR)
        if not self.created:
            overlays.create(self.config.NAME, ElementType.PANEL, {
                GLOBAL.ALIGN_X: Align.LEFT, GLOBAL.ALIGN_Y: Align.TOP, GLOBAL.LIMIT: False,
                GLOBAL.WIDTH: GLOBAL.ZERO, GLOBAL.HEIGHT: GLOBAL.ZERO, GLOBAL.ALPHA: GLOBAL.ONE, GLOBAL.DRAG: False})
            for name in (GLOBAL.TOP, GLOBAL.BOTTOM, GLOBAL.LEFT, GLOBAL.RIGHT):
                overlays.create(self.config.NAME + '.' + name, ElementType.PANEL, {
                    GLOBAL.ALIGN_X: Align.LEFT, GLOBAL.ALIGN_Y: Align.TOP, GLOBAL.LIMIT: False,
                    GLOBAL.ALPHA: GLOBAL.ONE, GLOBAL.DRAG: False,
                    'customBackground': {'fill': True, GLOBAL.COLOR: color, GLOBAL.ALPHA: GLOBAL.ONE}})
            self.created = True
        overlays.update(self.config.NAME, {GLOBAL.X: x, 'y': y})
        for name, props in (
                (GLOBAL.TOP, {GLOBAL.X: GLOBAL.ZERO, GLOBAL.Y: GLOBAL.ZERO, GLOBAL.WIDTH: width, GLOBAL.HEIGHT: BOX_THICKNESS}),
                (GLOBAL.BOTTOM, {GLOBAL.X: GLOBAL.ZERO, GLOBAL.Y: height - BOX_THICKNESS, GLOBAL.WIDTH: width, GLOBAL.HEIGHT: BOX_THICKNESS}),
                (GLOBAL.LEFT, {GLOBAL.X: GLOBAL.ZERO, GLOBAL.Y: GLOBAL.ZERO, GLOBAL.WIDTH: BOX_THICKNESS, GLOBAL.HEIGHT: height}),
                (GLOBAL.RIGHT, {GLOBAL.X: width - BOX_THICKNESS, GLOBAL.Y: GLOBAL.ZERO, GLOBAL.WIDTH: BOX_THICKNESS, GLOBAL.HEIGHT: height})):
            props['customBackground'] = {'fill': True, GLOBAL.COLOR: color, GLOBAL.ALPHA: GLOBAL.ONE}
            overlays.update(self.config.NAME + '.' + name, props)


autoaim_target_indicator_settings = AutoaimTargetIndicatorSettings()
controller = AutoAimController(autoaim_target_indicator_settings)


def init():
    controller.init()


def fini():
    controller.fini()
