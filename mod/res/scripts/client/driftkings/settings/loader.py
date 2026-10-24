# -*- coding: utf-8 -*-
"""Python defaults, selected profile and per-feature JSON persistence."""
import copy
import math
import os
import re
import shutil
import tempfile

from driftkings.logger import get_logger
from driftkings.settings.default_values import SELECTOR
from driftkings.settings.settings_data import part_name, SettingsData, user_settings
from driftkings.settings.store import merge, read_object, recover_file, SettingsStore

try:
    string_types = (basestring,)
    number_types = (int, long, float)
except NameError:
    string_types = (str,)
    number_types = (int, float)

LOG = get_logger('Driftkings.Settings')


def validate_types(defaults, values, path=''):
    """Keep extra user keys; reject malformed known options without rewriting them."""
    if not isinstance(values, dict):
        raise ValueError('Expected an object: ' + path)
    for key, default in defaults.items():
        if key not in values or default is None:
            continue
        value = values[key]
        name = path + '.' + str(key) if path else str(key)
        if isinstance(default, dict):
            validate_types(default, value, name)
        elif type(default) is bool:
            if type(value) is not bool:
                raise ValueError('Expected a boolean: ' + name)
        elif isinstance(default, number_types):
            if isinstance(value, bool) or not isinstance(value, number_types):
                raise ValueError('Expected a number: ' + name)
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                raise ValueError('Expected a finite number: ' + name)
        elif isinstance(default, string_types):
            if not isinstance(value, string_types):
                raise ValueError('Expected text: ' + name)
        elif isinstance(default, (tuple, list)) and not isinstance(value, (tuple, list)):
            raise ValueError('Expected a list: ' + name)


class SettingsLoader(object):
    def __init__(self, root, settings=None):
        self.root = os.path.abspath(root)
        self.settings = settings or SettingsData()
        self.defaults = {}
        self._active = None

    def directory(self, name):
        if not isinstance(name, string_types) or not re.match(r'^[A-Za-z0-9_-]{1,64}\Z', name):
            raise ValueError('Profile names may contain letters, digits, _ and -')
        if name.upper() in ('CON', 'PRN', 'AUX', 'NUL') or re.match(r'^(COM|LPT)[0-9]\Z', name.upper()):
            raise ValueError('Reserved profile name: ' + name)
        target = os.path.realpath(os.path.join(self.root, name))
        if not os.path.normcase(target).startswith(os.path.normcase(os.path.realpath(self.root)) + os.sep):
            raise ValueError('Profile path is outside the configuration directory')
        return target

    def selected(self):
        path = os.path.join(self.root, 'load.json')
        recover_file(path)
        if not os.path.isfile(path):
            name = SELECTOR['loadConfig']
            self.directory(name)
            return name
        name = read_object(path).get('loadConfig')
        self.directory(name)
        return name

    @property
    def active(self):
        if self._active is None:
            self._active = self.selected()
            selector = os.path.join(self.root, 'load.json')
            if not os.path.isfile(selector):
                SettingsStore(selector).write({'loadConfig': self._active})
        return self._active

    def select(self, name):
        # Pin the running session before changing the next-start selector.
        current = self.active
        path = self.directory(name)
        if not os.path.isdir(path):
            raise ValueError('Configuration profile does not exist: ' + name)
        SettingsStore(os.path.join(self.root, 'load.json')).write({'loadConfig': name})
        return current != name

    def profiles(self):
        names = set((self.active, self.selected()))
        if os.path.isdir(self.root):
            for name in os.listdir(self.root):
                try:
                    folder = self.directory(name)
                except ValueError:
                    continue
                if not os.path.isdir(folder):
                    continue
                entries = os.listdir(folder)
                # Python 2 list comprehensions leak their variables; keep the folder name intact.
                known = [section + '.json' for section in self.settings.configs]
                if any(key in entries for key in known) or any(section in entries for section in ('team_panels', 'vehicle_carousel', 'minimap_enhancements')):
                    names.add(name)
        return sorted(names)

    def clone(self, name):
        target = self.directory(name)
        if os.path.exists(target):
            raise ValueError('Profile already exists: ' + name)
        source = self.directory(self.active)
        if not os.path.isdir(source):
            raise ValueError('The current profile has not been loaded')
        staging = tempfile.mkdtemp(prefix='.profile-', dir=self.root)
        try:
            for directory, dirs, files in os.walk(source):
                dirs[:] = [item for item in dirs if not item.startswith('.') and not os.path.islink(os.path.join(directory, item))]
                for filename in files:
                    if filename.startswith('.') or not filename.endswith('.json'):
                        continue
                    path = os.path.join(directory, filename)
                    if os.path.islink(path):
                        continue
                    destination = os.path.join(staging, os.path.relpath(path, source))
                    SettingsStore(destination).write(read_object(path))
            os.rename(staging, target)
        finally:
            if os.path.isdir(staging):
                shutil.rmtree(staging)
        return name

    def path(self, component):
        return os.path.join(self.directory(self.active), part_name(component) + '.json')

    def load(self, component, defaults):
        component = part_name(component)
        if component not in self.defaults:
            self.defaults[component] = copy.deepcopy(defaults)
        defaults = self.defaults[component]
        if component == 'minimap_enhancements':
            from driftkings.settings.minimap_store import MinimapStore
            directory = os.path.join(self.directory(self.active), component)
            return MinimapStore(directory).load(defaults)
        path = self.path(component)
        recover_file(path)
        values = read_object(path) if os.path.isfile(path) else {}
        validate_types(defaults, values, component)
        result = merge(defaults, values)
        if not os.path.isfile(path):
            SettingsStore(path).write(result)
        return result

    def save(self, component, values):
        component = part_name(component)
        if component == 'minimap_enhancements':
            from driftkings.settings.minimap_store import MinimapStore
            directory = os.path.join(self.directory(self.active), part_name(component))
            validate_types(self.defaults.get(component, {}), values, component)
            return MinimapStore(directory).save(values)
        path = self.path(component)
        recover_file(path)
        previous = read_object(path) if os.path.isfile(path) else {}
        candidate = merge(previous, values)
        validate_types(self.defaults.get(component, {}), candidate, component)
        SettingsStore(path).write(candidate)
        return copy.deepcopy(candidate)

    def split_store(self, component, factory):
        target = os.path.join(self.directory(self.active), part_name(component))
        return factory(target)


settings_loader = SettingsLoader('./mods/configs/driftkings', user_settings)
