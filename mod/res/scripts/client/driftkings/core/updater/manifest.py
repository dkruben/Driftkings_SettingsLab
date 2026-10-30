# -*- coding: utf-8 -*-
"""Bounded release metadata: legacy package or complete modpack. No IO."""
import json
import re

from driftkings.common.utils.compat import integer_types, string_types
from driftkings.core.updater.endpoints import official_release_url
from driftkings.core.updater.inventory import Inventory
from driftkings.core.updater.versioning import game_key, normalize_game_version, Version

MAX_MANIFEST = 64 * 1024
MAX_PACKAGE = 64 * 1024 * 1024
REQUIRED = frozenset(('schema', 'version', 'channel', 'gameVersion', 'file', 'size', 'sha256', 'download'))
OPTIONAL = frozenset(('minGameVersion', 'maxGameVersion', 'changelog', 'modpack'))

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def bounded_json(raw, maximum=MAX_MANIFEST):
    if not isinstance(raw, (bytes,) + string_types):
        raise ValueError('Expected JSON text')
    data = raw.encode('utf-8') if not isinstance(raw, bytes) else raw
    if len(data) > maximum:
        raise ValueError('Response exceeds limit')
    return json.loads(data.decode('utf-8'), object_pairs_hook=unique_object)


class Manifest(object):
    def __init__(self, document):
        if not isinstance(document, dict) or not REQUIRED.issubset(document) or set(document) - REQUIRED - OPTIONAL:
            raise ValueError('Invalid manifest fields')
        try:
            if len(json.dumps(document, ensure_ascii=False).encode('utf-8')) > MAX_MANIFEST:
                raise ValueError('Manifest exceeds limit')
            if type(document['schema']) not in integer_types or document['schema'] not in (1, 2):
                raise ValueError('Unknown manifest schema')
            self.schema = document['schema']
            if (self.schema == 2) != ('modpack' in document):
                raise ValueError('Manifest schema requires a complete modpack')
            self.version = Version(document['version'])
            self.channel = document['channel']
            if self.channel not in ('stable', 'beta') or not self.version.allowed(self.channel):
                raise ValueError('Invalid release channel')
            if (self.channel == 'beta') != bool(self.version.prerelease):
                raise ValueError('Release channel disagrees with version')
            for name in ('gameVersion', 'minGameVersion', 'maxGameVersion'):
                if name in document and normalize_game_version(document[name]) != document[name]:
                    raise ValueError('Manifest game version must be normalized')
            self.game_version = document['gameVersion']
            self.minimum = document.get('minGameVersion', self.game_version)
            self.maximum = document.get('maxGameVersion', self.game_version)
            if not game_key(self.minimum) <= game_key(self.game_version) <= game_key(self.maximum):
                raise ValueError('Invalid game version range')
            if document['file'] != 'driftkings.wotmod':
                raise ValueError('Unexpected package name')
            if type(document['size']) not in integer_types or not 0 < document['size'] <= MAX_PACKAGE:
                raise ValueError('Invalid package size')
            if not isinstance(document['sha256'], string_types) or re.match(r'\A[0-9a-fA-F]{64}\Z', document['sha256']) is None:
                raise ValueError('Invalid SHA-256')
            official_release_url(document['download'])
            changelog = document.get('changelog', [])
            if (not isinstance(changelog, list) or len(changelog) > 50 or
                    any(not isinstance(line, string_types) or len(line) > 500 for line in changelog) or
                    sum(len(line.encode('utf-8')) for line in changelog) > 16 * 1024):
                raise ValueError('Invalid changelog')
            self.changelog = tuple(changelog)
            self.size = document['size']
            self.sha256 = document['sha256'].lower()
            self.download = document['download']
            self.inventory = None
            self.payload_size, self.payload_sha256 = self.size, self.sha256
            if self.schema == 2:
                self.inventory = Inventory(document['modpack'], self.version.text, self.channel, self.game_version)
                code = next(item for item in self.inventory.files if item['kind'] == 'code')
                if code['size'] != self.size or code['sha256'] != self.sha256:
                    raise ValueError('Modpack code differs from release package')
                # Code and distribution must be assets of the same release.
                if not self.download.endswith('/driftkings.wotmod'):
                    raise ValueError('Invalid package asset URL')
                self.download = self.download.rsplit('/', 1)[0] + '/' + self.inventory.distribution['file']
                official_release_url(self.download)
                self.payload_size = self.inventory.distribution['size']
                self.payload_sha256 = self.inventory.distribution['sha256']
        except (TypeError, KeyError, OverflowError):
            raise ValueError('Invalid manifest types')

    @classmethod
    def parse(cls, raw):
        return cls(bounded_json(raw))

    def compatible(self, client_version):
        normalized = normalize_game_version(client_version)
        if self.inventory is not None and normalized != self.game_version:
            return False
        return normalized is not None and game_key(self.minimum) <= game_key(normalized) <= game_key(self.maximum)

    def document(self):
        download = self.download if self.inventory is None else self.download.rsplit('/', 1)[0] + '/driftkings.wotmod'
        document = dict(schema=self.schema, version=self.version.text, channel=self.channel, gameVersion=self.game_version, minGameVersion=self.minimum, maxGameVersion=self.maximum, file='driftkings.wotmod', size=self.size, sha256=self.sha256, download=download, changelog=list(self.changelog))
        if self.inventory is not None:
            document['modpack'] = self.inventory.document()
        return document
