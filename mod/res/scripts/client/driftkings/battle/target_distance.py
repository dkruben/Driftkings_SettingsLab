# -*- coding: utf-8 -*-
from AvatarInputHandler import AvatarInputHandler
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin

from driftkings._constants import GLOBAL
from driftkings.core.hooks import override
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.target_distance import TargetDistanceSettings as Settings
from driftkings.settings.service import settings_service
from driftkings.flash.battle.target_distance import ALIAS, DistanceMarkerController, DistanceMarkerView

LOG = get_logger('driftkings.battle.target_distance')

g_distanceMarker = None
config = Settings()


@override(AvatarInputHandler, 'handleMouseEvent')
def handleMouseEvent(func, self, event):
    result = func(self, event)
    if g_distanceMarker is not None:
        DistanceMarkerController.onMouseEvent(event.dx, event.dy)
    return result


@override(VehicleMarkerPlugin, 'start')
def start(func, self):
    func(self)
    try:
        global g_distanceMarker
        if g_distanceMarker is None and settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            g_distanceMarker = DistanceMarkerController(self._clazz)
    except Exception as e:
        LOG.error(('Failed to create distance marker app: {}').format(e) , exc_info=True)


@override(VehicleMarkerPlugin, 'stop')
def stop(func, self):
    func(self)
    try:
        global g_distanceMarker
        if g_distanceMarker is not None:
            g_distanceMarker.close()
            g_distanceMarker = None
    except Exception as e:
        LOG.error(('Failed to close distance marker app: {}').format(e) , exc_info=True)


def fini():
    global g_distanceMarker
    if g_distanceMarker is not None:
        g_distanceMarker.close()
        g_distanceMarker = None


def getBattleViews():
    return ((ALIAS, DistanceMarkerView, config),)
