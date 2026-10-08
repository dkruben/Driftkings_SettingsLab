# -*- coding: utf-8 -*-
"""One catalog per language, with unified optional JSON overrides."""
import copy
import importlib
import json
import logging
import os

from Driftkings.settings.store import SettingsStore, merge, recover_file

LANGUAGES = ('cs', 'de', 'en', 'es', 'fr', 'hu', 'it', 'pl', 'pt', 'ru', 'tr', 'uk')
LOG = logging.getLogger('Driftkings.i18n')


def language_code(language):
    code = str(language).lower().replace('-', '_').split('_')[0]
    return code if code in LANGUAGES else 'en'


def read_catalog(path):
    with open(path, 'rb') as stream:
        value = json.loads(stream.read().decode('utf-8-sig'))
    if not isinstance(value, dict) or any(not isinstance(section, dict) for section in value.values()):
        raise ValueError('Expected a catalog with component sections: ' + path)
    return value


def client_text(value):
    # Preserve the UTF-8 strings expected by the existing Python 2 client APIs.
    try:
        text_type = unicode
    except NameError:
        return value
    if isinstance(value, text_type):
        return value.encode('utf-8')
    if isinstance(value, dict):
        return dict((client_text(key), client_text(text)) for key, text in value.items())
    if isinstance(value, list):
        return [client_text(text) for text in value]
    return value


class TranslationCatalog(object):
    def __init__(self, root='./mods/configs/Driftkings'):
        self.root = os.path.abspath(root)
        self.cache = {}

    def bundled(self, language):
        english = importlib.import_module('Driftkings.i18n.en').TEXT
        if language == 'en':
            return copy.deepcopy(english)
        return merge(english, importlib.import_module('Driftkings.i18n.' + language).TEXT)

    def migrate(self, language, components, path):
        sections = {}
        for component in components:
            legacy = os.path.join(self.root, component, 'i18n', language + '.json')
            if not os.path.isfile(legacy):
                continue
            try:
                with open(legacy, 'rb') as stream:
                    value = json.loads(stream.read().decode('utf-8-sig'))
                if not isinstance(value, dict):
                    raise ValueError('Expected an object')
                sections[component] = value
            except (ValueError, IOError) as error:
                # Do not mark migration complete when a source could not be read.
                raise ValueError('Could not import translations from %s: %s' % (legacy, error))
        SettingsStore(path).write(sections)

    def read(self, language):
        language = language_code(language)
        path = os.path.join(self.root, 'i18n', language + '.json')
        try:
            recover_file(path)
            if not os.path.isfile(path):
                self.migrate(language, self.bundled(language), path)
            stat = os.stat(path)
            signature = (stat.st_mtime, stat.st_size)
            if language not in self.cache or self.cache[language][0] != signature:
                overrides = read_catalog(path)
                self.cache[language] = (signature, merge(self.bundled(language), overrides))
            return self.cache[language][1]
        except (ValueError, IOError, OSError):
            LOG.exception('Could not load translation overrides: %s', path)
            return self.bundled(language)

    def section(self, component, language='en'):
        catalog = self.read(language)
        return client_text(merge(catalog.get('common', {}), catalog.get(component, {'UI_description': component})))


catalog = TranslationCatalog()
