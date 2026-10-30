# -*- coding: utf-8 -*-
"""Shared locale identifiers for the mod catalogs and settings panel."""
from __future__ import unicode_literals

LANGUAGES = (
    ('cs', 'Čeština'), ('de', 'Deutsch'), ('en', 'English'),
    ('es', 'Español'), ('fr', 'Français'), ('hu', 'Magyar'),
    ('it', 'Italiano'), ('ja', '日本語'), ('ko', '한국어'),
    ('pl', 'Polski'), ('pt', 'Português'), ('ru', 'Русский'),
    ('th', 'ไทย'), ('tr', 'Türkçe'), ('uk', 'Українська'),
    ('vi', 'Tiếng Việt'), ('zh_cn', '简体中文'), ('zh_tw', '繁體中文'),
)
CODES = tuple(code for code, _ in LANGUAGES)
ALIASES = {
    'cz': 'cs', 'jp': 'ja', 'kr': 'ko', 'vn': 'vi',
    'zh': 'zh_cn', 'zh_sg': 'zh_cn', 'zh_hans': 'zh_cn',
    'zh_hans_cn': 'zh_cn', 'zh_hans_sg': 'zh_cn',
    'zh_hk': 'zh_tw', 'zh_mo': 'zh_tw', 'zh_hant': 'zh_tw',
    'zh_hant_tw': 'zh_tw', 'zh_hant_hk': 'zh_tw',
}


# Returns the language code for a given language identifier.
def language_code(language):
    code = str(language or 'en').strip().lower().replace('-', '_')
    if code in ALIASES:
        return ALIASES[code]
    if code in CODES:
        return code
    for known in sorted(tuple(CODES) + tuple(ALIASES), key=len, reverse=True):
        if code.startswith(known + '_'):
            return ALIASES.get(known, known)
    # Regional English, Spanish and Portuguese use their existing catalogs.
    base = code.split('_')[0]
    return ALIASES.get(base, base) if base in CODES or base in ALIASES else 'en'
