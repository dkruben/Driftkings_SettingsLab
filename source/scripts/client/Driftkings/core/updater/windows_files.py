# -*- coding: utf-8 -*-
"""Owned bounded Win32 IPC, compatible with Python 2.7 without _ctypes."""
import atexit
import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
try:
    import Queue as queue
except ImportError:
    import queue
try:
    TEXT = unicode
except NameError:
    TEXT = str

HELPER_RESOURCE = 'gui/Driftkings/windows-files/Driftkings.WindowsFiles.exe'
INFO_RESOURCE = 'gui/Driftkings/windows-files/helper.json'
_client = None
_configuration_lock = threading.RLock()


def encoded_path(path):
    if not isinstance(path, TEXT):
        path = path.decode('mbcs') if isinstance(path, bytes) else None
    if path is None or len(path) >= 4096: raise OSError('Invalid Windows path')
    try: return base64.b64encode(path.encode('utf-8'))
    except (UnicodeError, ValueError): raise OSError('Invalid Windows path encoding')


class WindowsPathValidator(object):
    """One owned process, serialized requests, blocking pipe reader, no polling."""
    def __init__(self, binary, root, sha256):
        self.binary, self.root, self.sha256 = binary, root, sha256
        self.process = None
        self.responses = queue.Queue()
        self.lock = threading.RLock()
        self.failed = False

    def identity(self):
        if not os.path.isfile(self.binary): raise OSError('Windows helper absent')
        with open(self.binary, 'rb') as stream:
            if hashlib.sha256(stream.read()).hexdigest() != self.sha256: raise OSError('Windows helper hash mismatch')

    def response(self):
        try: line = self.responses.get(timeout=10)
        except queue.Empty:
            self.failed = True
            if self.process is not None and self.process.poll() is None: self.process.kill()
            raise OSError('Windows helper response timeout')
        if not line:
            self.failed = True
            raise OSError('Windows helper terminated without response')
        return line.rstrip(b'\r\n')

    def start(self):
        self.identity()
        if self.failed: raise OSError('Windows helper session failed; no retry')
        if self.process is not None:
            if self.process.poll() is not None:
                self.failed = True
                raise OSError('Windows helper exited; no retry')
            return
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        self.process = subprocess.Popen([self.binary, '--serve', self.root, str(os.getpid()), self.sha256],
                                        shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, startupinfo=startup, creationflags=0x08000000)
        def reading():
            try:
                while True:
                    line = self.process.stdout.readline(32770)
                    self.responses.put(line)
                    if not line: break
            except Exception: self.responses.put(b'')
        thread = threading.Thread(target=reading, name='Driftkings.WindowsFiles.pipe')
        thread.daemon = True
        thread.start()
        if self.response() != b'READY\t1':
            self.failed = True
            raise OSError('Windows helper handshake rejected')

    def request(self, operation, *paths):
        with self.lock:
            self.start()
            message = b'\t'.join([operation.encode('ascii')] + [encoded_path(path) for path in paths]) + b'\n'
            if len(message) > 32768: raise OSError('Windows helper request exceeds bound')
            try:
                self.process.stdin.write(message)
                self.process.stdin.flush()
            except Exception:
                self.failed = True
                raise OSError('Windows helper pipe failed')
            result = self.response()
            if result == b'OK\t' + operation.encode('ascii'): return
            fields = result.split(b'\t')
            if len(fields) == 3 and fields[0] == b'ERR':
                try:
                    code = int(fields[1]); message = base64.b64decode(fields[2]).decode('utf-8')
                except Exception:
                    self.failed = True
                    raise OSError('Invalid Windows helper error response')
                error = OSError(code, message)
                error.winerror = code
                raise error
            self.failed = True
            raise OSError('Unexpected Windows helper response')

    def close(self):
        with self.lock:
            if self.process is not None:
                try: self.process.stdin.close()
                except Exception: pass
                def stop_owned_process():
                    try:
                        if self.process.poll() is None: self.process.kill()
                    except Exception: pass
                timer = threading.Timer(3, stop_owned_process)
                timer.daemon = True
                timer.start()
                try: self.process.wait()
                except Exception: pass
                finally: timer.cancel()
                for stream in (self.process.stdout, self.process.stderr):
                    try: stream.close()
                    except Exception: pass
            self.failed = True


def initialize(resource_reader, root, cache_root=None):
    """Client-thread resource snapshot/bootstrap; workers never access ResMgr."""
    global _client
    with _configuration_lock:
        if _client is not None and not _client.failed and _client.root == os.path.abspath(root): return
        binary = resource_reader(HELPER_RESOURCE)
        raw_metadata = resource_reader(INFO_RESOURCE)
        if not isinstance(raw_metadata, bytes) or len(raw_metadata) > 4096:
            raise OSError('Invalid Windows helper metadata resource')
        metadata = json.loads(raw_metadata.decode('utf-8'))
        if (not isinstance(binary, bytes) or not 0 < len(binary) <= 256 * 1024 or
                not isinstance(metadata, dict) or set(metadata) != set(('schema', 'size', 'sha256')) or
                type(metadata['schema']) is not int or metadata['schema'] != 1 or
                type(metadata['size']) is not int or metadata['size'] != len(binary) or
                not isinstance(metadata['sha256'], (TEXT, str)) or
                re.match(r'\A[0-9a-f]{64}\Z', metadata['sha256']) is None or
                hashlib.sha256(binary).hexdigest() != metadata['sha256']):
            raise OSError('Windows helper resource identity mismatch')
        root = os.path.abspath(root)
        cache = os.path.abspath(cache_root or os.path.join(root, 'mods/configs/Driftkings/cache/windows-files'))
        if cache != root and not os.path.normcase(cache).startswith(os.path.normcase(root + os.sep)):
            raise OSError('Windows helper cache escapes owned root')
        if not os.path.isdir(cache): os.makedirs(cache)
        directory = tempfile.mkdtemp(prefix='wf-', dir=cache)
        path = os.path.join(directory, 'Driftkings.WindowsFiles.exe')
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(binary); stream.flush(); os.fsync(stream.fileno())
        client = WindowsPathValidator(path, root, metadata['sha256'])
        client.identity()
        if _client is not None: _client.close()
        _client = client


def close():
    global _client
    with _configuration_lock:
        if _client is not None:
            _client.close(); _client = None


def safe_path(path):
    if _client is None: raise OSError('Windows validator not initialized')
    _client.request('V', path)


def replace_receipt(source, destination):
    if _client is None: raise OSError('Windows validator not initialized')
    _client.request('R', source, destination)


atexit.register(close)
