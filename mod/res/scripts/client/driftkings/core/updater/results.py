# -*- coding: utf-8 -*-
"""Bounded local receipts, separate from Installer and profile persistence."""
import hashlib
import json
import os
import re
import time

from driftkings import VERSION
from driftkings.core.updater.installer import digest, read_json, validate_package, write_new
from driftkings.core.updater.manifest import INTEGER, Manifest
from driftkings.core.updater.versioning import normalize_game_version, TEXT, Version
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Updater')
FINAL_STATUSES = frozenset(('installed', 'rolledBack', 'rolled_back', 'cancelled', 'error', 'failed'))
# Interrupted downloads are kept this long in case the same session is still writing them.
ABANDONED_SECONDS = 24 * 60 * 60
TICKET_KEYS = frozenset(('schema', 'gameVersion', 'version', 'size', 'sha256', 'installedVersion', 'installedSize', 'installedSha256'))


def fingerprint(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, ensure_ascii=True).encode('ascii')).hexdigest()


def safe_path(path):
    """No creation; reject Windows junctions even under Python 2.7."""
    current = os.path.abspath(path)
    native_check = False
    while True:
        if os.path.lexists(current):
            info = os.lstat(current)
            if os.path.islink(current) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Receipt reparse path rejected')
            if os.name == 'nt' and not hasattr(info, 'st_file_attributes'):
                native_check = True
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    if native_check:
        from driftkings.core.updater.windows_files import safe_path as windows_safe_path
        windows_safe_path(path)
    return path


def remove_flat_directory(path):
    """Delete one owned cache folder holding only regular files; nested directories are refused."""
    safe_path(path)
    entries = [os.path.join(path, name) for name in os.listdir(path)]
    if any(os.path.isdir(entry) or not os.path.isfile(entry) for entry in entries):
        raise ValueError('Unexpected entry in owned cache folder')
    for entry in entries:
        os.remove(entry)
    os.rmdir(path)


