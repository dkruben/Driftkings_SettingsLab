# -*- coding: utf-8 -*-
"""Native marker lifecycle and deduplicated statistics payload transport."""
import json
import re
import weakref

from driftkings.core.vehicle_markers.hooks import Hooks
from driftkings.core.vehicle_markers.ratings import values


class Ratings(object):
    def __init__(self, logger, stats, settings, arena, schedule, cancel, supported, minimum, context=None):
        self.logger, self.stats, self.settings = logger, stats, settings
        self.arena, self.schedule, self.cancel = arena, schedule, cancel
        self.supported, self.minimum = supported, minimum
        self.hooks = Hooks(logger)
        self.managers = {}
        self.callback = None
        self.active = False
        self.failed = False
        self.context = context or (lambda *args: {})
        self.distance = bool(re.search(r'\{\{[^{}]*\b(?:distance|dist)\b', json.dumps(settings.get('customFields', {}))))
        self.ticks = 0

    def install(self, manager):
        self.active = True
        self.stats.acquire(self)
        try:
            self.hooks.after(manager, '_populate', self.populated)
            self.hooks.after(manager, '_dispose', self.disposed)
            self.hooks.after(manager, 'setMarkerSettings', self.invalidated)
        except Exception:
            self.close()
            raise

    def populated(self, result, manager, *args, **kwargs):
        if self.active and self.supported(manager):
            self.managers[id(manager)] = [weakref.ref(manager), None]
            if self.callback is None:
                self.ticks = 0
                self.callback = self.schedule(0, self.tick)

    def disposed(self, result, manager, *args, **kwargs):
        self.managers.pop(id(manager), None)
        if not self.managers and self.callback is not None:
            self.cancel(self.callback)
            self.callback = None

    def invalidated(self, result, manager, *args, **kwargs):
        record = self.managers.get(id(manager))
        if record is not None:
            record[1] = None

    def tick(self):
        self.callback = None
        if not self.active:
            return
        try:
            arena = self.arena()
            if not self.distance or self.ticks % 5 == 0:
                self.stats.loadStats()
            self.ticks += 1
            rows = []
            if arena is not None and arena.vehicles:
                # One synchronous roster operation; keep dynamic context per vehicle.
                enabled = self.stats.enabled()
                minimum = self.minimum()
                rating = self.settings.get('ratingType', 'wn8')
                scale = self.settings.get('colorRating', 0)
                for ident, vehicle in sorted(arena.vehicles.items()):
                    info = self.stats.getPlayersInfo(vehicle.get('accountDBID', 0)) if enabled else None
                    row = values(info, rating, scale, minimum, bool(vehicle.get('isAnonymized')))
                    row.update(self.context(ident, vehicle, self.distance))
                    rows.append({'name': vehicle.get('name', ''), 'values': row})
            for key, record in list(self.managers.items()):
                manager = record[0]()
                if manager is None:
                    self.managers.pop(key, None)
                elif self.supported(manager) and manager._isDAAPIInited() and record[1] != rows:
                    manager.as_setMarkerSettingsS({'__vmRatings': rows})
                    record[1] = rows
            self.failed = False
        except Exception:
            if not self.failed:
                self.logger.exception('Could not refresh vehicle marker statistics')
            self.failed = True
        if self.active and self.managers:
            self.callback = self.schedule(.2 if self.distance else 1, self.tick)

    def close(self):
        self.active = False
        if self.callback is not None:
            self.cancel(self.callback)
        self.callback = None
        self.managers.clear()
        self.hooks.clear()
        self.stats.release(self)
