# -*- coding: utf-8 -*-
"""Apply functional marker options at the native Flash manager boundary."""
import copy

from driftkings.core.vehicle_markers.hooks import Hooks
from driftkings.core.vehicle_markers.presentation import apply


class Presentation(object):
    def __init__(self, logger, options, fields=None, supported=None):
        self.logger = logger
        self.options = options
        self.fields = fields
        self.supported = supported
        self.skipped = set()
        self.hooks = Hooks(logger)
        self.active = False
        self.reported = False

    def install(self, manager):
        if self.active:
            return
        self.active = True
        try:
            self.hooks.around(manager, 'setMarkerSettings', self.configure)
        except Exception:
            self.close()
            raise

    def configure(self, original, manager, settings, *args, **kwargs):
        if not self.active:
            return original(manager, settings, *args, **kwargs)
        allowed = type(manager).__name__ != 'KillCamMarkersManager'
        if self.supported is not None:
            try:
                allowed = allowed and self.supported(manager)
            except Exception:
                allowed = False
                self.logger.exception('[Driftkings.VehicleMarkers] Cannot identify battle mode; keeping native settings')
        if not allowed:
            configured = copy.deepcopy(settings)
            if isinstance(configured, dict):
                # Explicitly clear our Flash payload if a movie/domain is reused.
                configured['__vmTest'] = None
            if type(manager).__name__ not in self.skipped:
                self.skipped.add(type(manager).__name__)
                self.logger.info('[Driftkings.VehicleMarkers] Native presentation retained for unsupported battle/manager: %s', type(manager).__name__)
            return original(manager, configured, *args, **kwargs)
        try:
            configured = apply(settings, self.options, self.fields)
        except Exception:
            self.logger.exception('[Driftkings.VehicleMarkers] Invalid native marker data; retaining original settings')
            configured = settings
        result = original(manager, configured, *args, **kwargs)
        if not self.reported:
            self.reported = True
            self.logger.info('[Driftkings.VehicleMarkers] JSON presentation applied to native markers (normal/Alt)')
        return result

    def close(self):
        self.active = False
        restored, retained = self.hooks.clear()
        self.logger.info('[Driftkings.VehicleMarkers] Presentation closed: hooks restored=%s; retained in other mod chains=%s', restored, retained)
