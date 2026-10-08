# -*- coding: utf-8 -*-
"""Bounded, strict schema 1 release metadata. No IO or installation."""
import json
import re
from Driftkings.core.updater.versioning import Version, TEXT, normalize_game_version, game_key
from Driftkings.core.updater.endpoints import validate_https

MAX_MANIFEST = 64 * 1024
MAX_PACKAGE = 64 * 1024 * 1024
REQUIRED = frozenset(('schema', 'version', 'channel', 'gameVersion', 'file', 'size', 'sha256', 'download'))
OPTIONAL = frozenset(('minGameVersion', 'maxGameVersion', 'changelog'))
try:
    INTEGER = (int, long)
except NameError:
    INTEGER = (int,)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def bounded_json(raw, maximum=MAX_MANIFEST):
    if not isinstance(raw, (bytes,) + TEXT):
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
            if type(document['schema']) not in INTEGER or document['schema'] != 1:
                raise ValueError('Unknown manifest schema')
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
            if document['file'] != 'Driftkings.wotmod':
                raise ValueError('Unexpected package name')
            if type(document['size']) not in INTEGER or not 0 < document['size'] <= MAX_PACKAGE:
                raise ValueError('Invalid package size')
            if not isinstance(document['sha256'], TEXT) or re.match(r'\A[0-9a-fA-F]{64}\Z', document['sha256']) is None:
                raise ValueError('Invalid SHA-256')
            validate_https(document['download'])
            changelog = document.get('changelog', [])
            if (not isinstance(changelog, list) or len(changelog) > 50 or
                    any(not isinstance(line, TEXT) or len(line) > 500 for line in changelog) or
                    sum(len(line.encode('utf-8')) for line in changelog) > 16 * 1024):
                raise ValueError('Invalid changelog')
            self.changelog = tuple(changelog)
            self.size = document['size']
            self.sha256 = document['sha256'].lower()
            self.download = document['download']
        except (TypeError, KeyError, OverflowError) as error:
            raise ValueError('Invalid manifest types')

    @classmethod
    def parse(cls, raw):
        return cls(bounded_json(raw))

    def compatible(self, client_version):
        normalized = normalize_game_version(client_version)
        return normalized is not None and game_key(self.minimum) <= game_key(normalized) <= game_key(self.maximum)

    def document(self):
        return dict(schema=1, version=self.version.text, channel=self.channel,
                    gameVersion=self.game_version, minGameVersion=self.minimum,
                    maxGameVersion=self.maximum, file='Driftkings.wotmod', size=self.size,
                    sha256=self.sha256, download=self.download, changelog=list(self.changelog))
