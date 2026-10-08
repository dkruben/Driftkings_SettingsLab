# -*- coding: utf-8 -*-
from Driftkings.common import DriftkingsConfigInterface
from Driftkings.common.config.utils import processHotKeys
from Driftkings.settings.settings_data import defaults, default_keys
from Driftkings.settings.template_schema import build_template


class ComponentSettings(DriftkingsConfigInterface):
    COMPONENT = None
    TRANSLATED_TITLE = True
    COLUMNS = ((), ())

    def createTemplate(self):
        return build_template(self)

    def getControlColumns(self):
        return self.COLUMNS

    def init(self):
        self.ID = self.COMPONENT
        self.data = defaults(self.ID)
        self.defaultKeys = default_keys(self.ID)
        processHotKeys(self.defaultKeys, list(self.defaultKeys), 'read')
        processHotKeys(self.data, self.defaultKeys, 'read')
        super(ComponentSettings, self).init()

    def getSettingsDefaults(self):
        data = defaults(self.ID)
        processHotKeys(data, self.defaultKeys, 'read')
        return data
