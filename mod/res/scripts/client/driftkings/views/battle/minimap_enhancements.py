# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, MINIMAP_ENHANCEMENTS
from driftkings.settings.service import settings_service
"""Presentation adapter for MinimapPlugins; gameplay state stays in its component."""
from aih_constants import CTRL_MODE_NAME
from gui.battle_control.avatar_getter import getInputHandler

from driftkings.common.utils.wgutils import isXvmInstalled
from driftkings.common.utils.game import checkKeys
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.meta.battle.minimap import MinimapMeta
from driftkings.ui.common.events import g_events

from importlib import import_module

# The client updates its strategic camera entry, which carries the artillery reticle, only in these modes.
STRATEGIC_MODES = (CTRL_MODE_NAME.STRATEGIC, CTRL_MODE_NAME.ARTY)


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.battle.minimap_enhancements')


class MinimapEnhancementsView(MinimapMeta):
    def __init__(self):
        super(MinimapEnhancementsView, self).__init__(_component().config.NAME)
        self._releaseCallback = None


    def _populate(self):
        # noinspection PyProtectedMember
        super(MinimapEnhancementsView, self)._populate()
        g_events.onAltKey += self.onAltKey
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged += self.onCameraChanged
            self.onCameraChanged(getattr(handler, 'ctrlModeName', None))
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
        handler = getInputHandler()
        if handler is not None and hasattr(handler, 'onCameraChanged'):
            handler.onCameraChanged -= self.onCameraChanged
        # noinspection PyProtectedMember
        super(MinimapEnhancementsView, self)._dispose()

    def _checkRelease(self):
        self._releaseCallback = None
        from driftkings.settings.registry import registry
        if not _component().controller._active:
            return
        if registry.isOpen or not checkKeys(settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.BUTTON]):
            _component().controller.setAlternative(False)
        elif _component().controller.minimapZoom:
            self._releaseCallback = callback(0.1, self._checkRelease)

    def onAltKey(self, pressed):
        if self._releaseCallback is not None:
            cancelCallback(self._releaseCallback)
            self._releaseCallback = None
        if pressed:
            self._releaseCallback = callback(0.1, self._checkRelease)
        if isXvmInstalled():
            return
        # Epic's segmented map keeps its native positioning; labels still switch.
        options = dict(settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.PRESENTATION])
        data = settings_service.getComponentDict(_component().config)
        for section in ('icons', 'health', 'lostMarker', 'mapSize', 'circles', 'extraCircles', 'nearby'):
            options[section] = data[section]
        visitor = _component().controller.sessionProvider.arenaVisitor
        bottom, top = visitor.type.getBoundingBox()
        options['mapWidth'], options['mapHeight'] = int(top[0] - bottom[0]), int(top[1] - bottom[1])
        info = _component().controller.sessionProvider.getArenaDP().getVehicleInfo()
        options['vehicleClass'] = info.vehicleType.classTag
        options.update(enabled=settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED],
                       alternative=bool(pressed),
                       zoom=bool(options['zoom'] and _component().controller.notEpicBattle),
                       scale=min(settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.ZOOM_FACTOR], settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.ZOOM_FACTOR_MAX]),
                       labels=settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.LABELS],
                       lines=settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.LINES],
                       artilleryAim=settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.ARTILLERY_AIM],
                       showVehicleTypes=settings_service.getComponentDict(_component().config)[MINIMAP_ENHANCEMENTS.SHOW_VEHICLE_TYPES]
                       )
        self.as_minimapPresentationS(options)

    def onCameraChanged(self, ctrlMode, _=None):
        self.as_minimapCameraS(ctrlMode in STRATEGIC_MODES)

    def onVehicleData(self, payload):
        if not isXvmInstalled():
            self.as_minimapVehicleS(payload)

    def onRanges(self, payload):
        if not isXvmInstalled():
            self.as_minimapRangesS(payload)
