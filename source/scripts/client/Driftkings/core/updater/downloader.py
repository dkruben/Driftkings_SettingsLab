# -*- coding: utf-8 -*-
"""Own staging only; complete size/hash/package validation before READY."""
import hashlib
import json
import os
import stat
import tempfile
import threading
import zipfile
import xml.etree.ElementTree as ET

from Driftkings.core.updater.https_transport import TransferError, CHUNK
from Driftkings.core.updater.manifest import Manifest


def safe_directory(directory):
    directory = os.path.abspath(directory)
    current = directory
    while True:
        if os.path.lexists(current):
            info = os.lstat(current)
            if os.path.islink(current) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise TransferError('stagingError')
            if current == directory and not stat.S_ISDIR(info.st_mode):
                raise TransferError('stagingError')
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    if not os.path.isdir(directory):
        os.makedirs(directory)
    return directory


def validate_package(path, version):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(entries) > 5000 or len(names) != len(set(name.lower() for name in names)) or sum(entry.file_size for entry in entries) > 128 * 1024 * 1024:
            raise TransferError('invalidPackage')
        for entry in entries:
            name = entry.filename
            if (name.startswith('/') or '\\' in name or ':' in name or '..' in name.split('/') or
                    entry.compress_type != zipfile.ZIP_STORED or entry.flag_bits & 1 or
                    stat.S_ISLNK(entry.external_attr >> 16)):
                raise TransferError('invalidPackage')
        if 'meta.xml' not in names or archive.getinfo('meta.xml').file_size > 8192:
            raise TransferError('invalidPackage')
        metadata = archive.read('meta.xml')
        if b'<!DOCTYPE' in metadata or b'<!ENTITY' in metadata:
            raise TransferError('invalidPackage')
        root = ET.fromstring(metadata)
        if root.tag != 'root' or root.findtext('id') != 'driftkings.unified' or root.findtext('version') != version:
            raise TransferError('invalidPackage')
        mods = [name for name in names if name.startswith('res/scripts/client/gui/mods/mod_')]
        if mods != ['res/scripts/client/gui/mods/mod_Driftkings.pyc'] or archive.testzip() is not None:
            raise TransferError('invalidPackage')
        if archive.read(mods[0])[:4] != b'\x03\xf3\x0d\x0a':
            raise TransferError('invalidPackage')


class StagingSink(object):
    def __init__(self, root, manifest):
        self.root = root
        self.manifest = Manifest(manifest.document())
        self.cancelled = threading.Event()
        self.verifying = lambda: None
        self.directory = None
        self.file = None
        self.count = 0
        self.ready = None

    def guard(self):
        if self.cancelled.is_set():
            raise TransferError('cancelled')

    def write(self, data):
        self.guard()
        if self.file is None:
            root = safe_directory(self.root)
            self.directory = tempfile.mkdtemp(prefix='download-', dir=root)
            self.file = open(os.path.join(self.directory, 'Driftkings.wotmod.download'), 'wb')
        if self.count + len(data) > self.manifest.size:
            raise TransferError('sizeMismatch')
        self.file.write(data)
        self.count += len(data)

    def finish(self):
        self.guard()
        self.verifying()
        if self.file is None or self.count != self.manifest.size:
            raise TransferError('sizeMismatch')
        self.file.flush()
        os.fsync(self.file.fileno())
        self.file.close()
        self.file = None
        partial = os.path.join(self.directory, 'Driftkings.wotmod.download')
        if os.path.getsize(partial) != self.manifest.size:
            raise TransferError('sizeMismatch')
        digest = hashlib.sha256()
        with open(partial, 'rb') as source:
            while True:
                self.guard()
                chunk = source.read(CHUNK)
                if not chunk:
                    break
                digest.update(chunk)
        if digest.hexdigest() != self.manifest.sha256:
            raise TransferError('hashMismatch')
        try:
            validate_package(partial, self.manifest.version.text)
        except TransferError:
            raise
        except Exception:
            raise TransferError('invalidPackage')
        self.guard()
        metadata = os.path.join(self.directory, 'release.json')
        with open(metadata, 'wb') as output:
            output.write(json.dumps(self.manifest.document(), ensure_ascii=False).encode('utf-8'))
            output.flush()
            os.fsync(output.fileno())
        self.guard()
        self.ready = os.path.join(self.directory, 'Driftkings.wotmod.ready')
        os.rename(partial, self.ready)
        return self.ready

    def abort(self):
        if self.file is not None:
            self.file.close()
            self.file = None
        if self.directory is not None:
            for name in ('Driftkings.wotmod.download', 'Driftkings.wotmod.ready', 'release.json'):
                path = os.path.join(self.directory, name)
                if os.path.isfile(path):
                    os.remove(path)
            os.rmdir(self.directory)
            self.directory = None
            self.ready = None


class Downloader(object):
    def __init__(self, transport, root, timeout=300.0):
        self.transport, self.root, self.timeout = transport, root, timeout
        self.busy = False
        self.handle = None
        self.sink = None

    def start(self, manifest, callback, progress=None):
        if self.busy:
            return False
        if not isinstance(manifest, Manifest):
            raise ValueError('Validated manifest required')
        sink = StagingSink(self.root, manifest)
        self.busy = True
        self.sink = sink
        def completed(path, error):
            if not self.busy:
                return
            self.busy = False
            self.handle = None
            callback(path, error)
        try:
            handle = self.transport.stream(manifest.download, self.sink, completed,
                                           self.timeout, manifest.size, progress)
            if self.busy:
                self.handle = handle
        except Exception:
            self.sink.abort()
            completed(None, 'networkError')
        return True

    def cancel(self):
        if not self.busy:
            return False
        self.sink.cancelled.set()
        if self.handle is not None:
            self.handle.cancel()
        return True
