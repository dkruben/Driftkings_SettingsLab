# -*- coding: utf-8 -*-
"""Interface catalogs; English is complete and the fallback for every key.

Add a text/<code>.yml resource and register it in driftkings.locale_support.
Optional overrides: <config root>/locales/<code>.json (strings only).
"""
import json
import os

from driftkings.i18n.resources import resources
from driftkings.locale_support import language_code as normalize
from driftkings.locale_support import LANGUAGES
from driftkings.logger import get_logger

logger = get_logger('driftkings.i18n.panel')
try:
    text_types = (str, unicode)
except NameError:
    text_types = (str,)


def is_text(value):
    return isinstance(value, text_types)

def _catalog(code):
    return resources.load(code)['PANEL']


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
