# -*- coding: utf-8 -*-
"""Core-owned settings interface; feature templates and file formats stay stable."""
from Driftkings.settings.loader import settings_loader
from Driftkings.settings.settings_data import user_settings


class SettingsService(object):
    def __init__(self):
        from Driftkings.settings.registry import registry
        self.registry = registry
        self.active = False
        self.controller = None

    def start(self):
        if self.active:
            return
        from Driftkings.settings.profiles import ProfileSettings
        from helpers import getClientLanguage, getClientVersion
        self.registry.register(ProfileSettings(settings_loader, getClientLanguage()))
        from Driftkings.settings.panel import settings
        from Driftkings.settings.panel.compatibility import TemplateAdapter
        from Driftkings.views.hangar.settings_window import controller
        settings.client_version = getClientVersion()
        settings.start(str(getClientLanguage()))
        controller.adapter = TemplateAdapter(settings, self.registry)
        controller.start(settings)
        self.controller = controller
        try:
            from gui.modsListApi import g_modsListApi
        except ImportError:
            class MissingModsList(object):
                def __getattr__(self, name):
                    return lambda *args, **kwargs: None
            g_modsListApi = MissingModsList()
        g_modsListApi.addModification(id='Driftkings', name=u'Driftkings', description=settings.strings['title'], icon='gui/maps/icons/Driftkings/small.png', enabled=True, login=True, lobby=True, callback=controller.open)
        self.active = True

    def onContextEntered(self, space):
        if self.controller is not None:
            self.controller.onContextEntered(space)

    def onContextLeft(self, space):
        if self.controller is not None:
            self.controller.onContextLeft(space)

    def stop(self):
        if not self.active:
            return
        self.active = False
        if self.controller is not None:
            self.controller.stop()
