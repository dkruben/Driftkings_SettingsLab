# -*- coding: utf-8 -*-
from AvatarInputHandler import AvatarInputHandler
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin

from Driftkings._constants import GLOBAL
from Driftkings.common import logError
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.distance_marker import DistanceMarkerSettings as ConfigInterface
from Driftkings.views.battle.distance_marker import DistanceMarkerController, DistanceMarkerView, ALIAS

g_distanceMarker = None
config = ConfigInterface()


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
        logError(config.ID, 'Failed to create distance marker app: {}', e, exc_info=True)


@override(VehicleMarkerPlugin, 'stop')
def stop(func, self):
    func(self)
    try:
        global g_distanceMarker
        if g_distanceMarker is not None:
            g_distanceMarker.close()
            g_distanceMarker = None
    except Exception as e:
        logError(config.ID, 'Failed to close distance marker app: {}', e, exc_info=True)


def fini():
    global g_distanceMarker
    if g_distanceMarker is not None:
        g_distanceMarker.close()
        g_distanceMarker = None


def getBattleViews():
    return ((ALIAS, DistanceMarkerView, config),)
