# -*- coding: utf-8 -*-
from Driftkings._constants import INFO_PANEL
from Driftkings.settings.template_schema import control, hotkey, options, slider
from Driftkings.settings.templates.base import ComponentSettings


class InfoPanelSettings(ComponentSettings):
    COMPONENT = INFO_PANEL.ID

    TRANSLATED_TITLE = False

    def getControlColumns(self):
        xFormat = self.i18n['UI_delay_format']
        showForOptions = ['all', 'ally', 'enemy']
        showForLabels = [self.i18n['UI_showFor_' + x] for x in showForOptions]
        templateOptions = ['default', 'minimal', 'detailed', 'full', 'kmp', 'ndo', 'driftkings']
        templateLabels = [self.i18n['UI_templatePreset_' + x] for x in templateOptions]
        return (
            [
                control(INFO_PANEL.TEXT_LOCK),
                slider(INFO_PANEL.DELAY, 1.0, 10, 1.0, '{{value}}%s' % xFormat),
                control(INFO_PANEL.ALIVE_ONLY),
                hotkey(INFO_PANEL.ALT_KEY),
                options(INFO_PANEL.SHOW_FOR, showForLabels)
            ],
            [
                control(INFO_PANEL.BACKGROUND_ENABLED),
                slider(INFO_PANEL.BACKGROUND_ALPHA, 0.0, 1.0, 0.1, '{{value}}'),
                options(INFO_PANEL.TEMPLATE_PRESET, templateLabels)
            ]
        )
