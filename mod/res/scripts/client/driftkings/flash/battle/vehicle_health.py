# -*- coding: utf-8 -*-
"""Health transport for the bar parented to the native consumables panel."""
from importlib import import_module
import weakref

from driftkings._constants import GLOBAL, VEHICLE_HEALTH
from driftkings.common.utils.formatting import percentToRgb
from driftkings.flash.battle.meta.vehicle_health import AmmoHealthMeta
from driftkings.settings.service import settings_service

_views = weakref.WeakSet()


def refresh_views(*args):
    for view in tuple(_views):
        view.refresh()


class AmmoHealthView(AmmoHealthMeta):

    def _populate(self):
        super(AmmoHealthView, self)._populate()
        _views.add(self)
        settings_service.onModSettingsChanged.connect(self.refresh, VEHICLE_HEALTH)
        self.refresh()

    def _dispose(self):
        settings_service.onModSettingsChanged.disconnect(self.refresh)
        _views.discard(self)
        super(AmmoHealthView, self)._dispose()

    def refresh(self, *args):
        component = import_module('driftkings.battle.vehicle_health')
        settings = settings_service.getComponentDict(component.vehicle_health_settings)
        state = component.tracker.state
        style = settings.get(VEHICLE_HEALTH.STYLE, 0)
        maximum, current = state['maximum'], state['current']
        percent = float(current) / maximum if maximum > 0 else 0.0
        enabled = bool(settings[GLOBAL.ENABLED] and 5 <= style <= 7
                       and state['battle'] and state['alive'] and maximum > 0)
        color = percentToRgb(percent, **settings[VEHICLE_HEALTH.AVG_COLOR])
        self._sendChanged('as_setHealth', percent, '%d / %d' % (current, maximum),
                          int(color[1:], 16), style - 5, enabled)
