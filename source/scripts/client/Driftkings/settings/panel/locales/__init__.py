# -*- coding: utf-8 -*-
"""Interface catalogs; English is complete and the fallback for every key.

Add a language by creating <code>.py with STRINGS and listing it in LANGUAGES.
Optional overrides: <config root>/locales/<code>.json (strings only).
"""
import json
import os

from Driftkings.settings.panel import logger
from Driftkings.settings.panel.controls import is_text

LANGUAGES = (('en', u'English'), ('pt', u'Português'))


def normalize(language):
    code = str(language or 'en').lower().replace('-', '_')
    for known, _ in LANGUAGES:
        if code == known or code.startswith(known + '_'):
            return known
    return 'en'


def _catalog(code):
    module = __import__('Driftkings.settings.panel.locales.' + code, fromlist=['STRINGS'])
    return dict(module.STRINGS)


def load(language, override_root=None):
    code = normalize(language)
    strings = _catalog('en')
    if code != 'en':
        strings.update(_catalog(code))
    if override_root:
        path = os.path.join(override_root, 'locales', code + '.json')
        if os.path.isfile(path):
            try:
                with open(path, 'rb') as stream:
                    extra = json.loads(stream.read().decode('utf-8-sig'))
                if isinstance(extra, dict):
                    strings.update(dict((k, v) for k, v in extra.items() if is_text(k) and is_text(v)))
            except (IOError, OSError, ValueError) as error:
                logger.warning('Ignored invalid locale override %s: %s', path, error)
    return code, strings


def translations(key):
    """{language: text} for a catalog key, for labels of built-in pages."""
    return dict((code, _catalog(code).get(key, _catalog('en').get(key, key))) for code, _ in LANGUAGES)
