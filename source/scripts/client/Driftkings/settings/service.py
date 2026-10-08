# -*- coding: utf-8 -*-
"""Shared settings access and notifications after successful application."""
import copy
import logging

from Driftkings.settings.settings_data import user_settings, part_name
from Driftkings.settings.store import merge

LOG = logging.getLogger('Driftkings.Settings')


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
    paths = getattr(changes, 'paths', tuple((key,) for key in changes))
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
    def __init__(self, settings=None):
        self.settings = user_settings if settings is None else settings
        self.onModSettingsChanged = SettingsChanged()
        self._applying = set()
        self._handlers = {}

    def register(self, config):
        self.settings.register(config)
        self._bind(config)

    def _bind(self, config):
        section = part_name(config.ID)
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
        if hasattr(component, 'data') or hasattr(component, 'ID') and callable(getattr(component, 'getData', None)):
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
        from Driftkings.views import BATTLE_COMPONENTS
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
        from Driftkings.settings.loader import validate_types
        validate_types(config.data, patch)
        return self.apply(config, patch)

    def reload(self, config, quiet=True):
        """Reload external JSON edits through the same notification path."""
        config = self.getConfig(config)
        before = copy.deepcopy(config.data)
        try:
            config.readData(quiet)
            config.readCurrentSettings(quiet)
        except Exception:
            restore(config.data, before)
            raise
        changes = changed_values(before, config.data)
        if changes:
            self._bind(config)
            self.onModSettingsChanged.emit(part_name(config.ID),
                SettingsChanges(changes, changed_paths(before, config.data)))
        return changes

    def apply(self, config, values, block=None, persist=True):
        """Keep feature validation/storage, suppress no-ops, then publish a diff."""
        if not isinstance(values, dict):
            raise ValueError('Settings must be a dictionary')
        config = self.getConfig(config)
        current = config.data if block is None else config.getData(block)
        before = copy.deepcopy(current)
        changes = changed_values(before, merge(before, values))
        if not changes:
            return {}
        token = (id(config), block)
        if token in self._applying:
            raise RuntimeError('Recursive settings application: ' + config.ID)
        self._bind(config)
        self._applying.add(token)
        try:
            if not persist:
                restore(current, merge(before, values))
            elif block is None:
                config.onApplySettings(changes)
            else:
                config.onApplySettings(changes, blockID=block)
        except Exception:
            restore(current, before)
            raise
        finally:
            self._applying.remove(token)
        current = config.data if block is None else config.getData(block)
        changes = changed_values(before, current)
        if changes:
            section = part_name(config.ID)
            paths = changed_paths(before, current)
            if block is not None:
                paths = frozenset((block,) + path for path in paths)
            self.onModSettingsChanged.emit(section, SettingsChanges(
                changes if block is None else {block: changes}, paths))
        return changes


settings_service = SettingsService()
