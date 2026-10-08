# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, MARKS_ON_GUN_HANGAR
"""Presentation adapter for MarksOnGunHangar; gameplay state stays in its component."""
from Driftkings.settings.service import settings_service, affects
from Driftkings.common import getStatisticColor
import weakref
from CurrentVehicle import g_currentVehicle
from gui.shared.personality import ServicesLocator
from Driftkings.views.hangar.common import HangarController, install_card, card_payload, publish_card

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.lobby.gun_marks')


def get_view_config(config):
    settings = settings_service.getComponentDict(config)
    panel = dict(settings[MARKS_ON_GUN_HANGAR.PANEL])
    panel['compactMode'] = bool(settings[MARKS_ON_GUN_HANGAR.COMPACT_MODE])
    panel['height'] = 194.0 if panel['compactMode'] else max(260.0, panel['height'])
    panel['locked'] = bool(settings[MARKS_ON_GUN_HANGAR.TEXT_LOCK])
    panel['visible'] = bool(settings[GLOBAL.ENABLED] and settings[MARKS_ON_GUN_HANGAR.SHOW_IN_HANGAR])
    panel['starAnimationWindow'] = float(settings.get(MARKS_ON_GUN_HANGAR.STAR_ANIMATION_WINDOW, 5.0))
    card = settings[MARKS_ON_GUN_HANGAR.CARD]
    for key in ('headerColor', 'titleColor', 'backgroundColor', 'backgroundAlpha',
                'outlineColor', 'lineColor', 'accentColor', 'accentSoftColor', 'mutedColor', 'warningColor'):
        panel[key] = card[key]
    scale = settings.get(MARKS_ON_GUN_HANGAR.COLOR_RATING, 0)
    for level in (65, 85, 95):
        panel['starColor%s' % level] = getStatisticColor('mog', level, scale)
    return panel


class MarksOnGunHangarController(HangarController):
    def start(self):
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, MARKS_ON_GUN_HANGAR)

    def stop(self):
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)

    def onSettingsChanged(self, component, changes):
        self.onApplySettings(changes)

    def onApplySettings(self, changes=None):
        if changes is None or affects(changes, GLOBAL.ENABLED, MARKS_ON_GUN_HANGAR.SHOW_IN_HANGAR,
                MARKS_ON_GUN_HANGAR.TEXT_LOCK, MARKS_ON_GUN_HANGAR.GOAL_SELECTION,
                MARKS_ON_GUN_HANGAR.COMPACT_MODE, MARKS_ON_GUN_HANGAR.HISTORY_BATTLES,
                MARKS_ON_GUN_HANGAR.COLOR_RATING, MARKS_ON_GUN_HANGAR.STAR_ANIMATION_WINDOW,
                MARKS_ON_GUN_HANGAR.PANEL, MARKS_ON_GUN_HANGAR.CARD):
            super(MarksOnGunHangarController, self).onApplySettings(changes)


def install_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent
    from Driftkings.ui.gameface import attach_assets

    class MarksModel(ViewModel):
        def __init__(self):
            super(MarksModel, self).__init__(properties=3, commands=1)

        def _initialize(self):
            super(MarksModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self.onSavePosition = self._addCommand('onSavePosition')
            attach_assets(self, _component().FEATURE, styles=[_component().ASSETS + 'marks.css'], scripts=[_component().ASSETS + 'marks.js'])

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
            rebuild = affects(changes, GLOBAL.ENABLED, MARKS_ON_GUN_HANGAR.SHOW_IN_HANGAR,
                              MARKS_ON_GUN_HANGAR.GOAL_SELECTION, MARKS_ON_GUN_HANGAR.HISTORY_BATTLES,
                              MARKS_ON_GUN_HANGAR.COLOR_RATING)
            self.refresh(config_only=not rebuild)

        def refresh(self, *args, **kwargs):
            if not self._marksActive:
                return
            try:
                parent = self._hangarRef()
                visible = bool(parent is not None and _component().g_controller.visible.get(parent, False)
                               and settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED] and settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_HANGAR.SHOW_IN_HANGAR])
                payload = card_payload(self._lastPayload, kwargs.get('config_only', False), visible,
                                       lambda: get_view_config(_component().config), _component().g_data.build_panel_model)
                publish_card(self, payload)
            except Exception:
                self._lastPayload = None
                _component().LOG.exception('Could not update Gameface hangar card')
                with self.getViewModel().transaction() as model:
                    model._setString(0, '{"config":{"visible":false}}')

        def savePosition(self, args):
            if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_HANGAR.TEXT_LOCK] or not isinstance(args, dict):
                return
            panel = dict(settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_HANGAR.PANEL])
            panel['x'] = max(-7680, min(7680, _component().finite(args.get('x'), panel['x'])))
            panel['y'] = max(-4320, min(4320, _component().finite(args.get('y'), panel['y'])))
            settings_service.apply(_component().config, {MARKS_ON_GUN_HANGAR.PANEL: panel})

    install_card(_component, MarksView, __name__)
