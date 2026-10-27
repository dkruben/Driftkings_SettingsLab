# -*- coding: utf-8 -*-
import weakref

from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from driftkings._constants import BATTLE_ALIASES, GLOBAL, MINIMAP_ENHANCEMENTS
from driftkings.common.utils.game import checkKeys
from driftkings.core.keyboard import keyboard
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.minimap_enhancements import MinimapEnhancementsSettings as Settings
from driftkings.settings.service import settings_service
from driftkings.ui import g_events

LOG = get_logger('driftkings.battle.minimap_enhancements')

PERSONAL = weakref.WeakSet()
VEHICLES = weakref.WeakSet()
VIEWS = weakref.WeakSet()
AS_BATTLE = BATTLE_ALIASES.MINIMAP


class MinimapController(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self, config):
        self.config = config
        self._active = False
        self.minimapZoom = False
        settings_service.onModSettingsChanged.connect(self.onModSettingsChanged, MINIMAP_ENHANCEMENTS)

    def activate(self):
        if self._active:
            return
        self._active = True
        keyboard.subscribe(self.onHotkeyPressed)

    def deactivate(self):
        keyboard.unsubscribe(self.onHotkeyPressed)
        self._active = False
        # Flash disposal restores zoom; do not access an arena being destroyed.
        self.minimapZoom = False

    def dispose(self):
        self.deactivate()
        settings_service.onModSettingsChanged.disconnect(self.onModSettingsChanged)

    def onModSettingsChanged(self, component, settings):
        if not settings_service.getComponentDict(self.config)[GLOBAL.ENABLED] or not settings_service.getComponentDict(self.config)[MINIMAP_ENHANCEMENTS.PRESENTATION]['alternativeEnabled']:
            self.setAlternative(False)
        changed = set(settings)
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_ENHANCEMENTS.YAW, MINIMAP_ENHANCEMENTS.LINES,
                                 MINIMAP_ENHANCEMENTS.CIRCLES, MINIMAP_ENHANCEMENTS.VIEW_RADIUS,
                                 MINIMAP_ENHANCEMENTS.CHANGE_COLOR_CIRCLES, MINIMAP_ENHANCEMENTS.COLOR_DRAW_CIRCLE,
                                 MINIMAP_ENHANCEMENTS.COLOR_MAX_VIEW_CIRCLE, MINIMAP_ENHANCEMENTS.COLOR_MIN_SPOTTING_CIRCLE,
                                 MINIMAP_ENHANCEMENTS.COLOR_VIEW_CIRCLE)):
            for plugin in list(PERSONAL):
                plugin.refreshPresentation()
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_ENHANCEMENTS.LABELS, MINIMAP_ENHANCEMENTS.PRESENTATION,
                                 MINIMAP_ENHANCEMENTS.SHOW_NAMES, MINIMAP_ENHANCEMENTS.SHOW_LAST_POSITIONS,
                                 MINIMAP_ENHANCEMENTS.LAST_POSITION_DURATION, MINIMAP_ENHANCEMENTS.LOST_MARKER,
                                 MINIMAP_ENHANCEMENTS.PERMANENT_MINIMAP_DEATH)):
            for plugin in list(VEHICLES):
                plugin.refreshLabels()
        if changed.intersection((GLOBAL.ENABLED, MINIMAP_ENHANCEMENTS.PRESENTATION, MINIMAP_ENHANCEMENTS.ZOOM_FACTOR,
                                 MINIMAP_ENHANCEMENTS.ZOOM_FACTOR_MAX, MINIMAP_ENHANCEMENTS.ICONS, MINIMAP_ENHANCEMENTS.HEALTH,
                                 MINIMAP_ENHANCEMENTS.LOST_MARKER, MINIMAP_ENHANCEMENTS.MAP_SIZE, MINIMAP_ENHANCEMENTS.CIRCLES,
                                 MINIMAP_ENHANCEMENTS.EXTRA_CIRCLES, MINIMAP_ENHANCEMENTS.LABELS, MINIMAP_ENHANCEMENTS.LINES,
                                 MINIMAP_ENHANCEMENTS.ARTILLERY_AIM, MINIMAP_ENHANCEMENTS.SHOW_VEHICLE_TYPES,
                                 MINIMAP_ENHANCEMENTS.NEARBY)):
            for view in list(VIEWS):
                view.onAltKey(self.minimapZoom)

    def setAlternative(self, pressed):
        if self.minimapZoom == pressed:
            return
        self.minimapZoom = pressed
        g_events.onAltKey(pressed)
        for plugin in list(VEHICLES):
            plugin.refreshLabels()

    @property
    def notEpicBattle(self):
        return not self.sessionProvider.arenaVisitor.gui.isInEpicRange()

    def onHotkeyPressed(self, event):
        settings = settings_service.getComponentDict(self.config)
        if not settings[GLOBAL.ENABLED] or not self._active:
            return
        self.setAlternative(bool(settings[MINIMAP_ENHANCEMENTS.PRESENTATION]['alternativeEnabled'] and checkKeys(settings[MINIMAP_ENHANCEMENTS.BUTTON])))


config = Settings()
controller = MinimapController(config)


from driftkings.flash.batalha.minimap_enhancements import MinimapEnhancementsView


def getBattleViews():
    return ((AS_BATTLE, MinimapEnhancementsView, config),)


def fini():
    controller.dispose()

from driftkings.flash.batalha.minimap_plugins import configure
configure(config, controller, PERSONAL, VEHICLES, VIEWS)
