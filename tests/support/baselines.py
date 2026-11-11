# -*- coding: utf-8 -*-
"""Versioned historical baselines for the native plugin migrations.

Tests compare the working tree with tests/fixtures/native_baselines.json instead
of calling ``git show <sha>``, so they also pass in shallow clones, exported
trees and after a squash merge. A missing fixture or key is a test error.
"""
import hashlib
import io
import json
import os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fixtures', 'native_baselines.json')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def baseline(name):
    with io.open(PATH, encoding='utf-8') as stream:
        return json.load(stream)['baselines'][name]


def text_hash(value):
    """SHA-256 of UTF-8 text or bytes with CRLF normalised to LF."""
    if not isinstance(value, bytes):
        value = value.encode('utf-8')
    return hashlib.sha256(value.replace(b'\r\n', b'\n')).hexdigest()


def json_hash(value):
    """SHA-256 of canonical JSON: sorted keys, compact separators, ASCII."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode('ascii')).hexdigest()


def file_hash(path):
    with io.open(os.path.join(ROOT, *path.split('/')), 'rb') as stream:
        return text_hash(stream.read())


def changed_catalog_entries(name, current):
    """Names, in catalog order, whose specification differs from the baseline."""
    old = baseline(name)['catalog']
    return [key for key in current if old.get(key) != json_hash(current[key])]
