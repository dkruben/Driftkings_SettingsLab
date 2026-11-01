# -*- coding: utf-8 -*-
from driftkings._constants import ACCOUNT_MANAGER
from driftkings.settings.controls_schema import caption
from driftkings.settings.definitions.base import SectionDefinition


class AccountManagerSettings(SectionDefinition):
    NAME = ACCOUNT_MANAGER.NAME

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        # A label without a setting carries the button; the header switch turns the login button on or off.
        manage = caption(self.i18n['UI_setting_openManagerInfo'])
        manage['button'] = self.i18n['UI_setting_openManager']
        return [manage], []

    def onButtonPress(self, name, value):
        from driftkings.components.account_manager import controller
        controller.openManager()
