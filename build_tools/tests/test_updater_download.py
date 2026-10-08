"""Production streaming/staging tested with deterministic IO and client callbacks."""
import hashlib
import io
import json
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core.updater import UpdaterService
from Driftkings.core.updater.downloader import Downloader, StagingSink
from Driftkings.core.updater.https_transport import HttpsTransport, HTTPSRedirects, TransferError, verified_opener, http, runtime_transport
from Driftkings.core.updater.manifest import Manifest
from Driftkings.core.updater.state import AVAILABLE, DOWNLOADING, VERIFYING, READY, ERROR, IDLE
from Driftkings.settings.panel.api import SettingsAPI
from Driftkings.settings.panel import core_page

URL = 'https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v1.0.0/Driftkings.wotmod'


def package(version='1.0.0', identity='driftkings.unified', entry='res/scripts/client/gui/mods/mod_Driftkings.pyc', extra=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('meta.xml', '<root><id>%s</id><version>%s</version></root>' % (identity, version))
        archive.writestr(entry, b'\x03\xf3\x0d\x0a' + b'\0' * 20)
        for name, value in (extra or {}).items():
            archive.writestr(name, value)
    return output.getvalue()


def manifest(data, **changes):
    values = dict(schema=1, version='1.0.0', channel='stable', gameVersion='2.4.0.2',
                  file='Driftkings.wotmod', size=len(data), sha256=hashlib.sha256(data).hexdigest(), download=URL)
    values.update(changes)
    return Manifest(values)


class Callbacks:
    def __init__(self):
        self.pending = {}
        self.sequence = 0
        self.thread = threading.get_ident()

    def schedule(self, delay, callback):
        assert threading.get_ident() == self.thread, 'Worker must never call client APIs'
        self.sequence += 1
        self.pending[self.sequence] = callback
        return self.sequence

    def cancel(self, token):
        self.pending.pop(token, None)

    def pump(self):
        pending, self.pending = self.pending, {}
        for callback in pending.values():
            callback()


class Response:
    def __init__(self, data, headers=None, url=URL, status=200):
        self.source = io.BytesIO(data)
        self.headers = headers or {}
        self.url, self.status = url, status
        self.closed = False
        self.reads = 0
        self.entered = None
        self.release = None
        self.error = None

    def geturl(self): return self.url
    def getcode(self): return self.status
    def info(self): return self.headers

    def read(self, count):
        self.reads += 1
        if self.entered is not None and self.reads == 2:
            self.entered.set()
            if not self.release.wait(5):
                raise RuntimeError('Test barrier timed out')
        if self.error is not None:
            raise self.error
        return self.source.read(count)

    def close(self):
        self.closed = True


class Opener:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request.get_full_url(), timeout))
        return self.response


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'cache/update'
        self.data = package(extra={'res/data.bin': b'a' * 100000})
        self.response = Response(self.data)
        self.opener = Opener(self.response)
        self.callbacks = Callbacks()
        self.transport = HttpsTransport(self.callbacks, opener_factory=lambda: self.opener)
        self.addCleanup(self.transport.close)
        self.downloader = Downloader(self.transport, str(self.stage))
        self.results, self.progress = [], []

    def start(self, meta=None):
        return self.downloader.start(meta or manifest(self.data), lambda *result: self.results.append(result),
                                     lambda *value: self.progress.append(value))

    def finish(self):
        operation = self.downloader.handle
        self.assertTrue(operation.finished.wait(5), 'Worker did not finish')
        self.callbacks.pump()
        self.assertEqual(len(self.results), 1)
        return self.results[0]

    def test_stream_good_hash_size_and_ready_manifest(self):
        self.assertTrue(self.start())
        path, error = self.finish()
        self.assertIsNone(error)
        self.assertEqual(Path(path).read_bytes(), self.data)
        self.assertTrue(path.endswith('Driftkings.wotmod.ready'))
        metadata = Manifest.parse((Path(path).parent / 'release.json').read_bytes())
        self.assertEqual(metadata.sha256, hashlib.sha256(self.data).hexdigest())
        self.assertEqual(list(self.stage.rglob('*.download')), [])
        self.assertIn(('verifying', None), self.progress)
        self.assertTrue(self.response.closed)
        self.assertEqual(self.callbacks.pending, {})

    def test_hash_mismatch_deletes_partial(self):
        self.start(manifest(self.data, sha256='0' * 64))
        path, error = self.finish()
        self.assertIsNone(path)
        self.assertEqual(error, 'hashMismatch')
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_size_mismatch_truncation(self):
        self.start(manifest(self.data, size=len(self.data) + 1))
        path, error = self.finish()
        self.assertEqual(error, 'sizeMismatch')
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_excessive_bytes_rejected_during_stream(self):
        self.start(manifest(self.data, size=10))
        path, error = self.finish()
        self.assertEqual(error, 'oversizedPayload')
        self.assertFalse(self.stage.exists())

    def test_header_limit_before_read(self):
        self.response.headers['Content-Length'] = str(len(self.data) + 1)
        self.start()
        path, error = self.finish()
        self.assertEqual(error, 'oversizedPayload')
        self.assertEqual(self.response.reads, 0)

    def test_partial_content_length(self):
        self.response.headers['Content-Length'] = str(len(self.data) - 1)
        self.start()
        path, error = self.finish()
        self.assertEqual(error, 'partialDownload')
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_http_error_and_non_identity_encoding(self):
        self.response.status = 404
        self.start()
        self.assertEqual(self.finish()[1], 'httpError')
        self.response.status = 200
        self.response.headers['Content-Encoding'] = 'gzip'
        self.results.clear()
        self.start()
        self.assertEqual(self.finish()[1], 'invalidResponse')

    def test_timeout_network_error_and_tls_failure(self):
        import socket
        import ssl
        for error, code in ((socket.timeout(), 'timeout'), (OSError('IO'), 'networkError'),
                            (ssl.SSLError('invalid certificate'), 'networkError')):
            self.response.error = error
            self.results.clear()
            self.start()
            self.assertEqual(self.finish()[1], code)
            self.assertFalse(list(self.stage.rglob('*.ready')))

    def test_redirect_final_http_rejected_without_read(self):
        self.response.url = 'http://github.com/package'
        self.start()
        self.assertEqual(self.finish()[1], 'networkError')
        self.assertEqual(self.response.reads, 0)

    def test_cancel_during_transfer_cleanup_and_no_concurrent_download(self):
        self.response.entered = threading.Event()
        self.response.release = threading.Event()
        self.start()
        self.assertTrue(self.response.entered.wait(5))
        self.assertEqual(len(list(self.stage.rglob('*.download'))), 1)
        self.assertFalse(self.start())
        self.assertTrue(self.downloader.cancel())
        self.assertTrue(self.downloader.busy)
        self.response.release.set()
        self.assertEqual(self.finish()[1], 'cancelled')
        self.assertFalse(self.downloader.busy)
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_cancel_after_worker_before_delivery_removes_ready(self):
        self.start()
        operation = self.downloader.handle
        self.assertTrue(operation.finished.wait(5))
        self.assertEqual(len(list(self.stage.rglob('*.ready'))), 1)
        self.downloader.cancel()
        self.callbacks.pump()
        self.assertEqual(self.results, [(None, 'cancelled')])
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_cleanup_failure_on_cancel_is_reported_without_success(self):
        self.start()
        self.assertTrue(self.downloader.handle.finished.wait(5))
        with patch.object(self.downloader.sink, 'abort', side_effect=OSError('locked staging')):
            with self.assertLogs('Driftkings.Updater', level='ERROR'):
                self.assertTrue(self.downloader.cancel())
            self.callbacks.pump()
        self.assertEqual(self.results, [(None, 'stagingError')])
        self.downloader.sink.abort()

    def test_close_cancels_callbacks_and_cleanup_without_late_delivery(self):
        self.response.entered = threading.Event()
        self.response.release = threading.Event()
        self.start()
        self.assertTrue(self.response.entered.wait(5))
        operation = self.downloader.handle
        self.transport.close()
        self.response.release.set()
        self.assertTrue(operation.finished.wait(5))
        self.callbacks.pump()
        self.assertEqual(self.results, [])
        self.assertEqual(self.callbacks.pending, {})
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_invalid_packages_with_good_hash_never_ready(self):
        samples = (b'not a wotmod', package(identity='other'), package(version='2.0.0'),
                   package(entry='res/scripts/client/gui/mods/mod_other.pyc'),
                   package(extra={'../unsafe': b'x'}))
        for data in samples:
            self.response.source = io.BytesIO(data)
            self.results.clear()
            self.start(manifest(data))
            self.assertEqual(self.finish()[1], 'invalidPackage')
            self.assertEqual(list(self.stage.iterdir()), [])

    def test_compressed_dtd_case_collision_and_crc_corruption_rejected(self):
        cases = []
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('meta.xml', '<root><id>driftkings.unified</id><version>1.0.0</version></root>')
            archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc', b'\x03\xf3\x0d\x0a')
        cases.append(output.getvalue())
        cases.append(package(extra={'META.XML': b'collision'}))
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
            archive.writestr('meta.xml', '<!DOCTYPE root [<!ENTITY test "expanded">]><root/>')
            archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc', b'\x03\xf3\x0d\x0a')
        cases.append(output.getvalue())
        corrupted = package(extra={'res/data.bin': b'UNIQUE_DATA'})
        cases.append(corrupted.replace(b'UNIQUE_DATA', b'CORRUPTDATA'))
        for data in cases:
            self.response.source = io.BytesIO(data)
            self.results.clear()
            self.start(manifest(data))
            self.assertEqual(self.finish()[1], 'invalidPackage')
            self.assertEqual(list(self.stage.iterdir()), [])

    def test_file_tampering_before_hash_verification_is_detected(self):
        self.response.entered = threading.Event()
        self.response.release = threading.Event()
        self.start()
        self.assertTrue(self.response.entered.wait(5))
        # The worker is paused in read(); commit its buffer before corrupting disk.
        self.downloader.sink.file.flush()
        partial = next(self.stage.rglob('*.download'))
        with partial.open('r+b') as output:
            output.write(b'BAD!')
        self.response.release.set()
        self.assertEqual(self.finish()[1], 'hashMismatch')
        self.assertEqual(list(self.stage.iterdir()), [])

    def test_configs_and_installed_package_untouched(self):
        config = self.root / 'configs/personal.json'
        installed = self.root / 'mods/2.4.0.2/Driftkings.wotmod'
        for path, data in ((config, b'{"custom":true}'), (installed, b'original')):
            path.parent.mkdir(parents=True)
            path.write_bytes(data)
        self.start()
        self.finish()
        self.assertEqual(config.read_bytes(), b'{"custom":true}')
        self.assertEqual(installed.read_bytes(), b'original')

    def test_staging_is_not_config_store_and_not_shared_between_jobs(self):
        self.start()
        first, error = self.finish()
        self.response.source.seek(0)
        self.results.clear()
        self.start()
        second, error = self.finish()
        self.assertNotEqual(Path(first).parent, Path(second).parent)
        self.assertEqual(Path(first).read_bytes(), self.data)

    def test_symlink_staging_rejected(self):
        target = self.root / 'target'
        target.mkdir()
        try:
            self.stage.parent.mkdir(parents=True)
            self.stage.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest('OS does not permit symlink creation')
        self.start()
        self.assertEqual(self.finish()[1], 'stagingError')
        self.assertEqual(list(target.iterdir()), [])

    def test_write_failure_and_promotion_failure_cleanup(self):
        with patch('Driftkings.core.updater.downloader.os.fsync', side_effect=OSError('disk error')):
            self.start()
            self.assertEqual(self.finish()[1], 'stagingError')
        self.response.source.seek(0)
        self.results.clear()
        with patch('Driftkings.core.updater.downloader.os.rename', side_effect=OSError('rename error')):
            self.start()
            self.assertEqual(self.finish()[1], 'stagingError')
        self.assertEqual(list(self.stage.iterdir()), [])


