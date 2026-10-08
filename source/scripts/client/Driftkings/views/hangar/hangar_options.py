# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, HANGAR_OPTIONS
from Driftkings.settings.service import settings_service, affects
"""Presentation adapter for HangarOptions; gameplay state stays in its component."""
import weakref
from Driftkings.common import logError
from Driftkings.core.hooks import override
from Driftkings.views.hangar.common import HangarController, publish_card

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.lobby.hangar_options')


class ClockController(HangarController):
    SETTINGS_KEYS = (HANGAR_OPTIONS.CLOCK_STYLE, HANGAR_OPTIONS.CLOCK_X, HANGAR_OPTIONS.CLOCK_Y,
                     HANGAR_OPTIONS.CLOCK_SCALE, HANGAR_OPTIONS.CLOCK_SECONDS, HANGAR_OPTIONS.CLOCK24_HOUR)

    def __init__(self):
        super(ClockController, self).__init__()
        self.active = False

    def start(self):
        if not self.active:
            self.active = True
            settings_service.onModSettingsChanged.connect(self.onSettingsChanged, HANGAR_OPTIONS)
            self.onApplySettings()

    def stop(self):
        if self.active:
            self.active = False
            settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
            self.onApplySettings()

    def onSettingsChanged(self, component, changes):
        if affects(changes, *((GLOBAL.ENABLED, HANGAR_OPTIONS.CLOCK) + self.SETTINGS_KEYS)):
            self.onApplySettings()

    def onApplySettings(self, changes=None):
        for child in list(self.views.values()):
            try:
                child.refresh()
            except Exception:
                logError(_component().config.ID, 'Could not refresh Gameface clock view')


def install_clock_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.gen_utils import INVALID_RES_ID
    from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
    from Driftkings.ui.gameface import attach_assets, resource_id as resolve_resource

    class ClockModel(ViewModel):
        def __init__(self):
            super(ClockModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(ClockModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, _component().FEATURE, styles=[_component().ASSETS + 'clock.css'], scripts=[_component().ASSETS + 'clock.js'])

    class ClockView(ViewComponent):
        def __init__(self, parent, resource_id):
            self._hangarRef = weakref.ref(parent)
            self._clockActive = False
            self._lastPayload = None
            super(ClockView, self).__init__(layoutID=resource_id, model=ClockModel)
            _component().g_clockController.views[parent] = self

        def _onLoading(self, *args, **kwargs):
            super(ClockView, self)._onLoading(*args, **kwargs)
            self._clockActive = True
            self.refresh()

        def _finalize(self):
            self._clockActive = False
            parent = self._hangarRef()
            if parent is not None and _component().g_clockController.views.get(parent) is self:
                _component().g_clockController.views.pop(parent, None)
                _component().g_clockController.visible.pop(parent, None)
            super(ClockView, self)._finalize()

        def refresh(self, *args):
            if not self._clockActive:
                return
            try:
                parent = self._hangarRef()
                controller = _component().g_clockController
                data = settings_service.getComponentDict(_component().config)
                visible = bool(controller.active and parent is not None and controller.visible.get(parent, False)
                               and data[GLOBAL.ENABLED] and data[HANGAR_OPTIONS.CLOCK])
                payload = {'config': {key: data[key] for key in controller.SETTINGS_KEYS}}
                payload['config']['visible'] = visible
                publish_card(self, payload)
            except Exception:
                logError(_component().config.ID, 'Could not update Gameface clock')
                publish_card(self, {'config': {'visible': False}})

    @override(RandomHangar, '_getChildComponents')
    def get_children(original, parent, *args, **kwargs):
        children = dict(original(parent, *args, **kwargs))
        try:
            resource_id = resolve_resource(_component().RESOURCE)
            if resource_id == INVALID_RES_ID:
                logError(_component().config.ID, 'Missing Gameface clock resource: ' + _component().RESOURCE)
            else:
                children[resource_id] = lambda: ClockView(parent, resource_id)
        except Exception:
            logError(_component().config.ID, 'Could not attach Gameface clock')
        return children

    @override(RandomHangar, '_onShown')
    def on_shown(original, parent, *args, **kwargs):
        result = original(parent, *args, **kwargs)
        _component().g_clockController.setVisible(parent, True)
        return result

    @override(RandomHangar, '_onHidden')
    def on_hidden(original, parent, *args, **kwargs):
        _component().g_clockController.setVisible(parent, False)
        return original(parent, *args, **kwargs)
