# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, HANGAR_MARKS_OF_EXCELLENCE, MARK_THRESHOLDS

"""Presentation adapter for MarksOnGunHangar; gameplay state stays in its component."""
from importlib import import_module
import weakref

from CurrentVehicle import g_currentVehicle
from gui.shared.personality import ServicesLocator

from driftkings.common.utils.colorratting import getStatisticColor
from driftkings.gameface.hangar.common import card_payload, HangarController, install_card, publish_card
from driftkings.interface_catalog import gameface_spec
from driftkings.settings.service import affects, settings_service
from driftkings.views.marks_model import moved_panel, number_locale

FEATURE = 'DriftkingsMarksOnGunHangar'
RESOURCE = gameface_spec(FEATURE)['resource']


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.lobby.hangar_marks_of_excellence')


def get_view_config(config):
    settings = settings_service.getComponentDict(config)
    panel = dict(settings[HANGAR_MARKS_OF_EXCELLENCE.PANEL])
    panel['compactMode'] = bool(settings[HANGAR_MARKS_OF_EXCELLENCE.COMPACT_MODE])
    panel['locked'] = bool(settings[HANGAR_MARKS_OF_EXCELLENCE.TEXT_LOCK])
    panel['visible'] = bool(settings[GLOBAL.ENABLED] and settings[HANGAR_MARKS_OF_EXCELLENCE.SHOW_IN_HANGAR])
    panel.update(settings.get(HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE, {}))
    card = settings[HANGAR_MARKS_OF_EXCELLENCE.CARD]
    for key in ('titleColor', 'backgroundColor', 'backgroundAlpha', 'accentColor'):
        panel[key] = card[key]
    scale = settings.get(HANGAR_MARKS_OF_EXCELLENCE.COLOR_RATING, 0)
    for level in MARK_THRESHOLDS:
        panel['starColor%s' % level] = getStatisticColor('mog', level, scale)
    panel.update(number_locale(config.lang))
    return panel


class MarksOnGunHangarController(HangarController):
    def start(self):
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, HANGAR_MARKS_OF_EXCELLENCE)

    def stop(self):
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        for child in list(self.views.values()):
            child.setEnabled(False)
            child.destroy()
        self.views.clear()
        self.visible.clear()

    def setVisible(self, parent, visible):
        super(MarksOnGunHangarController, self).setVisible(parent, visible)
        if not visible:
            from driftkings.core.marks_state import marks_state
            marks_state.clear('hangar')

    def onSettingsChanged(self, component, changes):
        self.onApplySettings(changes)

    def onApplySettings(self, changes=None):
        if changes is None or affects(changes, GLOBAL.ENABLED, HANGAR_MARKS_OF_EXCELLENCE.SHOW_IN_HANGAR,
                HANGAR_MARKS_OF_EXCELLENCE.TEXT_LOCK, HANGAR_MARKS_OF_EXCELLENCE.GOAL_SELECTION,
                HANGAR_MARKS_OF_EXCELLENCE.COMPACT_MODE, HANGAR_MARKS_OF_EXCELLENCE.HISTORY_BATTLES,
                HANGAR_MARKS_OF_EXCELLENCE.COLOR_RATING,
                HANGAR_MARKS_OF_EXCELLENCE.PANEL, HANGAR_MARKS_OF_EXCELLENCE.CARD, HANGAR_MARKS_OF_EXCELLENCE.GAMEFACE):
            super(MarksOnGunHangarController, self).onApplySettings(changes)


def install_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent

    from driftkings.gameface.core import attach_assets

    class MarksModel(ViewModel):
        def __init__(self):
            super(MarksModel, self).__init__(properties=3, commands=1)

        def _initialize(self):
            super(MarksModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self.onSavePosition = self._addCommand('onSavePosition')
            attach_assets(self, FEATURE)

    class MarksView(ViewComponent):
        def __init__(self, parent, resource_id):
            self._hangarRef = weakref.ref(parent)
            self._marksActive = False
            self._lastPayload = None
            super(MarksView, self).__init__(layoutID=resource_id, model=MarksModel)
            _component().g_controller.views[parent] = self

        def _getEvents(self):
            return ((g_currentVehicle.onChanged, self.refresh),
                    (ServicesLocator.itemsCache.onSyncCompleted, self.refresh),
                    (self.getViewModel().onSavePosition, self.savePosition))

        def _onLoading(self, *args, **kwargs):
            super(MarksView, self)._onLoading(*args, **kwargs)
            self._marksActive = True
            self.refresh()

        def _finalize(self):
            self._marksActive = False
            parent = self._hangarRef()
            if parent is not None and _component().g_controller.views.get(parent) is self:
                _component().g_controller.views.pop(parent, None)
            super(MarksView, self)._finalize()

        def refreshSettings(self, changes):
            rebuild = affects(changes, GLOBAL.ENABLED, HANGAR_MARKS_OF_EXCELLENCE.SHOW_IN_HANGAR,
                              HANGAR_MARKS_OF_EXCELLENCE.GOAL_SELECTION, HANGAR_MARKS_OF_EXCELLENCE.HISTORY_BATTLES,
                              HANGAR_MARKS_OF_EXCELLENCE.COLOR_RATING)
            self.refresh(config_only=not rebuild)

        def refresh(self, *args, **kwargs):
            if not self._marksActive:
                return
            try:
                parent = self._hangarRef()
                visible = bool(parent is not None and _component().g_controller.visible.get(parent, False)
                               and settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED] and settings_service.getComponentDict(_component().config)[HANGAR_MARKS_OF_EXCELLENCE.SHOW_IN_HANGAR]
                               and _component().has_marks_tier())
                payload = card_payload(self._lastPayload, kwargs.get('config_only', False), visible,
                                       lambda: get_view_config(_component().config), _component().g_data.build_panel_model)
                publish_card(self, payload)
            except Exception:
                from driftkings.core.marks_state import marks_state
                marks_state.clear('hangar')
                self._lastPayload = None
                _component().LOG.exception('Could not update Gameface hangar card')
                with self.getViewModel().transaction() as model:
                    model._setString(0, '{"config":{"visible":false}}')

        def savePosition(self, args):
            settings = settings_service.getComponentDict(_component().config)
            if settings[HANGAR_MARKS_OF_EXCELLENCE.TEXT_LOCK]:
                return
            panel = moved_panel(settings[HANGAR_MARKS_OF_EXCELLENCE.PANEL], args)
            if panel is None:
                return
            settings_service.apply(_component().config, {HANGAR_MARKS_OF_EXCELLENCE.PANEL: panel})

    install_card(_component, MarksView, __name__, RESOURCE)
