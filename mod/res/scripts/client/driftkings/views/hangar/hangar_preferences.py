# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, HANGAR_PREFERENCES
from driftkings.interface_catalog import gameface_spec
from driftkings.logger import get_logger
from driftkings.settings.service import affects, settings_service

LOG = get_logger('driftkings.views.hangar.hangar_preferences')
"""Presentation adapter for HangarOptions; gameplay state stays in its component."""
from importlib import import_module

from driftkings.core.hooks import override


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.lobby.hangar_preferences')


def install_header_options():
    import json

    from frameworks.wulf import ViewModel
    from gui.impl.lobby.page.lobby_header import LobbyHeader
    from gui.impl.pub.view_component import ViewComponent
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
