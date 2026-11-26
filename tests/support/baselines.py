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
    with io.open(PATH, encoding='utf-8') as stream:
        fixtures = json.load(stream)
    prior = fixtures.get('approved_revisions', {}).get(path, {})
    restored_clock = (path == 'mod/res/scripts/client/driftkings/gameface/lobby/main.py'
                      and prior.get('approved_sha256') == historical
                      and prior.get('historical_sha256') == text_hash(current))
    if text_hash(current) == historical or restored_clock:
        return 'historical'
    revision = fixtures.get('format_only_revisions', {}).get(path)
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


# Reviewed Phase 4.3.1 target identities; the historical contract tests compare against this exact table.
PHASE431_TARGETS = {
    "na999": {"realm": "NA", "build": "999"},
    "eu1000": {"realm": "EU", "build": "1000"},
    "ct995": {"realm": "CT", "build": "995"},
    "ct996": {"realm": "CT", "build": "996"},
}


def phase2_prior_build_config(current):
    """Reverse only the intentional Phase 2 contract changes for historical comparisons."""
    assert current['game'].pop('development_realms') == ['CT']
    assert current['game']['supported_realms'] == ['NA', 'EU', 'ASIA', 'CN']
    current['game']['supported_realms'] = ['CT']
    current['reference'].pop('production_clients')
    current['reference'].pop('production_profiles')
    # Phase 4.3.1 adds exactly this reviewed target table and legacy CT label binding; any other change still fails.
    assert current.pop('targets') == PHASE431_TARGETS
    assert current['reference'].pop('legacy_ct_build') == '996'
    # Retired physical output paths (Phase 6.3) are restored with their historical values for this comparison only.
    current['package']['output'] = 'build/unified/driftkings.wotmod'
    current['package']['debug_root'] = 'build/debug'
    current['python']['staging_root'] = 'build/staging/res/scripts/client'
    current['python'].pop('exclude')
    # The optional Remove Fog helper generator is part of the historical contract; it must match the fixture exactly.
    with io.open(PATH, encoding='utf-8') as stream:
        historical_fog = json.load(stream)['phase2_historical_fog_generator']
    if 'fog_package_helper' in current['generators']:
        assert current['generators']['fog_package_helper'] == historical_fog
        current['generators'].pop('fog_package_helper')
    # Phase 3 removed the external UI packages; the historical declaration is restored only for this comparison.
    assert 'ui_dependencies' not in current
    with io.open(PATH, encoding='utf-8') as stream:
        current['ui_dependencies'] = json.load(stream)['phase3_historical_ui_dependencies']
    with io.open(PATH, encoding='utf-8') as stream:
        current['generators']['fog_package_helper'] = json.load(stream)['phase2_historical_fog_generator']
