# -*- coding: utf-8 -*-
"""Core-owned settings interface; section metadata and file formats stay stable."""
from driftkings.settings.loader import settings_loader
from driftkings.settings.settings_data import user_settings


class SettingsService(object):
    def __init__(self):
        from driftkings.settings.registry import registry
        self.registry = registry
        self.active = False
        self.controller = None

    def start(self):
        if self.active:
            return
        from helpers import getClientLanguage, getClientVersion

        from driftkings.settings.profiles import ProfileSettings
        self.registry.register(ProfileSettings(settings_loader, getClientLanguage()))
        from driftkings.gameface.lobby.settings_window import controller
        from driftkings.settings.panel import settings
        from driftkings.settings.panel.sections import SectionPanelBinding
        settings.client_version = getClientVersion()
        settings.start(str(getClientLanguage()))
        controller.adapter = SectionPanelBinding(settings, self.registry)
        self.controller = controller
        controller.start(settings)
        try:
            from gui.modsListApi import g_modsListApi
        except ImportError:
            class MissingModsList(object):
                def __getattr__(self, name):
                    return lambda *args, **kwargs: None
            g_modsListApi = MissingModsList()
        g_modsListApi.addModification(id='driftkings', name=u'driftkings', description=settings.strings['title'], icon='gui/maps/icons/driftkings/small.png', enabled=True, login=True, lobby=True, callback=controller.open)
        self.active = True

    def onContextEntered(self, space):
        if self.controller is not None:
            self.controller.onContextEntered(space)

    def onContextLeft(self, space):
        if self.controller is not None:
            self.controller.onContextLeft(space)

    def stop(self):
        self.active = False
        from driftkings.core.diagnostics import diagnostics
        diagnostics.configure(False)
        if self.controller is not None:
            self.controller.stop()
