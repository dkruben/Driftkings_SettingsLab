# -*- coding: utf-8 -*-
"""Functional vehicle marker settings; Flash integration lives in its adapter."""
from driftkings.core.vehicle_markers.config import prepare
from driftkings.flash.batalha.vehicle_markers.runtime import start as start_presentation, stop
from driftkings.settings.definitions.battle.vehicle_markers import VehicleMarkersSettings
from driftkings.settings.service import settings_service

config = VehicleMarkersSettings()


def start():
    start_presentation(prepare(settings_service.getComponentDict(config)), config)


def changed(component, changes):
    start()


def init():
    settings_service.onModSettingsChanged.connect(changed, config)
    start()


def fini():
    settings_service.onModSettingsChanged.disconnect(changed)
    stop()
