# -*- coding: utf-8 -*-
"""Publish our battle package; the client owns view registration and lifecycle."""
import weakref

BATTLE_COMPONENTS = {}
BATTLE_HANDLERS = weakref.WeakSet()


class BattleViews(object):
    def __init__(self, registration=None, visibility=None):
        self.registration = registration
        self.visibility = visibility
        self.definitions = {}
        self.active = False

    def register(self, alias, view, config):
        if alias in self.definitions:
            raise ValueError('Duplicate battle component: ' + alias)
        self.definitions[alias] = (view, config)

    def start(self):
        if self.active:
            return
        if self.registration is None:
            from Driftkings.core.hud_visibility import hudVisibility
            from Driftkings.views.battle.overlay import ALIAS, OverlayView, OverlayConfig
            self.visibility = hudVisibility
            self.registration = BattlePackageRegistration()
            self.register(ALIAS, OverlayView, OverlayConfig())
        if self.visibility is not None:
            self.visibility.start()
        self.registration.install(self.definitions)
        self.active = True

    def stop(self):
        if not self.active:
            return
        self.active = False
        self.registration.uninstall()
        if self.visibility is not None:
            self.visibility.stop()


class BattlePackageRegistration(object):
    PACKAGE = 'Driftkings.views.battle'
    SWF = 'DriftkingsBattle.swf'

    def __init__(self):
        self.addedPackages = []
        self.addedLibrary = False

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
        for handler in tuple(BATTLE_HANDLERS):
            handler.close()
        for packages in self.addedPackages:
            if self.PACKAGE in packages:
                packages.remove(self.PACKAGE)
        self.addedPackages = []
        if self.addedLibrary and self.SWF in BATTLE_REQUIRED_LIBRARIES:
            BATTLE_REQUIRED_LIBRARIES.remove(self.SWF)
        self.addedLibrary = False
        BATTLE_COMPONENTS.clear()
