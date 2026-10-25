# -*- coding: utf-8 -*-
"""Observe native markers only. No Flash replacement or external statistics."""
from driftkings.core.vehicle_markers.hooks import Hooks


class Diagnostics(object):
    def __init__(self, logger, debug):
        self.logger = logger
        self.debug = debug
        self.hooks = Hooks(logger)
        self.managers = {}
        self.health_events = 0
        self.active = False

    def install(self, manager, plugin):
        if self.active:
            return
        self.active = True
        try:
            self.hooks.after(manager, '_populate', self.populated)
            self.hooks.after(manager, 'createMarker', self.created)
            self.hooks.after(manager, 'destroyMarker', self.destroyed)
            self.hooks.after(manager, '_dispose', self.disposed)
            self.hooks.after(plugin, '_updateVehicleHealth', self.health)
        except Exception:
            self.close()
            raise

    def supported(self, manager):
        return type(manager).__name__ != 'KillCamMarkersManager'

    def state(self, manager):
        return self.managers.setdefault(id(manager), {'created': 0, 'destroyed': 0, 'live': set()})

    def populated(self, result, manager, *args, **kwargs):
        if self.active and self.supported(manager):
            self.state(manager)
            self.logger.info('[Driftkings.VehicleMarkers] Native marker manager populated')

    def created(self, result, manager, *args, **kwargs):
        if not self.active or not self.supported(manager):
            return
        state = self.state(manager)
        state['created'] += 1
        state['live'].add(result)
        if self.debug and state['created'] <= 3:
            self.logger.info('[Driftkings.VehicleMarkers] Marker created id=%s symbol=%s', result,
                             args[0] if args else kwargs.get('symbol'))

    def destroyed(self, result, manager, markerID, *args, **kwargs):
        if not self.active or not self.supported(manager):
            return
        state = self.state(manager)
        state['destroyed'] += 1
        state['live'].discard(markerID)

    def health(self, result, plugin, *args, **kwargs):
        if not self.active:
            return
        self.health_events += 1
        if self.debug and self.health_events <= 3:
            self.logger.info('[Driftkings.VehicleMarkers] Native health update observed (%s)', self.health_events)

    def disposed(self, result, manager, *args, **kwargs):
        state = self.managers.pop(id(manager), None)
        if self.active and state is not None:
            self.logger.info('[Driftkings.VehicleMarkers] Manager disposed: created=%s destroyed=%s remaining=%s',
                             state['created'], state['destroyed'], len(state['live']))
        if not self.managers:
            self.health_events = 0

    def close(self):
        was_active = self.active
        self.active = False
        tracked = len(self.managers)
        markers = sum(len(state['live']) for state in self.managers.values())
        restored, retained = self.hooks.clear()
        self.managers.clear()
        self.health_events = 0
        if was_active:
            self.logger.info('[Driftkings.VehicleMarkers] Diagnostics closed: manager records released=%s; marker IDs released=%s; hooks restored=%s; hooks retained in other mod chains=%s',
                             tracked, markers, restored, retained)
