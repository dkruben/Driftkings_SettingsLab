# -*- coding: utf-8 -*-
"""Python defaults, selected profile and per-feature JSON persistence."""
import copy
import math
import os
import re
import shutil
import tempfile

from Driftkings.settings.settings_data import SettingsData, user_settings, part_name
from Driftkings.settings.store import SettingsStore, merge, recover_file, read_object

try:
    string_types = (basestring,)
    number_types = (int, long, float)
except NameError:
    string_types = (str,)
    number_types = (int, float)


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
            return 'default'
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
                known = [key + '.json' for key in self.settings.configs]
                if any(key in entries for key in known) or any(key in entries for key in ('player_panel_pro', 'carousel_stats', 'minimap_plugins')):
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

    def load(self, component, defaults, legacy=None):
        if component not in self.defaults:
            self.defaults[component] = copy.deepcopy(defaults)
        defaults = self.defaults[component]
        if component == 'MinimapPlugins':
            from Driftkings.settings.minimap_store import MinimapStore
            directory = os.path.join(self.directory(self.active), part_name(component))
            if os.path.isdir(directory):
                MinimapStore(directory).recover()
                if os.path.isfile(os.path.join(directory, 'minimap.json')):
                    return MinimapStore(directory).load(defaults)
        path = self.path(component)
        recover_file(path)
        if os.path.isfile(path):
            values = read_object(path)
        else:
            values = {}
            if self.active == 'default':
                central = SettingsStore(os.path.join(self.root, 'Driftkings.json')).read()['components']
                values = central.get(component)
                if values is None:
                    values = legacy() if legacy else {}
            validate_types(defaults, values, component)
            values = merge(defaults, values)
            SettingsStore(path).write(values)
        validate_types(defaults, values, component)
        if component == 'MinimapPlugins':
            # Keep the previous single file untouched as a migration backup.
            initial = merge(defaults, values)
            if not initial.get('minimapSchema'):
                for item in initial['circles'].values():
                    item['alpha'] = initial['alpha']
                initial['minimapSchema'] = 1
            return MinimapStore(directory).load(initial)
        return merge(defaults, values)

    def save(self, component, values):
        if component == 'MinimapPlugins':
            from Driftkings.settings.minimap_store import MinimapStore
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

    def split_store(self, component, factory, files, legacy_directory):
        target = os.path.join(self.directory(self.active), part_name(component))
        def create(directory, migrating=False):
            if component == 'PlayerPanelPro':
                return factory(directory, legacy_root=self.root if migrating and self.active == 'default' else False)
            return factory(directory)
        if os.path.isdir(target):
            return create(target)
        profile = self.directory(self.active)
        if not os.path.isdir(profile):
            os.makedirs(profile)
        staging = tempfile.mkdtemp(prefix='.settings-', dir=profile)
        try:
            if self.active == 'default':
                migration_files = tuple(files) + (('.transaction.json',) if component == 'PlayerPanelPro' else ())
                if component == 'PlayerPanelPro':
                    from Driftkings.settings.player_panel_store import LEGACY_FILES
                    migration_files += LEGACY_FILES
                for name in migration_files:
                    source = os.path.join(legacy_directory, name)
                    recover_file(source)
                    if os.path.isfile(source):
                        SettingsStore(os.path.join(staging, name)).write(read_object(source))
            # Use each feature's own validator and existing split-file migration.
            create(staging, True).load()
            os.rename(staging, target)
        finally:
            if os.path.isdir(staging):
                shutil.rmtree(staging)
        return create(target)


settings_loader = SettingsLoader('./mods/configs/Driftkings', user_settings)
