# -*- coding: utf-8 -*-
"""Diagnostic JSON only: decode Windows filesystem bytes without changing paths."""
import json
import os
import sys

try:
    UNICODE = unicode
except NameError:
    UNICODE = str


def _to_json_unicode(value):
    if isinstance(value, UNICODE):
        return value
    if isinstance(value, bytes):
        encoding = 'mbcs' if os.name == 'nt' else sys.getfilesystemencoding()
        return value.decode(encoding, 'strict')
    if isinstance(value, dict):
        output = {}
        for key, item in value.items():
            normalized = _to_json_unicode(key)
            if normalized in output:
                raise ValueError('Diagnostic JSON key collision')
            output[normalized] = _to_json_unicode(item)
        return output
    if isinstance(value, (list, tuple)):
        return [_to_json_unicode(item) for item in value]
    return value


def json_bytes(value, indent=None):
    return json.dumps(_to_json_unicode(value), ensure_ascii=False, indent=indent).encode('utf-8')
