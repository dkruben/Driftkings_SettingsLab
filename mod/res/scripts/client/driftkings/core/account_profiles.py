# -*- coding: utf-8 -*-
"""Account profiles without secrets: a title, an e-mail and a server. Passwords are typed on the login screen.

The profiles file is separate from the legacy `accounts.manager`, which is never opened, read, copied or
replaced by this module. Nothing here decrypts, compresses or encodes credentials.
"""
import copy
import json
import os
import uuid

from driftkings.common.utils.filesystem import atomicWrite
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.AccountManager')

FILE_NAME = 'accounts_profiles.json'
LEGACY_NAME = 'accounts.manager'
# Any key in this set is a secret or a secret-like value. Such a record is refused, never stored.
FORBIDDEN_KEYS = frozenset(('password', 'passwd', 'pwd', 'token', 'cookie', 'cookies', 'session', 'secret',
                            'credential', 'credentials', 'key', 'privatekey'))
ALLOWED_KEYS = frozenset(('id', 'title', 'email', 'cluster', 'server', 'serverName', 'realm'))
MAX_TITLE = 60
MAX_EMAIL = 254


class ProfileFileError(ValueError):
    """The profiles file exists but cannot be used safely; it is preserved untouched."""


def valid_record(record):
    """Returns True when a record holds only the allowed, non-secret fields with the expected types."""
    if not isinstance(record, dict):
        return False
    keys = set(record)
    if keys & FORBIDDEN_KEYS or keys - ALLOWED_KEYS:
        return False
    if not (isinstance(record.get('id'), (str, type(u''))) and record.get('id')):
        return False
    if not (isinstance(record.get('title'), (str, type(u''))) and 0 < len(record.get('title').strip()) <= MAX_TITLE):
        return False
    email = record.get('email')
    if not (isinstance(email, (str, type(u''))) and '@' in email and 0 < len(email) <= MAX_EMAIL):
        return False
    cluster = record.get('cluster')
    if type(cluster) is not int or cluster < -1:
        return False
    for optional in ('server', 'serverName', 'realm'):
        if optional in record and not isinstance(record[optional], (str, type(u''))):
            return False
    return True


def parse(raw):
    """Strict JSON: a list of valid records with unique identifiers. Any deviation raises ProfileFileError."""
    try:
        records = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        raise ProfileFileError('not valid UTF-8 JSON')
    if not isinstance(records, list) or not all(valid_record(item) for item in records):
        raise ProfileFileError('invalid profile records')
    identifiers = [str(item['id']) for item in records]
    if len(set(identifiers)) != len(identifiers):
        raise ProfileFileError('duplicate identifiers')
    return records


class ProfileFile(object):
    """Loads and saves the profiles file. A corrupt file blocks writes so it is never overwritten."""

    def __init__(self, path, legacy_path=None):
        self.path = path
        self.legacy_path = legacy_path
        self.accounts = []
        self.read_error = False
        if os.path.isfile(path):
            self.load()

    @property
    def legacy_present(self):
        # Only the existence is checked. The legacy content is never read.
        return bool(self.legacy_path) and os.path.isfile(self.legacy_path)

    def load(self):
        try:
            with open(self.path, 'rb') as stream:
                raw = stream.read()
            self.accounts = [] if not raw.strip() else parse(raw)
            self.read_error = False
        except (IOError, OSError, ProfileFileError) as error:
            self.accounts = []
            self.read_error = True
            # Type name only: the file can contain e-mail addresses.
            LOG.error('Could not read account profiles (%s); existing file preserved', type(error).__name__)

    def write_accounts(self):
        if self.read_error:
            return False
        try:
            records = [copy.deepcopy(item) for item in self.accounts]
            if not all(valid_record(item) for item in records):
                raise ProfileFileError('refusing to save an invalid record')
            directory = os.path.dirname(self.path)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            data = json.dumps(records, indent=2, sort_keys=True).encode('utf-8')
            atomicWrite(self.path, data)
            return True
        except Exception as error:
            LOG.error('Could not save account profiles (%s); no secrets are stored', type(error).__name__)
            return False


def new_identifier():
    return uuid.uuid4().hex
