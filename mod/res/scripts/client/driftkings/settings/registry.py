# -*- coding: utf-8 -*-
"""Section metadata and validation shared by the owned settings panel."""
import copy
import json
import math
import re

from driftkings.core.keycodes import valid_key_code
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Settings.Validation')

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


def path_value(data, path):
    for part in path:
        data = data[part]
    return data


def set_path(data, path, value):
    parent = path_value(data, path[:-1])
    parent[path[-1]] = value


class SettingsRegistry(object):
    def __init__(self):
        self.entries = {}
        self.isOpen = False

    def register(self, config):
        defaults = config.getSettingsDefaults() if hasattr(config, 'getSettingsDefaults') else config.data
        self.entries[config.NAME] = (config, copy.deepcopy(defaults))

    def describe(self, modID):
        config, defaults = self.entries[modID]
        values = config.data
        from driftkings.settings.controls_schema import nested_description, resolve
        controls = []
        if getattr(config, 'AUTOMATIC_CONTROLS', False):
            for key in sorted(values):
                value = values[key]
                kind = 'CheckBox' if type(value) is bool else 'Slider' if type(value) in (int, float) else 'TextInput' if isinstance(value, string_types) else None
                if kind:
                    controls.append({'type': kind, 'varName': key, 'text': config.i18n.get('UI_setting_' + key + '_text', key),
                                     'tooltip': config.i18n.get('UI_setting_' + key + '_tooltip', '')})
        else:
            if 'enabled' in values:
                controls.append({'type': 'CheckBox', 'varName': 'enabled', 'text': config.i18n.get('UI_native_enabled', 'Enable mod'),
                                 'tooltip': config.i18n.get('UI_native_enabled_tooltip', '')})
            columns = config.getControlColumns()
            if len(columns) != 2:
                raise ValueError('Expected two settings columns: ' + config.NAME)
            for column, declarations in enumerate(columns):
                for item in declarations:
                    control = resolve(item, config.i18n, values)
                    control['column'] = column
                    controls.append(control)
        title = config.i18n['UI_description'] if getattr(config, 'TRANSLATED_TITLE', True) and not getattr(config, 'AUTOMATIC_CONTROLS', False) else config.NAME
        controls = copy.deepcopy(controls)
        active, defaultValues = {}, {}
        for control in controls:
            key = control.get('varName')
            if key is None: continue
            path = control.get('path', [key])
            try:
                active[key] = copy.deepcopy(path_value(values, path))
            except (KeyError, IndexError, TypeError):
                raise ValueError('Unknown setting: ' + key)
            try: defaultValues[key] = copy.deepcopy(path_value(defaults, path))
            except (KeyError, IndexError, TypeError): defaultValues[key] = copy.deepcopy(active[key])
            control.setdefault('text', config.i18n.get('UI_setting_' + key + '_text', key))
            if not control.get('tooltip'):
                control['tooltip'] = nested_description(path, config.i18n)
            if control.get('jsonValue'):
                for source in (active, defaultValues):
                    source[key] = json.dumps(source[key], ensure_ascii=False)
            if control.get('optionValues') is not None:
                choices = control['optionValues']
                for source in (active, defaultValues):
                    if source[key] not in choices: raise ValueError('Invalid option: ' + key)
                    source[key] = choices.index(source[key])
        for control in controls:
            if control['type'] == 'HotKey':
                key = control['varName']
                for source in (active, defaultValues):
                    source[key] = [list(group) if isinstance(group, (list, tuple)) else [group] for group in source[key]]
        result = {'id': modID, 'title': title, 'controls': controls,
                  'values': active, 'defaults': defaultValues, 'labels': dict(config.i18n)}
        if hasattr(config, 'getPanelPreview'):
            result['preview'] = config.getPanelPreview()
        return result

    def catalog(self):
        return [{'id': key, 'title': key} for key in sorted(self.entries)]

    def apply(self, modID, values):
        config, defaults = self.entries[modID]
        description = self.describe(modID)
        if set(values) != set(description['values']): raise ValueError('Incomplete settings')
        for control in description['controls']:
            key = control.get('varName')
            if key is None: continue
            kind, value = control['type'], values[key]
            try:
                if kind == 'CheckBox':
                    if type(value) is not bool: raise ValueError('Invalid switch')
                elif kind in ('Dropdown', 'RadioButtonGroup'):
                    if type(value) is not int or not 0 <= value < len(control['options']): raise ValueError('Invalid option')
                elif kind in ('Slider', 'NumericStepper'):
                    if type(value) not in (int, float) or math.isnan(value) or math.isinf(value): raise ValueError('Invalid number')
                    if 'minimum' in control and value < control['minimum'] or 'maximum' in control and value > control['maximum']: raise ValueError('Number out of range')
                    # Decimal controls can start with an integer JSON value (scale=1).
                    decimal = any(type(control.get(name)) is float
                                  for name in ('minimum', 'maximum', 'snapInterval'))
                    if not decimal and type(description['values'][key]) is int:
                        if value != int(value): raise ValueError('Integer required')
                        values[key] = int(value)
                elif kind in ('TextInput', 'TextArea', 'ColorChoice'):
                    if not isinstance(value, string_types): raise ValueError('Text required')
                    if kind == 'ColorChoice' and not re.match(r'^(?:#|0x)?[0-9a-fA-F]{6}$', value): raise ValueError('Invalid color')
                elif kind == 'HotKey':
                    if not isinstance(value, list) or len(value) > 4: raise ValueError('Invalid hotkey')
                    for group in value:
                        if not isinstance(group, list) or not group or len(group) > 4: raise ValueError('Invalid hotkey')
                        if any(not valid_key_code(code) for code in group): raise ValueError('Invalid key code')
                else: raise ValueError('Unsupported control: ' + kind)
            except ValueError as error:
                LOG.warning('Rejected setting: mod=%s field=%s control=%s reason=%s',
                            modID, key, kind, error)
                raise
        current = config.data
        settings = {}
        for control in description['controls']:
            key = control.get('varName')
            if key is None: continue
            value = copy.deepcopy(values[key])
            if control.get('jsonValue'):
                value = json.loads(value)
            if control.get('optionValues') is not None: value = control['optionValues'][value]
            path = control.get('path', [key])
            if len(path) == 1: settings[path[0]] = value
            else:
                if path[0] not in settings: settings[path[0]] = copy.deepcopy(current[path[0]])
                set_path(settings, path, value)
        from driftkings.settings.service import settings_service
        settings_service.apply(config, settings)
        return self.describe(modID)

    def button(self, modID, key, value):
        config, defaults = self.entries[modID]
        controls = self.describe(modID)['controls']
        if not any(c.get('varName') == key and c.get('button') is not None for c in controls):
            raise ValueError('Unknown action')
        config.onButtonPress(key, value)


registry = SettingsRegistry()
