# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, MINIMAP_PLUGINS
from Driftkings.settings.service import settings_service
"""Presentation adapter for MinimapPlugins; gameplay state stays in its component."""
from Driftkings.common import xvmInstalled
from Driftkings.common.utils.game import checkKeys
from Driftkings.core.callbacks import callback, cancelCallback
from Driftkings.meta.battle.minimap import MinimapMeta
from Driftkings.ui.common.events import g_events

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.battle.minimap')


class MinimapCentredView(MinimapMeta):
    def __init__(self):
        super(MinimapCentredView, self).__init__(_component().config.ID)
        self._releaseCallback = None


    def _populate(self):
        # noinspection PyProtectedMember
        super(MinimapCentredView, self)._populate()
        g_events.onAltKey += self.onAltKey
        _component().VIEWS.add(self)
        _component().controller.activate()
        self.onAltKey(_component().controller.minimapZoom)
        for plugin in list(_component().VEHICLES):
            for payload in plugin._presentations.values():
                self.onVehicleData(payload)
        for plugin in list(_component().PERSONAL):
            if hasattr(plugin, '_ranges'):
                self.onRanges(plugin._ranges)

    def _dispose(self):
        # AS disposal restores zoom; arena data may already be gone here.
        if self._releaseCallback is not None:
            cancelCallback(self._releaseCallback)
            self._releaseCallback = None
        _component().VIEWS.discard(self)
        if not _component().VIEWS:
            _component().controller.deactivate()
        g_events.onAltKey -= self.onAltKey
        # noinspection PyProtectedMember
        super(MinimapCentredView, self)._dispose()

    def _checkRelease(self):
        self._releaseCallback = None
        from Driftkings.settings.registry import registry
        if not _component().controller._active:
            return
        if registry.isOpen or not checkKeys(settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.BUTTON]):
            _component().controller.setAlternative(False)
        elif _component().controller.minimapZoom:
            self._releaseCallback = callback(0.1, self._checkRelease)

    def onAltKey(self, pressed):
        if self._releaseCallback is not None:
            cancelCallback(self._releaseCallback)
            self._releaseCallback = None
        if pressed:
            self._releaseCallback = callback(0.1, self._checkRelease)
        if xvmInstalled:
            return
        # Epic's segmented map keeps its native positioning; labels still switch.
        options = dict(settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.PRESENTATION])
        data = settings_service.getComponentDict(_component().config)
        for section in ('icons', 'health', 'lostMarker', 'mapSize', 'circles', 'extraCircles'):
            options[section] = data[section]
        visitor = _component().controller.sessionProvider.arenaVisitor
        bottom, top = visitor.type.getBoundingBox()
        options['mapWidth'], options['mapHeight'] = int(top[0] - bottom[0]), int(top[1] - bottom[1])
        info = _component().controller.sessionProvider.getArenaDP().getVehicleInfo()
        options['vehicleClass'] = info.vehicleType.classTag
        options.update(enabled=settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED],
                       alternative=bool(pressed),
                       zoom=bool(options['zoom'] and _component().controller.notEpicBattle),
                       scale=min(settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.ZOOM_FACTOR], settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.ZOOM_FACTOR_MAX]),
                       labels=settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.LABELS],
                       lines=settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.LINES],
                       artilleryAim=settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.ARTILLERY_AIM],
                       showVehicleTypes=settings_service.getComponentDict(_component().config)[MINIMAP_PLUGINS.SHOW_VEHICLE_TYPES]
                       )
        self.as_minimapPresentationS(options)

    def onVehicleData(self, payload):
        if not xvmInstalled:
            self.as_minimapVehicleS(payload)

    def onRanges(self, payload):
        if not xvmInstalled:
            self.as_minimapRangesS(payload)
