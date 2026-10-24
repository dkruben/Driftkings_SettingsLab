# -*- coding: utf-8 -*-
"""One catalog per language, with unified optional JSON overrides."""
import copy
import json
from driftkings.logger import get_logger
import os

from driftkings.i18n.resources import resources
from driftkings.locale_support import language_code
from driftkings.settings.sections import section_name
from driftkings.settings.store import merge, recover_file

LOG = get_logger('driftkings.i18n')


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
    def __init__(self, root='./mods/configs/driftkings'):
        self.root = os.path.abspath(root)
        self.cache = {}

    def bundled(self, language):
        english = resources.load('en')['TEXT']
        if language == 'en':
            return copy.deepcopy(english)
        return merge(english, resources.load(language)['TEXT'])


    def read(self, language):
        language = language_code(language)
        path = os.path.join(self.root, 'i18n', language + '.json')
        try:
            recover_file(path)
            if not os.path.isfile(path):
                return self.bundled(language)
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
        component = section_name(component)
        catalog = self.read(language)
        return client_text(merge(catalog.get('common', {}), catalog.get(component, {'UI_description': component})))


catalog = TranslationCatalog()
