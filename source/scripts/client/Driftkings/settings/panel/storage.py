# -*- coding: utf-8 -*-
"""One readable JSON document per mod, atomic replacement and bounded backups."""
import json
import os
import re
import shutil
import tempfile

from Driftkings.settings.store import replace_file as _replace, recover_file as _recover

FILE_PATTERN = re.compile(r'^[A-Za-z0-9_.-]{1,64}$')
MAX_BACKUPS = 3
SECRETS_DIRECTORY = 'secrets'


class ConfigReadError(ValueError):
    """The document exists but cannot be used; it is preserved, never overwritten silently."""


class ConfigStore(object):
    def __init__(self, root, max_backups=MAX_BACKUPS):
        self.root = os.path.abspath(root)
        self.max_backups = max_backups

    def path(self, name, secret=False):
        if not FILE_PATTERN.match(name) or name.startswith('.'):
            raise ValueError('Invalid configuration file name: %r' % (name,))
        folder = os.path.join(self.root, SECRETS_DIRECTORY) if secret else self.root
        return os.path.join(folder, name + '.json')

    def read(self, name, secret=False):
        """Return the stored dictionary, {} when missing; raise ConfigReadError when unusable."""
        path = self.path(name, secret)
        _recover(path)
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, 'rb') as stream:
                raw = stream.read()
            document = json.loads(raw.decode('utf-8-sig')) if raw.strip() else {}
        except (IOError, OSError, ValueError) as error:
            raise ConfigReadError('%s: %s' % (os.path.basename(path), error))
        if not isinstance(document, dict):
            raise ConfigReadError('%s: expected a JSON object' % os.path.basename(path))
        return document

    def write(self, name, document, secret=False):
        path = self.path(name, secret)
        content = json.dumps(document, ensure_ascii=False, indent=4, sort_keys=True, allow_nan=False,
                             separators=(',', ': '))
        if not isinstance(content, bytes):
            content = content.encode('utf-8')
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        descriptor, temporary = tempfile.mkstemp(prefix='.dk-', suffix='.tmp', dir=directory)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            if not secret:
                self.backup(name)
            _replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)

    def backup(self, name):
        """Rotate name.json.bak, .bak.1 ... keeping at most max_backups copies."""
        path = self.path(name)
        if self.max_backups <= 0 or not os.path.isfile(path):
            return None
        names = [path + '.bak'] + ['%s.bak.%d' % (path, index) for index in range(1, self.max_backups)]
        if os.path.exists(names[-1]):
            os.remove(names[-1])
        for index in range(len(names) - 1, 0, -1):
            if os.path.exists(names[index - 1]):
                os.rename(names[index - 1], names[index])
        shutil.copy2(path, names[0])
        return names[0]

    def backups(self, name):
        path = self.path(name)
        candidates = [path + '.bak'] + ['%s.bak.%d' % (path, index) for index in range(1, self.max_backups)]
        return [candidate for candidate in candidates if os.path.isfile(candidate)]
