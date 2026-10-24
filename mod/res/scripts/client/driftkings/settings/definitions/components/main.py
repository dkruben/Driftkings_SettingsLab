# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, MAIN
from driftkings.settings.controls_schema import field as nested_field
from driftkings.settings.definitions.base import SectionDefinition


class MainSettings(SectionDefinition):
    NAME = MAIN.NAME

    TRANSLATED_TITLE = True

    def getControlColumns(self):
        # The clock fields (MAIN.FORMATS) are edited in main.json; the panel only switches the clock.
        def nested(section, key, kind='CheckBox'):
            title = self.i18n.get('UI_setting_' + section + '_' + key + '_text', key)
            return nested_field([section, key], title, kind)
        return (
            [nested(MAIN.CLOCK, GLOBAL.ENABLED)],
            []
        )
