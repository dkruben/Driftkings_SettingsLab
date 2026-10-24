# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, MAIN
from driftkings.settings.controls_schema import field as nested_field
from driftkings.settings.definitions.base import SectionDefinition

FIELD_DEFAULTS = {'x': 0, 'y': 0, 'width': 0, 'height': 0, 'screenHAlign': 'left', 'format': '',
                  'textFormat': {'align': 'left', 'valign': 'top', 'color': '#959688'},
                  'shadow': {'enabled': False, 'distance': 0, 'angle': 0, 'color': '#000000',
                             'alpha': 100, 'blur': 4, 'strength': 1}}


class MainSettings(SectionDefinition):
    NAME = MAIN.NAME

    TRANSLATED_TITLE = True

    def normalize_loaded(self, values):
        import copy
        for item in values[MAIN.CLOCK][MAIN.FORMATS]:
            if not isinstance(item, dict):
                continue
            for key, default in FIELD_DEFAULTS.items():
                if key not in item or isinstance(default, dict) and not isinstance(item[key], dict):
                    item[key] = copy.deepcopy(default)
                elif isinstance(default, dict) and isinstance(item[key], dict):
                    for child, value in default.items():
                        item[key].setdefault(child, value)
        return values

    def normalize_changes(self, values, changes):
        return self.normalize_loaded(values)

    def getControlColumns(self):
        columns = [[nested_field([MAIN.CLOCK, GLOBAL.ENABLED],
                    self.i18n['UI_setting_clock_enabled_text'])], []]
        def add(index, path, kind='Slider', low=None, high=None, choices=None):
            key = '_'.join(path)
            item = nested_field([MAIN.CLOCK, MAIN.FORMATS, index] + path,
                                self.i18n['UI_clock_' + key], kind, low, high, choices,
                                tab=self.i18n['UI_clock_field'] + ' ' + str(index + 1))
            if choices is not None:
                item['options'] = [{'label': self.i18n['UI_clock_' + choice]} for choice in choices]
            item['tooltip'] = self.i18n['UI_clock_' + key + '_tooltip']
            columns[1 if path[0] == 'shadow' else 0].append(item)
        for index, value in enumerate(self.data[MAIN.CLOCK][MAIN.FORMATS]):
            if not isinstance(value, dict):
                continue
            # Also supports sparse, hand-written definitions before normalization.
            for key, low, high in (('x', -4096, 4096), ('y', -2160, 2160),
                                   ('width', 0, 4096), ('height', 0, 2160)):
                if key in value:
                    add(index, [key], low=low, high=high)
            if 'screenHAlign' in value:
                add(index, ['screenHAlign'], 'Dropdown', choices=['left', 'center', 'right'])
            if 'format' in value:
                add(index, ['format'], 'TextArea')
            for key, choices in (('align', ['left', 'center', 'right']),
                                 ('valign', ['top', 'center', 'bottom'])):
                if key in value.get('textFormat', {}):
                    add(index, ['textFormat', key], 'Dropdown', choices=choices)
            if 'color' in value.get('textFormat', {}):
                add(index, ['textFormat', 'color'], 'ColorChoice')
            for key, kind, high in (('enabled', 'CheckBox', None), ('color', 'ColorChoice', None),
                                    ('distance', 'Slider', 255), ('angle', 'Slider', 360),
                                    ('alpha', 'Slider', 100), ('blur', 'Slider', 255),
                                    ('strength', 'Slider', 8)):
                if key in value.get('shadow', {}):
                    add(index, ['shadow', key], kind, 0 if high is not None else None, high)
        return columns
