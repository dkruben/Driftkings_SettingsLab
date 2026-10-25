# -*- coding: utf-8 -*-
"""Integrated vehicle markers; settings are edited in the hangar and applied next battle."""
import ResMgr

from driftkings.core.vehicle_markers.compatibility import manager_supported
from driftkings.core.vehicle_markers.config import prepare
from driftkings.core.vehicle_markers.diagnostics import Diagnostics
from driftkings.core.vehicle_markers.presentation import Presentation
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.vehicle_markers import VehicleMarkersSettings
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.VehicleMarkers')
config = VehicleMarkersSettings()
_controller = None
_presentation = None


def stop():
    global _controller, _presentation
    if _presentation is not None:
        _presentation.close()
        _presentation = None
    if _controller is not None:
        _controller.close()
        _controller = None


def start():
    global _controller, _presentation
    stop()
    data = prepare(settings_service.getComponentDict(config))
    if not data['enabled']:
        return
    if ResMgr.isFile('scripts/client/gui/mods/mod_vm_test.pyc'):
        LOG.warning('Standalone VM_TEST is installed; remove it before using integrated markers')
        return
    from gui.Scaleform.daapi.view.battle.shared.markers2d.manager import MarkersManager
    from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
    try:
        _controller = Diagnostics(LOG, data['debug'])
        _controller.install(MarkersManager, VehicleMarkerPlugin)
        if data['markers']['enabled']:
            _presentation = Presentation(LOG, data['markers'], data['customFields'], supported=manager_supported)
            _presentation.install(MarkersManager)
        LOG.info('Integrated markers ready')
    except Exception:
        stop()
        raise


def changed(component, changes):
    start()


def init():
    settings_service.onModSettingsChanged.connect(changed, config)
    start()


def fini():
    settings_service.onModSettingsChanged.disconnect(changed)
    stop()