class Results(object):
    def __init__(self, game_root, loaded_version=VERSION):
        self.root = os.path.abspath(game_root)
        self.cache = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'cache', 'update')
        self.loaded_version = loaded_version

    def proof_signature(self, ready):
        """Cheap change guard for a background-validated receipt, not validation."""
        from driftkings.core.updater.installer import file_signature
        ready = os.path.abspath(ready)
        folder = os.path.dirname(ready)
        if (os.path.basename(ready) != 'driftkings.wotmod.ready' or os.path.dirname(folder) != self.cache or
                not os.path.basename(folder).startswith('download-')):
            raise ValueError('Unknown operation path')
        return file_signature([ready] + [os.path.join(folder, name) for name in
                              ('result.json', 'install.json', 'release.json', 'Driftkings.UpdateInstaller.exe', 'restart.install')])

    def _folder(self, ready):
        ready = os.path.abspath(ready)
        folder = os.path.dirname(ready)
        if (os.path.basename(ready) != 'driftkings.wotmod.ready' or os.path.dirname(folder) != self.cache or
                not os.path.basename(folder).startswith('download-')):
            raise ValueError('Unknown operation path')
        safe_path(folder)
        return folder

    def result_stamp(self, ready):
        """Freshness evidence for a reused ticket/PID; captured before launch."""
        folder = self._folder(ready)
        path = safe_path(os.path.join(folder, 'result.json'))
        if not os.path.isfile(path):
            return None
        value = read_json(path)
        info = os.stat(path)
        return (fingerprint(value), info.st_mtime, info.st_ctime, info.st_size, info.st_ino)

    def ticket(self, ready):
        folder = self._folder(ready)
        ticket = read_json(safe_path(os.path.join(folder, 'install.json')))
        manifest = Manifest(read_json(safe_path(os.path.join(folder, 'release.json'))))
        if manifest.inventory is not None:
            from driftkings.core.updater.modpack_transaction import validate_ticket
            return validate_ticket(ticket, manifest)
        if (not isinstance(ticket, dict) or set(ticket) != TICKET_KEYS or
                type(ticket['schema']) not in INTEGER or ticket['schema'] != 1 or
                normalize_game_version(ticket['gameVersion']) != ticket['gameVersion'] or
                not manifest.compatible(ticket['gameVersion']) or ticket['version'] != manifest.version.text or
                ticket['size'] != manifest.size or ticket['sha256'] != manifest.sha256 or
                Version(ticket['installedVersion']) >= manifest.version):
            raise ValueError('Invalid local ticket')
        for key in ('size', 'installedSize'):
            if type(ticket[key]) not in INTEGER or not 0 < ticket[key] <= 64 * 1024 * 1024:
                raise ValueError('Invalid ticket size')
        for key in ('sha256', 'installedSha256'):
            if not isinstance(ticket[key], TEXT) or re.match(r'\A[0-9a-f]{64}\Z', ticket[key]) is None:
                raise ValueError('Invalid ticket hash')
        return ticket

    def _package_matches(self, ticket, old=False):
        if ticket['schema'] == 2:
            from driftkings.core.updater.modpack_transaction import verify_result
            return verify_result(self.root, ticket, self.loaded_version, old)
        path = os.path.join(self.root, 'mods', ticket['gameVersion'], 'driftkings.wotmod')
        safe_path(path)
        size = ticket['installedSize'] if old else ticket['size']
        sha = ticket['installedSha256'] if old else ticket['sha256']
        version = ticket['installedVersion'] if old else ticket['version']
        if not os.path.isfile(path) or os.path.getsize(path) != size or digest(path) != sha:
            raise ValueError('Installed package missing or hash differs')
        validate_package(path, version)
        if self.loaded_version != version:
            raise ValueError('Loaded VERSION differs from transaction result')
        backup = path + '.old'
        if os.path.lexists(backup):
            safe_path(backup)
            if not os.path.isfile(backup) or os.path.getsize(backup) != ticket['installedSize'] or digest(backup) != ticket['installedSha256']:
                raise ValueError('Ambiguous backup')
        if os.path.lexists(path + '.new'):
            raise ValueError('Unresolved temporary package')

    def _superseded(self, version):
        """A release older than the loaded one can no longer be resumed or proven."""
        try:
            return Version(version) < Version(self.loaded_version)
        except Exception:
            return False

    def _result_time(self, name):
        try:
            return os.path.getmtime(os.path.join(self.cache, name, 'result.json'))
        except (IOError, OSError):
            return 0

    def scan(self, client_version):
        if not os.path.isdir(self.cache):
            return []
        safe_path(self.cache)
        reports = []
        # Folder names are random; order by result time so reports[-1] is the latest outcome.
        names = sorted((name for name in os.listdir(self.cache) if name.startswith('download-')),
                       key=self._result_time, reverse=True)[:100]
        for name in reversed(names):
            folder = os.path.join(self.cache, name)
            if not os.path.isfile(os.path.join(folder, 'result.json')):
                continue
            ready = os.path.join(folder, 'driftkings.wotmod.ready')
            try:
                self._folder(ready)
                missing = [filename for filename in ('install.json', 'release.json')
                           if not os.path.lexists(safe_path(os.path.join(folder, filename)))]
                if missing:
                    LOG.warning('Ignoring incomplete update result in %s: missing %s',
                                name, ', '.join(missing))
                    continue
                ticket = self.ticket(ready)
                if ticket['gameVersion'] != normalize_game_version(client_version):
                    continue
                if self._superseded(ticket['version']):
                    continue
            except Exception:
                LOG.warning('Ignoring result with unknown or invalid local ticket', exc_info=True)
                continue
            status, error = 'failed', 'invalidResult'
            result = None
            try:
                result = read_json(safe_path(os.path.join(folder, 'result.json')))
                if (not isinstance(result, dict) or set(result) != set(('schema', 'status', 'error', 'helperPid')) or
                        type(result['schema']) not in INTEGER or result['schema'] != 1 or
                        type(result['helperPid']) not in INTEGER or result['helperPid'] <= 0 or
                        result['error'] is not None and (not isinstance(result['error'], TEXT) or len(result['error']) > 256)):
                    raise ValueError('Invalid result schema')
                status = {'installed': 'installed', 'rolledBack': 'rolled_back', 'rolled_back': 'rolled_back',
                          'cancelled': 'cancelled', 'error': 'failed', 'failed': 'failed'}.get(result['status'])
                if status is None:
                    # prepared/installing never imply success in a new process.
                    status, error = 'failed', 'incompletePreviousInstall'
                else:
                    error = result['error']
                    if status in ('installed', 'rolled_back', 'cancelled'):
                        self._package_matches(ticket, old=status != 'installed')
            except Exception:
                status, error = 'failed', 'invalidResult'
                LOG.warning('Previous update result could not be verified', exc_info=True)
            identity = fingerprint(dict(ticket=ticket, result=result, status=status, error=error))
            receipt = os.path.join(folder, 'notified.json')
            try:
                if os.path.isfile(receipt) and read_json(safe_path(receipt)) == dict(schema=1, fingerprint=identity):
                    continue
            except Exception:
                LOG.warning('Previous notification receipt invalid')
            reports.append(dict(status=status, version=ticket['version'], error=error, ready=ready, fingerprint=identity))
        return reports

    def _stage_version(self, folder):
        """Release version of a removable stage, or None while it may still be needed."""
        result_path = os.path.join(folder, 'result.json')
        if os.path.lexists(os.path.join(folder, 'install.json')):
            # An armed transaction is only removable once the helper reported a final status.
            if not os.path.isfile(result_path):
                return None
            result = read_json(safe_path(result_path))
            if not isinstance(result, dict) or result.get('status') not in FINAL_STATUSES:
                return None
        release_path = os.path.join(folder, 'release.json')
        if not os.path.isfile(release_path):
            return None
        release = read_json(safe_path(release_path))
        version = release.get('version') if isinstance(release, dict) else None
        return version if isinstance(version, TEXT) else None

    def _abandoned(self, folder, now):
        """A folder without ticket or release: a reported outcome or an old interrupted download."""
        if os.path.lexists(os.path.join(folder, 'install.json')) or os.path.lexists(os.path.join(folder, 'release.json')):
            return False
        result_path = os.path.join(folder, 'result.json')
        if os.path.isfile(result_path):
            # scan() can never report it again and nothing is left to resume.
            result = read_json(safe_path(result_path))
            return isinstance(result, dict) and result.get('status') in FINAL_STATUSES
        # No result yet: only a download untouched for a day, never one in progress.
        stamps = [os.path.getmtime(os.path.join(folder, name)) for name in os.listdir(folder)]
        return max(stamps + [os.path.getmtime(folder)]) < now - ABANDONED_SECONDS

    def prune(self):
        """Remove stage folders of releases older than the loaded one, including their backups,
        and abandoned folders that can no longer be resumed or reported."""
        if not os.path.isdir(self.cache):
            return 0
        safe_path(self.cache)
        removed = 0
        now = time.time()
        for name in sorted(os.listdir(self.cache)):
            folder = os.path.join(self.cache, name)
            if not name.startswith('download-') or not os.path.isdir(folder):
                continue
            try:
                version = self._stage_version(folder)
                if version is None:
                    if not self._abandoned(folder, now):
                        continue
                elif not self._superseded(version):
                    continue
                remove_flat_directory(folder)
                removed += 1
            except Exception:
                LOG.warning('Could not remove superseded update folder %s', name, exc_info=True)
        return removed

    def acknowledge(self, report):
        """Controlled cleanup: one receipt; retain ticket/result/backups for diagnosis."""
        folder = os.path.dirname(report['ready'])
        # Revalidate ownership immediately before creating the cache receipt.
        self.ticket(report['ready'])
        receipt = safe_path(os.path.join(folder, 'notified.json'))
        if not os.path.lexists(receipt):
            write_new(receipt, dict(schema=1, fingerprint=report['fingerprint']))
        else:
            # This is a new result for the same resumed transaction. Only our
            # notification metadata is replaced; ticket/result remain untouched.
            import tempfile
            descriptor, temporary = tempfile.mkstemp(prefix='notice-', dir=folder)
            try:
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(json.dumps(dict(schema=1, fingerprint=report['fingerprint'])).encode('ascii'))
                    output.flush()
                    os.fsync(output.fileno())
                safe_path(receipt)
                if os.name == 'nt':
                    from driftkings.core.updater.windows_files import replace_receipt
                    replace_receipt(temporary, receipt)
                else:
                    os.rename(temporary, receipt)
            finally:
                if os.path.isfile(temporary):
                    os.remove(temporary)
        # No package, backup, executable or configuration is deleted here.
