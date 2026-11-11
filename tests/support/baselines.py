# -*- coding: utf-8 -*-
"""Versioned historical baselines for the native plugin migrations.

Tests compare the working tree with tests/fixtures/native_baselines.json instead
of calling ``git show <sha>``, so they also pass in shallow clones, exported
trees and after a squash merge. A missing fixture or key is a test error.
"""
import ast
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


def normalized_ast(source):
    """Dump of the syntax tree with each run of consecutive imports sorted.

    Insensitive to layout, comments and import ordering only; any other change
    to names, values, statements or their order produces a different dump. The
    dump depends on the interpreter, so compare two sources in the same process
    and never store it.
    """
    tree = ast.parse(source)
    imports = (ast.Import, ast.ImportFrom)
    for node in ast.walk(tree):
        for field in ('body', 'orelse', 'finalbody'):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            result, run = [], []
            for statement in block + [None]:
                if isinstance(statement, imports):
                    run.append(statement)
                    continue
                result.extend(sorted(run, key=ast.dump))
                run = []
                if statement is not None:
                    result.append(statement)
            block[:] = result
    return ast.dump(tree)


def protected_file(base, path, current=None):
    """Check a protected file against a historical baseline; AssertionError otherwise.

    Returns 'historical' when the bytes equal the hash recorded from the baseline
    commit. Returns 'format_only' when the file differs but the fixture records a
    format-only revision whose stored historical source still hashes to that
    historical value, whose normalized syntax tree equals the current one, and
    whose exact revised hash equals the current file. Historical hashes are never
    replaced. ``current`` (bytes) overrides the working-tree content.
    """
    if current is None:
        with io.open(os.path.join(ROOT, *path.split('/')), 'rb') as stream:
            current = stream.read()
    historical = base['files'][path]
    if text_hash(current) == historical:
        return 'historical'
    with io.open(PATH, encoding='utf-8') as stream:
        revision = json.load(stream).get('format_only_revisions', {}).get(path)
    if revision is None:
        raise AssertionError('%s differs from its historical baseline and has no recorded format-only revision' % path)
    if revision['historical_sha256'] != historical or text_hash(revision['historical_source']) != historical:
        raise AssertionError('%s: recorded historical source does not match the baseline hash' % path)
    if normalized_ast(current) != normalized_ast(revision['historical_source'].encode('utf-8')):
        raise AssertionError('%s: functional change against the historical baseline' % path)
    if text_hash(current) != revision['revised_sha256']:
        raise AssertionError('%s: content differs from the recorded format-only revision' % path)
    return 'format_only'


def changed_catalog_entries(name, current):
    """Names, in catalog order, whose specification differs from the baseline."""
    old = baseline(name)['catalog']
    return [key for key in current if old.get(key) != json_hash(current[key])]
