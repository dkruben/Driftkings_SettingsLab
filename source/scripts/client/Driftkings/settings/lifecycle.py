# -*- coding: utf-8 -*-
"""Configuration lifecycle owned by the package and its Gameface panel."""
from constants import DEFAULT_LANGUAGE


class SettingsLifecycle(object):
    def __init__(self):
        self.lang = DEFAULT_LANGUAGE
        self.init()
        self.loadLang()
        self.tb = self.createTB()
        self.load()

    def migrateConfigs(self):
        pass

    def readCurrentSettings(self, quiet=True):
        pass

    def onPanelOpened(self):
        from Driftkings.settings.service import settings_service
        settings_service.reload(self)

    def onPanelClosed(self):
        pass

    def onButtonPress(self, name, value):
        pass

    def registerSettings(self):
        from Driftkings.common.utils.delayed.api import registerSettings
        registerSettings(self)

    def load(self):
        self.migrateConfigs()
        self.registerSettings()
        self.readData(False)
        self.readCurrentSettings(False)
