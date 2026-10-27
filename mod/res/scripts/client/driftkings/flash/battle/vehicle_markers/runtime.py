# -*- coding: utf-8 -*-
"""Integrated vehicle markers; settings are edited in the hangar and applied next battle."""
import BigWorld
import ResMgr

from driftkings.core.vehicle_markers.compatibility import manager_supported
from driftkings.core.vehicle_markers.context import context
from driftkings.core.vehicle_markers.diagnostics import Diagnostics
from driftkings.flash.battle.vehicle_markers.presentation import Presentation
from driftkings.flash.battle.vehicle_markers.ratings import Ratings
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.VehicleMarkers')

_controller = None
_presentation = None
_ratings = None


def stop():
    global _controller, _presentation, _ratings
    if _ratings is not None:
        _ratings.close()
        _ratings = None
    if _presentation is not None:
        _presentation.close()
        _presentation = None
    if _controller is not None:
        _controller.close()
        _controller = None


def start(data, config):
    global _controller, _presentation, _ratings
    stop()
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
            data['customFields']['blownUp'] = config.i18n['UI_preview_blowup']
            _presentation = Presentation(LOG, data['markers'], data['customFields'], supported=manager_supported)
            _presentation.install(MarkersManager)
            from driftkings._constants import TEAM_PANELS
            from driftkings.core import player_ratings
            stats = player_ratings.shared()
            _ratings = Ratings(LOG, stats, data, lambda: getattr(BigWorld.player(), 'arena', None),
                               BigWorld.callback, BigWorld.cancelCallback, manager_supported,
                               lambda: settings_service.getComponentDict(player_ratings.config)[TEAM_PANELS.PERFORMANCE]['minBattlesToShow'],
                               lambda ident, vehicle, distance: context(BigWorld.player(), BigWorld.entity, ident, vehicle, distance))
            _ratings.install(MarkersManager)
        LOG.info('Integrated markers ready')
    except Exception:
        stop()
        raise


