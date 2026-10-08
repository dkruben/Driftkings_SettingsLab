# -*- coding: utf-8 -*-
"""These metadata contract tests run unchanged on Python 2.7.18 and Python 3."""
import json
import hashlib
import io
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../source/scripts/client')))
from Driftkings import VERSION
from Driftkings.core.updater import UpdaterService
from Driftkings.core.updater.checker import Checker
from Driftkings.core.updater.endpoints import RELEASES, REPOSITORY
from Driftkings.core.updater.manifest import Manifest
from Driftkings.core.updater.versioning import Version
from Driftkings.core.updater.transport import Response
from Driftkings.core.updater.state import State
from Driftkings.core.updater.downloader import Downloader
from Driftkings.core.updater.https_transport import HttpsTransport, verified_opener, http
from Driftkings.core.updater.installer import Installer, write_new, digest, read_json
from Driftkings.core.updater.context import InstallContext
from Driftkings.core.updater.results import Results


class UpdaterSmokeTests(unittest.TestCase):
    def test_post_restart_receipt_python27_windows_paths_and_deduplication(self):
        import shutil
        fixtures = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../build/updater-tests'))
        if not os.path.isdir(fixtures): os.makedirs(fixtures)
        root = tempfile.mkdtemp(dir=fixtures)
        try:
            stage = os.path.join(root, 'mods', 'configs', 'Driftkings', 'cache', 'update', 'download-receipt')
            os.makedirs(stage)
            def data(version):
                output = io.BytesIO()
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
                    archive.writestr('meta.xml', '<root><id>driftkings.unified</id><version>%s</version></root>' % version)
                    archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc', b'\x03\xf3\x0d\x0a' + b'\0' * 20)
                return output.getvalue()
            old, new = data('0.1.0'), data('1.0.0')
            meta = Manifest(dict(schema=1, version='1.0.0', channel='stable', gameVersion='2.4.0.2',
                file='Driftkings.wotmod', size=len(new), sha256=hashlib.sha256(new).hexdigest(),
                download='https://github.com/' + REPOSITORY + '/releases/download/v1.0.0/Driftkings.wotmod'))
            ticket = dict(schema=1, gameVersion='2.4.0.2', version='1.0.0', size=len(new), sha256=meta.sha256,
                installedVersion='0.1.0', installedSize=len(old), installedSha256=hashlib.sha256(old).hexdigest())
            write_new(os.path.join(stage, 'install.json'), ticket)
            write_new(os.path.join(stage, 'release.json'), meta.document())
            result_path = os.path.join(stage, 'result.json')
            write_new(result_path, dict(schema=1, status='installed', helperPid=123, error=None))
            target = os.path.join(root, 'mods', '2.4.0.2', 'Driftkings.wotmod')
            os.makedirs(os.path.dirname(target))
            with open(target, 'wb') as output: output.write(new)
            reader = Results(root, loaded_version='1.0.0')
            report = reader.scan('2.4.0.2')[0]
            self.assertEqual(report['status'], 'installed')
            reader.acknowledge(report)
            self.assertEqual(reader.scan('2.4.0.2'), [])
            os.remove(result_path)
            write_new(result_path, dict(schema=1, status='failed', helperPid=456, error='installIOError'))
            report = reader.scan('2.4.0.2')[0]
            reader.acknowledge(report)
            self.assertEqual(reader.scan('2.4.0.2'), [])
        finally:
            shutil.rmtree(root)

    def test_context_policy_python27_replay_and_loading_fail_closed(self):
        class Client(object):
            inited = spaceInited = isModelLoaded = True
            def getSpaceID(self): return 3
            def player(self): return self
            def current_mode(self): return 'hangar'
            def is_in_battle(self): return False
            def isPlaying(self): return False
            def isLoading(self): return False
        client = Client()
        policy = InstallContext(3, client, client, client, client)
        self.assertIsNone(policy.blocked_reason(3))
        client.isLoading = lambda: True
        self.assertEqual(policy.blocked_reason(3), 'replayContext')
        self.assertEqual(policy.blocked_reason(None), 'unsafeContext')

    def test_installer_python27_local_ticket_and_fail_closed_context(self):
        fixtures = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../build/updater-tests'))
        if not os.path.isdir(fixtures):
            os.makedirs(fixtures)
        root = tempfile.mkdtemp(dir=fixtures)
        path = os.path.join(root, 'install.json')
        try:
            write_new(path, dict(schema=1, version=u'1.0.0'))
            self.assertEqual(read_json(path)['version'], '1.0.0')
            with open(path, 'rb') as source:
                self.assertEqual(digest(path), hashlib.sha256(source.read()).hexdigest())
            with self.assertRaises(OSError):
                write_new(path, {})
            installer = Installer(root)
            self.assertFalse(installer.schedule('not-a-stage', '2.4.0.2', 'stable', lambda: None))
            self.assertIsNone(installer.recover_ready(None, 'stable'))
        finally:
            os.remove(path)
            os.rmdir(root)

    def test_semver_and_unicode_manifest(self):
        self.assertGreater(Version('1.0.0-beta.10'), Version('1.0.0-beta.2'))
        self.assertLess(Version('1.0.0-rc.1'), Version('1.0.0'))
        self.assertEqual(Version('1.0.0+build'), Version('1.0.0'))
        manifest = Manifest.parse(json.dumps(dict(schema=1, version='1.0.0', channel='stable',
            gameVersion='2.4.0.2', file='Driftkings.wotmod', size=123, sha256='a' * 64,
            download='https://github.com/' + REPOSITORY + '/releases/download/v1/Driftkings.wotmod',
            changelog=[u'Atualiza\u00e7\u00e3o']), ensure_ascii=False).encode('utf-8'))
        self.assertTrue(manifest.compatible('v.2.4.0.2 #966'))
        self.assertFalse(manifest.compatible(None))

    def test_checker_import_and_callback_without_game(self):
        class Transport(object):
            def request(self, url, callback, timeout, max_bytes):
                self.url = url
                callback(Response(200, b'[]', url), None)
        transport, results = Transport(), []
        self.assertTrue(Checker(transport).check(VERSION, 'stable', '2.4.0.2', lambda result, error: results.append((result, error))))
        self.assertEqual(transport.url, RELEASES)
        self.assertIsNone(results[0][1])
        self.assertIsNone(results[0][0]['latestVersion'])
        self.assertEqual(State().snapshot()['installedVersion'], VERSION)
        self.assertFalse(UpdaterService().active)

    def test_verified_https_handler_on_real_python_runtime(self):
        import ssl
        handler = next(item for item in verified_opener().handlers if isinstance(item, http.HTTPSHandler))
        self.assertEqual(handler._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(handler._context.check_hostname)

    def test_compatible_streaming_hash_and_ready(self):
        class Callbacks(object):
            callback = None
            def schedule(self, delay, callback):
                self.callback = callback
                return 1
            def cancel(self, token):
                self.callback = None
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
            archive.writestr('meta.xml', '<root><id>driftkings.unified</id><version>1.0.0</version></root>')
            archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc', b'\x03\xf3\x0d\x0a' + b'\0' * 16)
        data = output.getvalue()
        url = 'https://github.com/' + REPOSITORY + '/releases/download/v1.0.0/Driftkings.wotmod'
        class Remote(object):
            def __init__(self): self.source = io.BytesIO(data)
            def read(self, count): return self.source.read(count)
            def info(self): return {'Content-Length': str(len(data))}
            def geturl(self): return url
            def getcode(self): return 200
            def close(self): pass
        class Opener(object):
            def open(self, request, timeout): return Remote()
        callbacks, results = Callbacks(), []
        transport = HttpsTransport(callbacks, opener_factory=Opener)
        root = tempfile.mkdtemp()
        path = None
        try:
            value = Manifest(dict(schema=1, version='1.0.0', channel='stable', gameVersion='2.4.0.2',
                file='Driftkings.wotmod', size=len(data), sha256=hashlib.sha256(data).hexdigest(), download=url))
            downloader = Downloader(transport, root)
            self.assertTrue(downloader.start(value, lambda result, error: results.append((result, error))))
            self.assertTrue(downloader.handle.finished.wait(5))
            callbacks.callback()
            path, error = results[0]
            self.assertIsNone(error)
            with open(path, 'rb') as source:
                self.assertEqual(source.read(), data)
            with open(os.path.join(os.path.dirname(path), 'release.json'), 'rb') as source:
                self.assertEqual(Manifest.parse(source.read()).sha256, value.sha256)
        finally:
            transport.close()
            # Only the fixture files created above are removed.
            for folder in os.listdir(root):
                directory = os.path.join(root, folder)
                for name in ('Driftkings.wotmod.ready', 'Driftkings.wotmod.download', 'release.json'):
                    target = os.path.join(directory, name)
                    if os.path.isfile(target): os.remove(target)
                os.rmdir(directory)
            os.rmdir(root)


if __name__ == '__main__':
    unittest.main()
