# -*- coding: utf-8 -*-
"""Functional vehicle marker settings; Flash integration lives in its adapter."""
from driftkings.core.vehicle_markers.config import prepare
from driftkings.flash.battle.vehicle_markers.runtime import start as start_presentation
from driftkings.flash.battle.vehicle_markers.runtime import stop
from driftkings.settings.definitions.battle.vehicle_markers import VehicleMarkersSettings
from driftkings.settings.service import settings_service

vehicle_markers_settings = VehicleMarkersSettings()


# Prepara as configurações e inicia a apresentação dos marcadores dos veículos.
def start():
    start_presentation(prepare(settings_service.getComponentDict(vehicle_markers_settings)), vehicle_markers_settings)


# Reinicia os marcadores com as configurações aplicadas.
def changed(component, changes):
    start()


# Inicializa o módulo de marcadores dos veículos.
def init():
    settings_service.onModSettingsChanged.connect(changed, vehicle_markers_settings)
    start()


# Liberta os recursos do módulo de marcadores dos veículos.
def fini():
    settings_service.onModSettingsChanged.disconnect(changed)
    stop()
