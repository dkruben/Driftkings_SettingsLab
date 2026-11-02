# -*- coding: utf-8 -*-
import hashlib

from driftkings._constants import TARGET_INFORMATION
from driftkings.settings.controls_schema import control, hotkey, options, slider
from driftkings.settings.definitions.base import SectionDefinition

# SHA-256 of the custom card formerly shipped as the default, with labels fixed in
# Portuguese. Saved copies of it fall back to the translated presets; edited ones stay.
RETIRED_DEFAULT_FORMATS = '90e86e50bd85c6518d5b22ea9a2421d722981175159ec3d7f508c715718dfb8a'


def _formats_digest(formats):
    text = u'\n'.join(value if isinstance(value, type(u'')) else value.decode('utf-8') for value in formats)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class TargetInformationSettings(SectionDefinition):
    NAME = TARGET_INFORMATION.NAME

    TRANSLATED_TITLE = True

    def normalize_loaded(self, values):
        formats = values.get(TARGET_INFORMATION.FORMATS)
        if isinstance(formats, list) and len(formats) == 1 and _formats_digest(formats) == RETIRED_DEFAULT_FORMATS:
            values[TARGET_INFORMATION.FORMATS] = []
        return values

    def getControlColumns(self):
        xFormat = self.i18n['UI_delay_format']
        showForOptions = ['all', 'ally', 'enemy']
        showForLabels = [self.i18n['UI_showFor_' + x] for x in showForOptions]
        templateOptions = ['default', 'minimal', 'detailed', 'full', 'kmp', 'ndo', 'driftkings']
        templateLabels = [self.i18n['UI_templatePreset_' + x] for x in templateOptions]
        return (
            [
                control(TARGET_INFORMATION.TEXT_LOCK),
                slider(TARGET_INFORMATION.DELAY, 1.0, 10, 1.0, '{{value}}%s' % xFormat),
                control(TARGET_INFORMATION.ALIVE_ONLY),
                hotkey(TARGET_INFORMATION.ALT_KEY),
                options(TARGET_INFORMATION.SHOW_FOR, showForLabels)
            ],
            [
                control(TARGET_INFORMATION.BACKGROUND_ENABLED),
                slider(TARGET_INFORMATION.BACKGROUND_ALPHA, 0.0, 1.0, 0.1, '{{value}}'),
                options(TARGET_INFORMATION.TEMPLATE_PRESET, templateLabels)
            ]
        )
