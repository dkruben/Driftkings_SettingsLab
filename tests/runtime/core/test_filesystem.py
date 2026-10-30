# -*- coding: utf-8 -*-
"""Shared file publication preserves existing documents after failure."""
import hashlib
import os
import shutil
import tempfile
from support import RuntimeTest, module, source


class FilesystemTests(RuntimeTest):
    def setUp(self):
        super(FilesystemTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.api = self.load('common.utils.filesystem')

    def test_atomic_write_and_streaming_hash(self):
        target = os.path.join(self.root, 'data.json')
        payload = b'abc' * 70000
        self.api.atomicWrite(target, payload)
        self.assertEqual(self.api.file_sha256(target), hashlib.sha256(payload).hexdigest())
        self.api.atomicWrite(target, b'new')
        with open(target, 'rb') as stream:
            self.assertEqual(stream.read(), b'new')
        self.assertEqual(os.listdir(self.root), ['data.json'])

    def test_windows_fallback_restores_original_when_publish_fails(self):
        target = os.path.join(self.root, 'data.json')
        with open(target, 'wb') as stream:
            stream.write(b'original')
        class WindowsOS(object):
            name = 'nt'
            replace = None
            def __getattr__(self, name):
                return getattr(os, name)
            def rename(self, source, destination):
                if os.path.basename(source).startswith('.driftkings-'):
                    raise OSError('simulated publish failure')
                return os.rename(source, destination)
        self.api.os = WindowsOS()
        self.addCleanup(setattr, self.api, 'os', os)
        with self.assertRaises(OSError):
            self.api.atomicWrite(target, b'replacement')
        with open(target, 'rb') as stream:
            self.assertEqual(stream.read(), b'original')
        self.assertEqual(os.listdir(self.root), ['data.json'])

    def test_recovery_and_store_compatibility(self):
        target = os.path.join(self.root, 'data.json')
        with open(target + '.previous', 'wb') as stream:
            stream.write(b'{"enabled": false}')
        store = source('settings/store.py', {'driftkings.common.utils.filesystem': self.api})
        self.assertIs(store['replace_file'], self.api.replace_file)
        self.assertIs(store['recover_file'], self.api.recover_file)
        self.api.recoverFile(target)
        with open(target, 'rb') as stream:
            self.assertEqual(stream.read(), b'{"enabled": false}')
        self.assertFalse(os.path.exists(target + '.previous'))
