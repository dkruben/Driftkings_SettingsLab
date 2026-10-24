# -*- coding: utf-8 -*-
"""Atomic JSON documents and recoverable multi-file transactions."""
import copy
import json
import os
import tempfile

from driftkings.common.utils.filesystem import recover_file, replace_file


def merge(base, values):
    result = copy.deepcopy(base)
    for key, value in values.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


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
            replace_file(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)


def load_config(config, loader=None, defaults=None):
    if loader is None:
        from driftkings.settings.loader import settings_loader
        loader = settings_loader
    return loader.load(config.NAME, config.data if defaults is None else defaults)
