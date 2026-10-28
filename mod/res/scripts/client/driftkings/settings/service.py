# -*- coding: utf-8 -*-
"""Shared settings access and notifications after successful application."""
import copy

from driftkings.logger import get_logger
from driftkings.settings.settings_data import part_name, user_settings
from driftkings.settings.store import merge

LOG = get_logger('Driftkings.Settings')


def changed_paths(before, after, prefix=()):
    """Report changed dictionary leaves; lists and scalars are atomic values."""
    paths = set()
    for key in set(before) | set(after):
        path = prefix + (key,)
        if key not in before or key not in after:
            paths.add(path)
        elif isinstance(before[key], dict) and isinstance(after[key], dict):
            paths.update(changed_paths(before[key], after[key], path))
        elif before[key] != after[key]:
            paths.add(path)
    return frozenset(paths)


class SettingsChanges(dict):
    """Complete changed sections, with paths for selective consumers."""
    def __init__(self, values=(), paths=None):
        super(SettingsChanges, self).__init__(values)
        self.paths = frozenset((key,) for key in self) if paths is None else frozenset(paths)


def affects(changes, *options):
    try:
        paths = changes.paths
    except AttributeError:
        paths = tuple((key,) for key in changes)
    for option in options:
        option = tuple(option) if isinstance(option, (tuple, list)) else (option,)
        for path in paths:
            length = min(len(option), len(path))
            if option[:length] == path[:length]:
                return True
    return False


class SettingsChanged(object):
    def __init__(self):
        self._listeners = []

    def connect(self, callback, component=None, keys=None):
        self.disconnect(callback)
        section = component.NAME if hasattr(component, 'NAME') else part_name(component) if component is not None else None
        self._listeners.append((callback, section, frozenset(keys) if keys is not None else None))

    def disconnect(self, callback):
        self._listeners[:] = [entry for entry in self._listeners if entry[0] != callback]

    def emit(self, component, changes):
        for callback, section, keys in tuple(self._listeners):
            if section is not None and section != component:
                continue
            if keys is not None and not keys.intersection(changes):
                continue
            try:
                callback(component, copy.deepcopy(changes))
            except Exception:
                LOG.exception('Settings notification failed: %s', component)


def changed_values(before, after):
    """Return changed top-level values; nested sections remain complete."""
    return dict((key, copy.deepcopy(value)) for key, value in after.items()
                if key not in before or before[key] != value)


