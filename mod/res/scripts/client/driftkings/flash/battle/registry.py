# -*- coding: utf-8 -*-
"""Publish our battle package; the client owns view registration and lifecycle."""
import weakref

from driftkings.interface_catalog import FLASH_COMPONENTS, FLASH_LIBRARY
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Views')

BATTLE_COMPONENTS = {}
BATTLE_HANDLERS = weakref.WeakSet()


class BattleViews(object):
    def __init__(self, registration=None, visibility=None):
        self.registration = registration
        self.visibility = visibility
        self.definitions = {}
        self.active = False
        self._pendingStop = []

    def register(self, alias, view, config):
        spec = FLASH_COMPONENTS.get(alias)
        if spec is None or getattr(view, 'FLASH_CLASS', None) != spec['as3']:
            raise ValueError('Unknown or mismatched Flash contract: ' + alias)
        if getattr(config, 'NAME', None) != spec['section']:
            raise ValueError('Wrong settings section for Flash component: ' + alias)
        if alias in self.definitions:
            raise ValueError('Duplicate battle component: ' + alias)
        self.definitions[alias] = (view, config)

    def start(self):
        if self._pendingStop:
            raise RuntimeError('Battle view cleanup is pending; retry stop before start')
        if self.active:
            return
        if self.registration is None:
            from driftkings.core.hud_visibility import hudVisibility
            from driftkings.flash.battle.overlay import ALIAS, OverlayConfig, OverlayView
            self.visibility = hudVisibility
            self.registration = BattlePackageRegistration()
            self.register(ALIAS, OverlayView, OverlayConfig())
        try:
            if self.visibility is not None:
                self.visibility.start()
            self.registration.install(self.definitions)
            self.active = True
        except Exception:
            # Partial installation uses the same recoverable teardown as stop.
            self.active = True
            self.stop()
            raise

    def stop(self):
        if self.active:
            self.active = False
            self._pendingStop = [self.registration.uninstall]
            if self.visibility is not None:
                self._pendingStop.append(self.visibility.stop)
        error = None
        for cleanup in tuple(self._pendingStop):
            try:
                cleanup()
            except Exception as failure:
                LOG.exception('Could not finish battle view cleanup: %s', cleanup)
                if error is None:
                    error = failure
            else:
                self._pendingStop.remove(cleanup)
        if error is not None:
            raise error


class BattlePackageRegistration(object):
    PACKAGE = 'driftkings.flash.battle'
    SWF = FLASH_LIBRARY

    def __init__(self):
        self.addedPackages = []
        self.addedLibrary = False
        self.pendingHandlers = set()

    def install(self, definitions):
        from constants import ARENA_GUI_TYPE
        from gui.override_scaleform_views_manager import g_overrideScaleFormViewsConfig
        from gui.Scaleform.required_libraries_config import BATTLE_REQUIRED_LIBRARIES
        BATTLE_COMPONENTS.clear()
        BATTLE_COMPONENTS.update(definitions)
        if self.SWF not in BATTLE_REQUIRED_LIBRARIES:
            BATTLE_REQUIRED_LIBRARIES.append(self.SWF)
            self.addedLibrary = True
        packagesByMode = g_overrideScaleFormViewsConfig.battlePackages
        # Include extension modes already registered by the current client.
        for guiType in set(ARENA_GUI_TYPE.RANGE).union(packagesByMode):
            packages = packagesByMode.setdefault(guiType, [])
            if self.PACKAGE not in packages:
                packages.append(self.PACKAGE)
                self.addedPackages.append(packages)

    def uninstall(self):
        from gui.Scaleform.required_libraries_config import BATTLE_REQUIRED_LIBRARIES
        error = None
        handlers = list(BATTLE_HANDLERS)
        handlers.extend(handler for handler in self.pendingHandlers if handler not in handlers)
        for handler in handlers:
            try:
                handler.close()
            except Exception as failure:
                # Strong ownership survives removal from the client's weak set.
                self.pendingHandlers.add(handler)
                LOG.exception('Could not close battle view handler: %s', handler)
                if error is None:
                    error = failure
            else:
                self.pendingHandlers.discard(handler)
                BATTLE_HANDLERS.discard(handler)
        for packages in self.addedPackages:
            if self.PACKAGE in packages:
                packages.remove(self.PACKAGE)
        self.addedPackages = []
        if self.addedLibrary and self.SWF in BATTLE_REQUIRED_LIBRARIES:
            BATTLE_REQUIRED_LIBRARIES.remove(self.SWF)
        self.addedLibrary = False
        BATTLE_COMPONENTS.clear()
        if error is not None:
            raise error
