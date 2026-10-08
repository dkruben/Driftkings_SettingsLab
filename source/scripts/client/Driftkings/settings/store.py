# -*- coding: utf-8 -*-
"""Atomic JSON writer and reader for importing the previous central document."""
import copy
import json
import os
import shutil
import tempfile


def merge(base, values):
    result = copy.deepcopy(base)
    for key, value in values.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def recover_file(target):
    previous = target + '.previous'
    if not os.path.exists(target) and os.path.isfile(previous):
        os.rename(previous, target)


def replace_file(source, target):
    replace = getattr(os, 'replace', None)
    if callable(replace):
        replace(source, target)
        return
    if os.name != 'nt':
        os.rename(source, target)
        return
    # The game's Python 2.7 does not include the native _ctypes module.
    # Preserve the old document until the new one has been published.
    recover_file(target)
    previous = target + '.previous'
    if os.path.exists(previous):
        os.remove(previous)
    had_target = os.path.isfile(target)
    if had_target:
        os.rename(target, previous)
    try:
        os.rename(source, target)
    except Exception:
        if had_target:
            os.rename(previous, target)
        raise
    if had_target:
        os.remove(previous)


def read_object(path):
    """Recover and read a UTF-8 JSON object; never rewrite malformed input."""
    recover_file(path)
    with open(path, 'rb') as stream:
        value = json.loads(stream.read().decode('utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object: ' + path)
    return value


class JsonDocuments(object):
    """Publish related JSON files together, rolling back an interrupted write."""
    def __init__(self, directory, filenames):
        self.directory = directory
        self.filenames = frozenset(filenames)

    def _path(self, name):
        if name not in self.filenames or os.path.basename(name) != name:
            raise ValueError('Invalid settings transaction file: ' + name)
        return os.path.join(self.directory, name)

    def recover(self):
        journal = os.path.join(self.directory, '.transaction.json')
        recover_file(journal)
        if not os.path.isfile(journal):
            return
        previous = read_object(journal)
        # Validate the entire journal before modifying the first document.
        for name, value in previous.items():
            self._path(name)
            if value is not None and not isinstance(value, dict):
                raise ValueError('Invalid settings transaction value: ' + name)
        for name, value in previous.items():
            path = self._path(name)
            if value is None:
                if os.path.isfile(path):
                    os.remove(path)
            else:
                SettingsStore(path).write(value)
        os.remove(journal)

    def publish(self, updates):
        self.recover()
        if not updates:
            return
        previous = {}
        for path, value in updates:
            name = os.path.basename(path)
            if os.path.normcase(os.path.abspath(path)) != os.path.normcase(os.path.abspath(self._path(name))):
                raise ValueError('Settings transaction path is outside its directory')
            if name in previous or not isinstance(value, dict):
                raise ValueError('Invalid settings transaction update: ' + name)
            json.dumps(value, ensure_ascii=False)
            recover_file(path)
            previous[name] = read_object(path) if os.path.isfile(path) else None
        journal = os.path.join(self.directory, '.transaction.json')
        SettingsStore(journal).write(previous)
        try:
            for path, value in updates:
                SettingsStore(path).write(value)
            os.remove(journal)
        except Exception:
            self.recover()
            raise


class SettingsStore(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)

    def read(self):
        recover_file(self.path)
        if not os.path.exists(self.path):
            return {'version': 1, 'components': {}}
        with open(self.path, 'rb') as stream:
            document = json.loads(stream.read().decode('utf-8-sig'))
        if not isinstance(document, dict) or document.get('version') != 1:
            raise ValueError('Unsupported Driftkings settings document')
        sections = document.get('components')
        if not isinstance(sections, dict) or any(not isinstance(value, dict) for value in sections.values()):
            raise ValueError('Invalid Driftkings component settings')
        return document

    def write(self, document):
        content = json.dumps(document, ensure_ascii=False, indent=4, sort_keys=True).encode('utf-8')
        directory = os.path.dirname(self.path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        descriptor, temporary = tempfile.mkstemp(prefix='Driftkings-', suffix='.tmp', dir=directory)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            if os.path.isfile(self.path):
                shutil.copy2(self.path, self.path + '.bak')
            replace_file(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)

    def load(self, component, defaults, legacy=None):
        document = self.read()
        sections = document['components']
        if component not in sections:
            values = legacy() if legacy is not None else {}
            if not isinstance(values, dict):
                raise ValueError('Invalid legacy settings for ' + component)
            sections[component] = merge(defaults, values)
            self.write(document)
        return merge(defaults, sections[component])

    def save(self, component, values):
        if not isinstance(values, dict):
            raise ValueError('Component settings must be a dictionary')
        document = self.read()
        document['components'][component] = merge(document['components'].get(component, {}), values)
        self.write(document)
        return copy.deepcopy(values)


def load_config(config):
    def legacy():
        from Driftkings.common.config.json_reader import JSONLoader
        path = os.path.join(config.configPath, config.ID + '.json')
        if not os.path.isfile(path):
            return {}
        text, _, success = JSONLoader.json_file_read(path, False)
        if not success:
            raise IOError('Could not read legacy settings: ' + path)
        return JSONLoader.json_loads(text)
    from Driftkings.settings.loader import settings_loader
    return settings_loader.load(config.ID, config.data, legacy)