class TransportTests(unittest.TestCase):
    def test_redirects_checked_before_following(self):
        handler = HTTPSRedirects()
        request = http.Request(URL)
        for url in ('http://github.com/a', 'https://evil.test/a', 'https://user@github.com/a', 'file:///tmp/a'):
            with self.assertRaises(ValueError):
                handler.redirect_request(request, None, 302, '', {}, url)
        result = handler.redirect_request(request, None, 302, '', {}, 'https://release-assets.githubusercontent.com/a')
        self.assertTrue(result.get_full_url().startswith('https://'))

    def test_verified_tls_policy(self):
        import ssl
        opener = verified_opener()
        https = next(handler for handler in opener.handlers if isinstance(handler, http.HTTPSHandler))
        self.assertEqual(https._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(https._context.check_hostname)
        self.assertTrue(https._context.get_ca_certs())

    def test_runtime_unavailable_if_verified_tls_missing(self):
        with patch('Driftkings.core.updater.https_transport.verified_opener', side_effect=ImportError('ssl missing')):
            self.assertFalse(runtime_transport().available)

    def test_response_limit_applies_to_metadata_too(self):
        callbacks = Callbacks()
        response = Response(b'a' * 11)
        transport = HttpsTransport(callbacks, opener_factory=lambda: Opener(response))
        self.addCleanup(transport.close)
        results = []
        handle = transport.request(URL, lambda *value: results.append(value), 15, 10)
        self.assertTrue(handle.finished.wait(5))
        callbacks.pump()
        self.assertEqual(results, [(None, 'oversizedPayload')])

    def test_total_deadline_and_invalid_timeout(self):
        callbacks = Callbacks()
        times = iter((0.0, 0.0, 20.0))
        response = Response(b'[]')
        transport = HttpsTransport(callbacks, opener_factory=lambda: Opener(response), clock=lambda: next(times))
        self.addCleanup(transport.close)
        results = []
        handle = transport.request(URL, lambda *value: results.append(value), 15, 100)
        self.assertTrue(handle.finished.wait(5))
        callbacks.pump()
        self.assertEqual(results, [(None, 'timeout')])
        self.assertEqual(response.reads, 0)
        for value in (0, -1, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                transport.request(URL, lambda *value: None, value, 100)


class ServiceDownloadTests(unittest.TestCase):
    def setUp(self):
        DownloadTests.setUp(self)
        self.api = SettingsAPI(str(self.root / 'settings'))
        core_page.install(self.api)
        self.api.client_version = '2.4.0.2'
        self.service = UpdaterService(self.api, self.transport, safe_spaces=('login', 'lobby'), staging_root=str(self.stage))
        self.service.start()
        self.addCleanup(self.service.stop)
        self.service.checker.selected_manifest = manifest(self.data)
        self.service.state.update(status=AVAILABLE, latestVersion='1.0.0', compatible=True, canDownload=True)

    def test_service_downloading_verifying_ready_and_check_blocked(self):
        states = []
        self.service.state.subscribe(lambda: states.append(self.service.state.snapshot()['status']))
        self.assertTrue(self.service.download())
        self.assertFalse(self.service.download())
        self.assertFalse(self.service.check(manual=True))
        handle = self.service.downloader.handle
        self.assertTrue(handle.finished.wait(5))
        self.callbacks.pump()
        self.assertIn(DOWNLOADING, states)
        self.assertIn(VERIFYING, states)
        self.assertEqual(states[-1], READY)
        self.assertEqual(self.service.state.snapshot()['downloadPercent'], 100)
        self.assertTrue(Path(self.service._ready_path).is_file())

    def test_incompatible_and_unknown_client_blocks_download(self):
        for version in ('2.5.0.0', None):
            self.api.client_version = version
            self.assertFalse(self.service.download())
        self.assertEqual(self.opener.calls, [])

    def test_ready_in_battle_does_not_install_or_restart(self):
        self.service.onContextEntered('battle')
        self.service.download()
        self.assertTrue(self.service.downloader.handle.finished.wait(5))
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['status'], READY)
        self.assertFalse(self.service.schedule_install())

    def test_stop_invalidates_download_result(self):
        self.service.download()
        operation = self.service.downloader.handle
        self.service.stop()
        self.assertTrue(operation.finished.wait(5))
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['status'], IDLE)
        self.assertIsNone(self.service._ready_path)
        self.assertFalse(list(self.stage.rglob('*.ready')))

    def test_channel_change_during_download_cancels_old_result(self):
        self.service.download()
        operation = self.service.downloader.handle
        self.api.registry.mods['dk.settings'].values['updateChannel'] = 'beta'
        self.service._preferences_changed({'updateChannel': 'beta'})
        self.assertTrue(operation.finished.wait(5))
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['channel'], 'beta')
        self.assertEqual(self.service.state.snapshot()['status'], IDLE)
        self.assertFalse(list(self.stage.rglob('*.ready')))

    def test_cancel_from_state_observer_before_request_starts(self):
        def cancel():
            if self.service.state.snapshot()['status'] == DOWNLOADING:
                self.service.cancel_download()
        self.service.state.subscribe(cancel)
        self.assertFalse(self.service.download())
        self.assertEqual(self.opener.calls, [])

    def test_download_failure_logs_error_and_allows_retry(self):
        self.service.checker.selected_manifest = manifest(self.data, sha256='0' * 64)
        with self.assertLogs('Driftkings.Updater', level='ERROR') as logged:
            self.service.download()
            self.assertTrue(self.service.downloader.handle.finished.wait(5))
            self.callbacks.pump()
        self.assertIn('hashMismatch', logged.output[0])
        self.assertEqual(self.service.state.snapshot()['status'], ERROR)
        self.assertTrue(self.service.state.snapshot()['canDownload'])
        self.assertFalse(list(self.stage.rglob('*.ready')))


if __name__ == '__main__':
    unittest.main()
