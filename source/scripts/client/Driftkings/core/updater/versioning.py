# -*- coding: utf-8 -*-
"""Product SemVer precedence and separate four-part client versions (Python 2.7)."""
import re
from functools import total_ordering

try:
    TEXT = (basestring,)
except NameError:
    TEXT = (str,)

_SEMVER = re.compile(r'\A(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?\Z')
_GAME = re.compile(r'\A\s*(?:v\.)?([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)(?:\s+#[0-9]+)?\s*\Z')


@total_ordering
class Version(object):
    def __init__(self, value):
        match = _SEMVER.match(value) if isinstance(value, TEXT) else None
        if match is None:
            raise ValueError('Invalid semantic version')
        self.text = value
        self.release = tuple(int(part) for part in match.groups()[:3])
        self.prerelease = tuple(match.group(4).split('.')) if match.group(4) else ()
        self.metadata = match.group(5) or ''
        for part in self.prerelease:
            if part.isdigit() and len(part) > 1 and part.startswith('0'):
                raise ValueError('Leading zero in prerelease')
        identifiers = tuple((0, int(part)) if part.isdigit() else (1, part) for part in self.prerelease)
        self._key = (self.release, not bool(self.prerelease), identifiers)

    def __eq__(self, other):
        return self._key == other._key if isinstance(other, Version) else NotImplemented

    def __lt__(self, other):
        return self._key < other._key if isinstance(other, Version) else NotImplemented

    def __hash__(self):
        return hash(self._key)

    def allowed(self, channel):
        if channel not in ('stable', 'beta'):
            raise ValueError('Invalid update channel')
        return not self.prerelease or (channel == 'beta' and self.prerelease[0] in ('beta', 'rc'))


def normalize_game_version(value):
    """Unknown/malformed runtime versions stay unknown, never assumed compatible."""
    match = _GAME.match(value) if isinstance(value, TEXT) else None
    if match is None:
        return None
    return '.'.join(str(int(part)) for part in match.group(1).split('.'))


def game_key(value):
    normalized = normalize_game_version(value)
    if normalized is None:
        raise ValueError('Invalid game version')
    return tuple(int(part) for part in normalized.split('.'))
