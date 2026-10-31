# -*- coding: utf-8 -*-
from AvatarInputHandler import AvatarInputHandler
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin

from driftkings._constants import GLOBAL
from driftkings.core.hooks import override
from driftkings.flash.battle.target_distance import ALIAS, DistanceMarkerController, DistanceMarkerView
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.target_distance import TargetDistanceSettings
from driftkings.settings.service import settings_service

LOG = get_logger('driftkings.battle.target_distance')

g_distanceMarker = None
target_distance_settings = TargetDistanceSettings()


# Atualiza o marcador de distância após o movimento nativo do rato.
@override(AvatarInputHandler, 'handleMouseEvent')
def handleMouseEvent(func, self, event):
    result = func(self, event)
    if g_distanceMarker is not None:
        DistanceMarkerController.onMouseEvent(event.dx, event.dy)
    return result


# Cria e ativa o controlador da distância ao iniciar a interface de batalha.
@override(VehicleMarkerPlugin, 'start')
def start(func, self):
    func(self)
    try:
        global g_distanceMarker
        if g_distanceMarker is None and settings_service.getComponentDict(target_distance_settings)[GLOBAL.ENABLED]:
            g_distanceMarker = DistanceMarkerController(self._clazz)
    except Exception as e:
        LOG.error(('Failed to create distance marker app: {}').format(e) , exc_info=True)


# Encerra o controlador da distância ao destruir a interface de batalha.
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


# Liberta os recursos do módulo de distância ao alvo.
def fini():
    global g_distanceMarker
    if g_distanceMarker is not None:
        g_distanceMarker.close()
        g_distanceMarker = None


# Declara os componentes visuais do módulo de distância ao alvo.
def getBattleViews():
    return ((ALIAS, DistanceMarkerView, target_distance_settings),)
