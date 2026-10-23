# -*- coding: utf-8 -*-
from driftkings.logger import get_logger
LOG = get_logger('driftkings.views.hangar.hangar_preferences')
from driftkings.interface_catalog import gameface_spec
from driftkings._constants import GLOBAL, HANGAR_PREFERENCES
from driftkings.settings.service import settings_service, affects
"""Presentation adapter for HangarOptions; gameplay state stays in its component."""
import weakref
from helpers import getClientLanguage
from driftkings.core.hooks import override
from driftkings.views.hangar.common import HangarController, publish_card

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
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
    SETTINGS_SECTION = HANGAR_PREFERENCES
    SETTINGS_KEYS = (HANGAR_PREFERENCES.CLOCK_X, HANGAR_PREFERENCES.CLOCK_Y, HANGAR_PREFERENCES.CLOCK_SCALE, HANGAR_PREFERENCES.CLOCK_BACKGROUND)

    def __init__(self):
        super(ClockController, self).__init__()
        self.clockText = None

    def start(self):
        if not self.active:
            self.clockText = settings_service.getComponentDict(_component().config)[HANGAR_PREFERENCES.CUSTOM_CLOCK_TEXT]
            super(ClockController, self).start()
            self.onApplySettings()

    def stop(self):
        if self.active:
            super(ClockController, self).stop()
            self.onApplySettings()

    def onSettingsChanged(self, component, changes):
        if affects(changes, *((GLOBAL.ENABLED, HANGAR_PREFERENCES.CLOCK) + self.SETTINGS_KEYS)):
            self.onApplySettings()

    def onApplySettings(self, changes=None):
        for child in list(self.views.values()):
            try:
                child.refresh()
            except Exception:
                LOG.exception('Could not refresh Gameface clock view')


def install_clock_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
    from driftkings.ui.gameface import INVALID_RES_ID, attach_assets, resource_id as resolve_resource

    class ClockModel(ViewModel):
        def __init__(self):
            super(ClockModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(ClockModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, _component().FEATURE)

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
                               and data[GLOBAL.ENABLED] and data[HANGAR_PREFERENCES.CLOCK])
                payload = {'config': {key: data[key] for key in controller.SETTINGS_KEYS}}
                payload['config'][HANGAR_PREFERENCES.CUSTOM_CLOCK_TEXT] = controller.clockText
                payload['config']['visible'] = visible
                payload['config']['locale'] = getClientLanguage().replace('_', '-')
                payload['config']['calendar'] = calendar_names()
                payload['config']['hidePrestige'] = bool(data[GLOBAL.ENABLED] and not data[HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET])
                publish_card(self, payload)
            except Exception:
                LOG.exception('Could not update Gameface clock')
                publish_card(self, {'config': {'visible': False}})

    @override(RandomHangar, '_getChildComponents')
    def get_children(original, parent, *args, **kwargs):
        children = dict(original(parent, *args, **kwargs))
        try:
            resource_id = resolve_resource(_component().RESOURCE)
            if resource_id == INVALID_RES_ID:
                LOG.error('Missing Gameface clock resource: ' + _component().RESOURCE)
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


def install_header_options():
    import json
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.lobby.page.lobby_header import LobbyHeader
    from gui.shared.personality import ServicesLocator
    from driftkings.ui.gameface import attach_assets, resource_id

    class HeaderOptionsModel(ViewModel):
        def __init__(self):
            super(HeaderOptionsModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(HeaderOptionsModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, 'DriftkingsHangarHeaderOptions')

    class HeaderOptionsView(ViewComponent):
        def __init__(self):
            super(HeaderOptionsView, self).__init__(layoutID=resource_id(gameface_spec('DriftkingsHangarHeaderOptions')['resource']), model=HeaderOptionsModel)

        def _onLoading(self, *args, **kwargs):
            super(HeaderOptionsView, self)._onLoading(*args, **kwargs)
            data = settings_service.getComponentDict(_component().config)
            payload = dict((key, data.get(key, True)) for key in ('showBuyPremiumButton', 'showWotPlusButton'))
            payload['premiumTime'] = bool(data.get('premiumTime', False))
            payload['enabled'] = data[GLOBAL.ENABLED]
            payload['expiry'] = ServicesLocator.itemsCache.items.stats.activePremiumExpiryTime
            self._headerPayload = payload
            settings_service.onModSettingsChanged.connect(self._onSettingsChanged, HANGAR_PREFERENCES)
            self.getViewModel()._setString(0, json.dumps(payload))

        def _onSettingsChanged(self, component, changes):
            if affects(changes, GLOBAL.ENABLED):
                self._headerPayload['enabled'] = settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED]
                self.getViewModel()._setString(0, json.dumps(self._headerPayload))

        def _finalize(self):
            settings_service.onModSettingsChanged.disconnect(self._onSettingsChanged)
            super(HeaderOptionsView, self)._finalize()

    @override(LobbyHeader, '_getChildComponents')
    def header_children(base, self):
        children = dict(base(self))
        children[resource_id(gameface_spec('DriftkingsHangarHeaderOptions')['resource'])] = HeaderOptionsView
        return children