def restore(target, snapshot):
    """Preserve dictionary references held by gameplay controllers."""
    for key in list(target):
        if key not in snapshot:
            del target[key]
    for key, value in snapshot.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            restore(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


class SettingsService(object):
    def __init__(self, settings=None, loader=None):
        self.loader = loader
        self.settings = user_settings if settings is None else settings
        self.onModSettingsChanged = SettingsChanged()
        self._applying = set()
        self._handlers = {}

    def initialize(self, section):
        """Own section setup and persistence; definitions never initialize a UI builder."""
        from helpers import getClientLanguage

        from driftkings.core.hooks import hooks
        from driftkings.settings.hotkeys import processHotKeys
        from driftkings.settings.settings_data import default_keys, defaults
        section.runtime_owner = hooks.current
        section.manager = self
        section.defaultKeys = default_keys(section.NAME)
        section.data = defaults(section.NAME)
        processHotKeys(section.data, section.defaultKeys, 'read')
        section.i18n = {}
        section.lang = str(getClientLanguage()).lower()
        section.configPath = './mods/configs/driftkings/%s/' % section.NAME
        section.loadLang()
        # Register only fully loaded sections; a failed load leaves no panel entry.
        restore(section.data, self._read(section))
        self.register(section)
        from driftkings.settings.registry import registry
        registry.register(section)

    def _loader(self):
        if self.loader is not None:
            return self.loader
        from driftkings.settings.loader import settings_loader
        return settings_loader

    def _storage(self, section):
        if section.STORAGE_CLASS is None:
            return None
        return self._loader().split_store(section.NAME, section.STORAGE_CLASS)

    def _read(self, section):
        from driftkings.settings.hotkeys import processHotKeys
        from driftkings.settings.settings_data import defaults
        from driftkings.settings.store import load_config
        store = self._storage(section)
        # File loading works on persisted key names, never on the live dictionary.
        if store is not None:
            values = store.load()
        else:
            values = load_config(section, self._loader(), defaults(section.NAME))
        processHotKeys(values, section.defaultKeys, 'read')
        return section.normalize_loaded(values)

    def _save(self, section, values):
        from driftkings.settings.hotkeys import processHotKeys
        persisted = copy.deepcopy(values)
        processHotKeys(persisted, section.defaultKeys, 'write')
        store = self._storage(section)
        if store is None:
            self._loader().save(section.NAME, persisted)
        else:
            store.save(persisted)

    def register(self, config):
        self.settings.register(config)
        self._bind(config)

    def _bind(self, config):
        section = part_name(config.NAME)
        handler = getattr(config, 'onModSettingsChanged', None)
        previous = self._handlers.get(section)
        if previous == handler:
            return
        if previous is not None:
            self.onModSettingsChanged.disconnect(previous)
        if callable(handler):
            self.onModSettingsChanged.connect(handler, section, getattr(config, 'REFRESH_KEYS', None))
            self._handlers[section] = handler
        else:
            self._handlers.pop(section, None)

    def getConfig(self, component):
        if hasattr(component, 'data') or hasattr(component, 'NAME') and callable(getattr(component, 'getData', None)):
            return component
        key = component.NAME if hasattr(component, 'NAME') else part_name(component)
        return self.settings.configs[key]

    def getComponentDict(self, component):
        # The same live dictionary is used by gameplay and Flash callbacks.
        return self.getConfig(component).data

    def getSetting(self, component, key=None):
        value = self.getComponentDict(component)
        if key is not None:
            for part in key if isinstance(key, (tuple, list)) else (key,):
                value = value[part]
        return value

    def getSettingDictByAliasBattle(self, alias):
        from driftkings.flash.battle.registry import BATTLE_COMPONENTS

        # Registration already links the alias to its config; no second map.
        config = BATTLE_COMPONENTS[alias][1]
        if config is None:
            raise KeyError('Component has no settings: ' + alias)
        return config.data

    def setSetting(self, component, key, value):
        config = self.getConfig(component)
        path = key if isinstance(key, (tuple, list)) else (key,)
        if not path:
            raise ValueError('Empty settings path')
        patch = copy.deepcopy(config.data)
        current = patch
        for part in path[:-1]:
            current = current[part]
        if path[-1] not in current:
            raise KeyError(path[-1])
        current[path[-1]] = copy.deepcopy(value)
        from driftkings.settings.loader import validate_types
        validate_types(config.data, patch)
        return self.apply(config, patch)

    def reload(self, config, quiet=True):
        """Reload external JSON edits through the same notification path."""
        config = self.getConfig(config)
        before = copy.deepcopy(config.data)
        try:
            restore(config.data, self._read(config))
        except Exception:
            restore(config.data, before)
            raise
        changes = changed_values(before, config.data)
        if changes:
            self._bind(config)
            self.onModSettingsChanged.emit(part_name(config.NAME),
                SettingsChanges(changes, changed_paths(before, config.data)))
        return changes

    def apply(self, config, values, persist=True):
        """Normalize and persist a candidate before publishing it to live consumers."""
        if not isinstance(values, dict):
            raise ValueError('Settings must be a dictionary')
        config = self.getConfig(config)
        current = config.data
        before = copy.deepcopy(current)
        candidate = merge(before, values)
        changes = changed_values(before, candidate)
        if not changes:
            return {}
        token = id(config)
        if token in self._applying:
            raise RuntimeError('Recursive settings application: ' + config.NAME)
        self._bind(config)
        self._applying.add(token)
        try:
            if not persist:
                restore(current, candidate)
            elif callable(getattr(config, 'persist_values', None)):
                candidate = config.persist_values(candidate)
                restore(current, candidate)
            else:
                candidate = config.normalize_changes(candidate, changes)
                from driftkings.settings.loader import validate_types
                validate_types(before, candidate)
                self._save(config, candidate)
                restore(current, candidate)
        except Exception:
            restore(current, before)
            raise
        finally:
            self._applying.remove(token)
        current = config.data
        changes = changed_values(before, current)
        if changes:
            section = part_name(config.NAME)
            paths = changed_paths(before, current)
            self.onModSettingsChanged.emit(section, SettingsChanges(
                changes, paths))
        return changes


settings_service = SettingsService()
