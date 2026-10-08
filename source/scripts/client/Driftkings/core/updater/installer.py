# -*- coding: utf-8 -*-
"""Internal installer boundary. Scheduling is explicit; no restart or game hooks."""
import hashlib
import json
import os
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET

from Driftkings import VERSION
from Driftkings.core.updater.downloader import safe_directory, validate_package
from Driftkings.core.updater.manifest import Manifest, MAX_MANIFEST, bounded_json
from Driftkings.core.updater.versioning import Version, TEXT, normalize_game_version

HELPER_RESOURCE = 'gui/Driftkings/updater/Driftkings.UpdateInstaller.exe'
INFO_RESOURCE = 'gui/Driftkings/updater/helper.json'
READY = 'Driftkings.wotmod.ready'


def digest(path):
    value = hashlib.sha256()
    with open(path, 'rb') as source:
        for block in iter(lambda: source.read(65536), b''):
            value.update(block)
    return value.hexdigest()


def safe_file(path):
    safe_directory(os.path.dirname(path))
    if not os.path.isfile(path) or os.path.islink(path):
        raise ValueError('Expected owned regular file')
    # Python 2.7 lstat does not expose junctions on all Windows versions.
    # The native helper independently rejects every reparse point before mutation.
    if getattr(os.lstat(path), 'st_file_attributes', 0) & 0x400:
        raise ValueError('Reparse point rejected')
    return path


def read_json(path):
    with open(safe_file(path), 'rb') as source:
        return bounded_json(source.read(MAX_MANIFEST + 1))


def write_new(path, document):
    # Exclusive creation also prevents overwriting a ticket for a live helper.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(json.dumps(document, ensure_ascii=False).encode('utf-8'))
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        os.remove(path)
        raise


def read_resource(name):
    import ResMgr
    section = ResMgr.openSection(name)
    if section is None:
        raise ValueError('Installer resource unavailable')
    return section.asBinary


