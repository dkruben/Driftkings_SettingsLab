# -*- coding: utf-8 -*-
"""Portable modpack contract and read-only planning. No game imports or writes."""
import copy
import hashlib
import io
import os
import re
import stat
import zipfile

try:
    TEXT = (basestring,)
    INTEGER = (int, long)
except NameError:
    TEXT = (str,)
    INTEGER = (int,)

MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_FILES = 256
HASH = re.compile(r'\A[0-9a-f]{64}\Z')
GAME = re.compile(r'\A(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z')
NAME = re.compile(r'\A[A-Za-z0-9][A-Za-z0-9_.+-]*\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_relative(path):
    require(isinstance(path, TEXT) and 0 < len(path) <= 240, 'Invalid inventory path')
    parts = path.split('/')
    require(all(NAME.match(part) and part not in ('.', '..') and not part.endswith('.') for part in parts),
            'Invalid inventory path')
    reserved = ('CON', 'PRN', 'AUX', 'NUL') + tuple('COM%d' % i for i in range(1, 10)) + tuple('LPT%d' % i for i in range(1, 10))
    require(all(part.split('.')[0].upper() not in reserved for part in parts), 'Reserved Windows path')
    return path


def signature(value):
    require(isinstance(value, dict) and type(value.get('size')) in INTEGER and 0 < value['size'] <= MAX_FILE,
            'Invalid inventory size')
    require(isinstance(value.get('sha256'), TEXT) and HASH.match(value['sha256']), 'Invalid inventory hash')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_signature(path):
    # This contract also loads standalone in Python 3 build tooling.
    digest = hashlib.sha256()
    with open(path, 'rb') as source:
        for block in iter(lambda: source.read(65536), b''):
            digest.update(block)
    return dict(size=os.path.getsize(path), sha256=digest.hexdigest())


class Inventory(object):
    def __init__(self, document, version, channel, game_version):
        require(isinstance(document, dict)
                and set(document) == set(('schema', 'packageId', 'version', 'channel', 'gameVersion', 'distribution',
                                          'files', 'defaults')),
                'Invalid modpack fields')
        require(type(document['schema']) in INTEGER and document['schema'] == 1
                and document['packageId'] == 'driftkings.modpack',
                'Invalid modpack identity')
        require(document['version'] == version and document['channel'] == channel and channel in ('beta', 'stable') and
                document['gameVersion'] == game_version and isinstance(game_version, TEXT) and GAME.match(game_version),
                'Modpack release identity mismatch')
        self.game_version = game_version
        self.version = version
        self.channel = channel
        require(isinstance(document['distribution'], dict), 'Invalid distribution metadata')
        self.distribution = dict(document['distribution'])
        require(set(self.distribution) == set(('file', 'size', 'sha256')), 'Invalid distribution fields')
        require(self.distribution['file'] == 'Driftkings-%s-WoT-%s.zip' % (version, game_version),
                'Unexpected distribution filename')
        safe_relative(self.distribution['file'])
        signature(self.distribution)
        self.files = self._entries(document['files'], False)
        self.defaults = self._entries(document['defaults'], True)
        kinds = [entry['kind'] for entry in self.files]
        require(kinds.count('code') == 1 and kinds.count('defaults') == 1 and kinds.count('instructions') == 1,
                'Missing or duplicate required modpack members')
        require(sum(entry['size'] for entry in self.files + self.defaults) <= MAX_TOTAL, 'Modpack exceeds limit')
        self._document = copy.deepcopy(document)

    def document(self):
        return copy.deepcopy(self._document)

    def _entries(self, entries, defaults):
        require(isinstance(entries, list) and 0 < len(entries) <= MAX_FILES, 'Invalid inventory entries')
        result, names = [], set()
        for entry in entries:
            require(isinstance(entry, dict) and set(entry) == set(('path', 'kind', 'size', 'sha256')),
                    'Invalid inventory entry')
            path = safe_relative(entry['path'])
            require(path.lower() not in names, 'Duplicate inventory path')
            names.add(path.lower())
            signature(entry)
            kind = entry['kind']
            if defaults:
                require(kind == 'config' and path.startswith('mods/configs/driftkings/') and path.endswith('.json') and
                        not path.startswith('mods/configs/driftkings/cache/'), 'Invalid default destination')
            elif kind == 'defaults':
                require(path == 'Driftkings-defaults.zip', 'Invalid defaults archive')
            elif kind == 'instructions':
                require(path == 'INSTALL.txt', 'Invalid instructions')
            else:
                require(kind in ('code', 'dependency'), 'Unknown member kind')
                prefix = 'mods/' + self.game_version + '/'
                require(path.startswith(prefix) and '/' not in path[len(prefix):] and path.endswith('.wotmod'),
                        'Invalid code destination')
                require((kind == 'code') == (path == prefix + 'driftkings.wotmod'), 'Invalid unified package identity')
            result.append(dict(entry))
        return tuple(result)

    def verify_archive(self, path):
        require(file_signature(path) == dict(size=self.distribution['size'], sha256=self.distribution['sha256']),
                'Distribution size/hash mismatch')
        with zipfile.ZipFile(path) as archive:
            self._verify_members(archive, self.files)
            raw = archive.read('Driftkings-defaults.zip')
        with zipfile.ZipFile(io.BytesIO(raw)) as defaults:
            self._verify_members(defaults, self.defaults)
        return True

    @staticmethod
    def _verify_members(archive, entries):
        expected = dict((entry['path'], entry) for entry in entries)
        members = archive.infolist()
        require(len(members) == len(expected), 'Archive inventory mismatch')
        seen = set()
        for member in members:
            name = safe_relative(member.filename)
            require(name in expected and name.lower() not in seen, 'Unexpected archive member')
            seen.add(name.lower())
            entry = expected[name]
            require(not member.flag_bits & 1 and not stat.S_ISLNK(member.external_attr >> 16) and
                    member.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                        and member.file_size == entry['size'],
                    'Invalid archive member metadata')
            digest = hashlib.sha256()
            with archive.open(member) as stream:
                for block in iter(lambda: stream.read(65536), b''):
                    digest.update(block)
            require(digest.hexdigest() == entry['sha256'], 'Archive member hash mismatch')

    def plan(self, observed, previous=None, owned=()):
        """observed maps owned candidate paths to fresh size/hash values (or None).

        A caller must inspect every candidate before using this plan. Previous
        inventory is provenance only when its recorded bytes still match disk.
        Shared dependencies already present are never claimed as ours.
        """
        require(previous is None or isinstance(previous, Inventory) and previous.game_version == self.game_version,
                'Previous inventory targets another game')
        old = dict((item['path'], item) for item in previous.files
                   if item['kind'] in ('code', 'dependency')) if previous else {}
        require(isinstance(owned, (list, tuple, set, frozenset)) and set(owned).issubset(old),
                'Invalid ownership receipt')
        old = dict((path, entry) for path, entry in old.items() if path in owned)
        current = dict((item['path'], item) for item in self.files if item['kind'] in ('code', 'dependency'))
        candidates = set(old) | set(current)
        require(len(set(path.lower() for path in candidates)) == len(candidates),
                'Case collision between old and new inventory')
        actions = []
        for path in sorted(candidates):
            require(path in observed, 'Missing disk observation: ' + path)
            actual, before, after = observed[path], old.get(path), current.get(path)
            if actual is not None:
                require(set(actual) == set(('size', 'sha256')), 'Invalid disk observation')
                signature(actual)
            def matches(entry):
                return entry is not None and actual == dict(size=entry['size'], sha256=entry['sha256'])
            if after is None:
                # Delete only bytes explicitly owned by the previous inventory.
                action = 'remove' if matches(before) else 'keep_unowned'
            elif matches(after):
                action = 'keep'
            elif actual is None:
                action = 'install'
            elif matches(before):
                action = 'replace'
            elif after['kind'] == 'code' and before is None:
                # First migration needs explicit package identity validation by
                # the installer before ownership can be established.
                action = 'verify_legacy_code'
            else:
                action = 'conflict'
            actions.append(dict(path=path, action=action, before=actual,
                                after=None if after is None else dict(size=after['size'], sha256=after['sha256'])))
        # Configs are never replacement/removal candidates, including defaults
        # removed upstream. The settings service handles missing defaults.
        return actions
