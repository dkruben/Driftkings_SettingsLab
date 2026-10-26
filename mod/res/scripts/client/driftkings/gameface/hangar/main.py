# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, HANGAR_PREFERENCES, MAIN
from driftkings.logger import get_logger
from driftkings.settings.service import affects, settings_service

LOG = get_logger('driftkings.gameface.hangar.main')
"""Hangar clock presentation for the main section; its state stays in the component."""
from importlib import import_module
import weakref

from helpers import getClientLanguage

from driftkings.core.hooks import override
from driftkings.gameface.hangar.common import HangarController, publish_card
from driftkings.interface_catalog import gameface_spec

FEATURE = 'DriftkingsHangarClock'
RESOURCE = gameface_spec(FEATURE)['resource']


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.components.main')


def _hangar():
    # The prestige widget switch still belongs to Hangar preferences.
    return import_module('driftkings.lobby.hangar_preferences')


def calendar_names():
    # Gameface's embedded engine may ignore locale/options in toLocaleDateString.
    # Resolve names through the same WoT utility used by its own interface.
    import BigWorld
    from helpers import dependency
    from skeletons.gui.app_loader import IAppLoader
    app = dependency.instance(IAppLoader).getApp()
    if app is None:
        return {}
    utils = app.utilsManager
    first = BigWorld.wg_firstDayOfWeek()
    def text(value):
        return value.decode('utf-8') if isinstance(value, bytes) else value
    def days(full):
        values = utils.getWeekDayNames(full, False, False)
        return [text(values[(i - first + 7) % 7]) for i in range(7)]
    return {'days': days(True), 'shortDays': days(False),
            'months': [text(x) for x in utils.getMonthsNames(True, False, False)],
            'shortMonths': [text(x) for x in utils.getMonthsNames(False, False, False)]}


class ClockController(HangarController):
    # The payload also owns the prestige policy from Hangar preferences.
    SETTINGS_SECTION = None

    def start(self):
        if not self.active:
            super(ClockController, self).start()
            self.onApplySettings()

    def stop(self):
        if self.active:
            super(ClockController, self).stop()
            self.onApplySettings()

    def onSettingsChanged(self, component, changes):
        if ((component == MAIN.NAME and affects(changes, GLOBAL.ENABLED, MAIN.CLOCK)) or
                (component == HANGAR_PREFERENCES.NAME and affects(
                    changes, GLOBAL.ENABLED, HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET))):
            self.onApplySettings()

    def onApplySettings(self, changes=None):
        for child in list(self.views.values()):
            try:
                child.refresh()
            except Exception:
                LOG.exception('Could not refresh Gameface clock view')


def install_clock_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
    from gui.impl.pub.view_component import ViewComponent

    from driftkings.gameface.core import attach_assets, INVALID_RES_ID
    from driftkings.gameface.core import resource_id as resolve_resource

    class ClockModel(ViewModel):
        def __init__(self):
            super(ClockModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(ClockModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, FEATURE)

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
                clock = data[MAIN.CLOCK]
                # main.enabled switches every general option; clock.enabled only the clock.
                visible = bool(controller.active and parent is not None and controller.visible.get(parent, False)
                               and data[GLOBAL.ENABLED] and clock[GLOBAL.ENABLED])
                payload = {'config': {MAIN.FORMATS: clock[MAIN.FORMATS]}}
                payload['config']['visible'] = visible
                payload['config']['locale'] = getClientLanguage().replace('_', '-')
                payload['config']['calendar'] = calendar_names()
                hangar = settings_service.getComponentDict(_hangar().config)
                payload['config']['hidePrestige'] = bool(hangar[GLOBAL.ENABLED] and not hangar[HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET])
                publish_card(self, payload)
            except Exception:
                LOG.exception('Could not update Gameface clock')
                publish_card(self, {'config': {'visible': False}})

    @override(RandomHangar, '_getChildComponents')
    def get_children(original, parent, *args, **kwargs):
        children = dict(original(parent, *args, **kwargs))
        try:
            resource_id = resolve_resource(RESOURCE)
            if resource_id == INVALID_RES_ID:
                LOG.error('Missing Gameface clock resource: ' + RESOURCE)
            else:
                children[resource_id] = lambda: ClockView(parent, resource_id)
        except Exception:
            LOG.exception('Could not attach Gameface clock')
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