class Installer(object):
    """Owned by UpdaterService, never an independent service.

    The caller must provide a fail-closed context predicate.
    """
    def __init__(self, game_root, resource_reader=None, launcher=None):
        self.root = os.path.abspath(game_root)
        self.cache = os.path.join(self.root, 'mods', 'configs', 'Driftkings', 'cache', 'update')
        self.resource_reader = resource_reader or read_resource
        self.launcher = launcher or subprocess.Popen
        self.process = None

    def validate_stage(self, ready, client_version, channel, installed=VERSION):
        ready = os.path.abspath(ready)
        folder = os.path.dirname(ready)
        if (os.path.basename(ready) != READY or os.path.dirname(folder) != self.cache or
                not os.path.basename(folder).startswith('download-')):
            raise ValueError('Stage outside owned cache')
        safe_file(ready)
        manifest = Manifest(read_json(os.path.join(folder, 'release.json')))
        if (not manifest.compatible(client_version) or not manifest.version.allowed(channel) or
                manifest.version <= Version(installed)):
            raise ValueError('Incompatible update or downgrade')
        if os.path.getsize(ready) != manifest.size or digest(ready) != manifest.sha256:
            raise ValueError('Stage size/hash mismatch')
        validate_package(ready, manifest.version.text)
        return manifest

    def recover_ready(self, client_version, channel, installed=VERSION):
        """Read-only bounded discovery; interrupted downloads/configs are untouched."""
        if not os.path.isdir(self.cache):
            return None
        safe_directory(self.cache)
        candidates = []
        for name in sorted(os.listdir(self.cache))[:100]:
            if not name.startswith('download-'):
                continue
            ready = os.path.join(self.cache, name, READY)
            try:
                result = os.path.join(self.cache, name, 'result.json')
                if os.path.isfile(result) and read_json(result).get('status') == 'installed':
                    continue
                manifest = self.validate_stage(ready, client_version, channel, installed)
                candidates.append((manifest.version, ready))
            except (ValueError, IOError, OSError, zipfile.BadZipfile, ET.ParseError):
                continue
        return max(candidates, key=lambda item: item[0])[1] if candidates else None

    def schedule(self, ready, client_version, channel, context_safe, installed=VERSION):
        """Arm local helper; acknowledgement/result are read separately by the caller.

        This does not mean installation succeeded. The helper opens the parent
        process handle and acknowledges before waiting for that process to exit.
        """
        if self.process is not None and self.process.poll() is None:
            return False
        if not callable(context_safe) or context_safe() is not True:
            return False
        manifest = self.validate_stage(ready, client_version, channel, installed)
        game_version = normalize_game_version(client_version)
        target = os.path.join(self.root, 'mods', game_version, 'Driftkings.wotmod')
        safe_file(target)
        validate_package(target, installed)
        if os.path.lexists(target + '.old') or os.path.lexists(target + '.new'):
            raise ValueError('Unresolved installation requires recovery')
        folder = os.path.dirname(os.path.abspath(ready))
        ticket_path = os.path.join(folder, 'install.json')
        if os.path.lexists(ticket_path):
            raise ValueError('Existing installation ticket requires recovery')
        binary = self.resource_reader(HELPER_RESOURCE)
        info = bounded_json(self.resource_reader(INFO_RESOURCE))
        if (not isinstance(info, dict) or set(info) != set(('schema', 'size', 'sha256')) or info['schema'] != 1 or
                len(binary) > 4 * 1024 * 1024 or
                len(binary) != info['size'] or hashlib.sha256(binary).hexdigest() != info['sha256'] or
                binary[:2] != b'MZ'):
            raise ValueError('Local installer resource mismatch')
        helper = os.path.join(folder, 'Driftkings.UpdateInstaller.exe')
        ticket = dict(schema=1, gameVersion=game_version, version=manifest.version.text,
                      size=manifest.size, sha256=manifest.sha256, installedVersion=installed,
                      installedSize=os.path.getsize(target), installedSha256=digest(target))
        helper_created = False
        ticket_created = False
        try:
            descriptor = os.open(helper, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            helper_created = True
            with os.fdopen(descriptor, 'wb') as output:
                output.write(binary)
                output.flush()
                os.fsync(output.fileno())
            # Recheck safety after validation and IO, immediately before launch.
            if context_safe() is not True:
                os.remove(helper)
                return False
            marker = os.path.join(folder, 'cancel.install')
            if os.path.lexists(marker):
                os.remove(safe_file(marker))
            write_new(ticket_path, ticket)
            ticket_created = True
            self.process = self.launcher([helper, folder, str(os.getpid())], shell=False,
                                         creationflags=0x08000000, close_fds=False)
        except Exception:
            if ticket_created:
                os.remove(ticket_path)
            if helper_created:
                os.remove(helper)
            raise
        return True

    def resume(self, ready, client_version, channel, context_safe, installed=VERSION):
        """Re-arm an interrupted local transaction without rewriting its provenance.

        Native validation/recovery remains authoritative. No obsolete ticket or
        cached executable can choose a different destination or a command.
        """
        if self.process is not None and self.process.poll() is None:
            return False
        if not callable(context_safe) or context_safe() is not True:
            return False
        manifest = self.validate_stage(ready, client_version, channel, installed)
        folder = os.path.dirname(os.path.abspath(ready))
        ticket = read_json(os.path.join(folder, 'install.json'))
        keys = ('schema', 'gameVersion', 'version', 'size', 'sha256', 'installedVersion',
                'installedSize', 'installedSha256')
        if (not isinstance(ticket, dict) or set(ticket) != set(keys) or type(ticket['schema']) is not int or ticket['schema'] != 1 or
                ticket['gameVersion'] != normalize_game_version(client_version) or
                ticket['version'] != manifest.version.text or ticket['size'] != manifest.size or
                ticket['sha256'] != manifest.sha256 or ticket['installedVersion'] != installed or
                not isinstance(ticket['installedSize'], int) or isinstance(ticket['installedSize'], bool) or
                not 0 < ticket['installedSize'] <= 64 * 1024 * 1024 or
                not isinstance(ticket['installedSha256'], TEXT) or
                re.match(r'\A[0-9a-f]{64}\Z', ticket['installedSha256']) is None):
            raise ValueError('Interrupted transaction does not match current update')
        helper = safe_file(os.path.join(folder, 'Driftkings.UpdateInstaller.exe'))
        info = bounded_json(self.resource_reader(INFO_RESOURCE))
        if (not isinstance(info, dict) or set(info) != set(('schema', 'size', 'sha256')) or info['schema'] != 1 or
                os.path.getsize(helper) > 4 * 1024 * 1024 or
                os.path.getsize(helper) != info['size'] or digest(helper) != info['sha256']):
            raise ValueError('Interrupted local helper mismatch')
        if context_safe() is not True:
            return False
        marker = os.path.join(folder, 'cancel.install')
        if os.path.lexists(marker):
            os.remove(safe_file(marker))
        self.process = self.launcher([helper, folder, str(os.getpid())], shell=False,
                                     creationflags=0x08000000, close_fds=False)
        return True

    @staticmethod
    def cancel(ready):
        """Fixed owned marker; the native helper observes it before mutation."""
        if ready is not None:
            path = os.path.join(os.path.dirname(os.path.abspath(ready)), 'cancel.install')
            safe_directory(os.path.dirname(path))
            if not os.path.lexists(path):
                write_new(path, dict(schema=1))

    @staticmethod
    def result(ready):
        """Missing result means preparation is still pending, never success."""
        path = os.path.join(os.path.dirname(ready), 'result.json')
        return read_json(path) if os.path.isfile(path) else None
