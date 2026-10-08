"""Owned post-restart receipts: require both a valid result and installed bytes."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core.updater.results import Results
from test_updater_download import package, manifest
from Driftkings.core.updater import windows_files


class ResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt':
            from windows_files_test_support import initialize
            initialize()

    @classmethod
    def tearDownClass(cls):
        from windows_files_test_support import close
        close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'mods/configs/Driftkings/cache/update/download-fixture'
        self.stage.mkdir(parents=True)
        self.old, self.new = package('0.1.0'), package('1.0.0')
        self.ready = self.stage / 'Driftkings.wotmod.ready'
        self.ready.write_bytes(self.new)
        (self.stage / 'release.json').write_text(json.dumps(manifest(self.new).document()))
        self.ticket = dict(schema=1, gameVersion='2.4.0.2', version='1.0.0', size=len(self.new),
                           sha256=hashlib.sha256(self.new).hexdigest(), installedVersion='0.1.0',
                           installedSize=len(self.old), installedSha256=hashlib.sha256(self.old).hexdigest())
        (self.stage / 'install.json').write_text(json.dumps(self.ticket))
        self.target = self.root / 'mods/2.4.0.2/Driftkings.wotmod'
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.new)
        self.config = self.root / 'mods/configs/Driftkings/user.json'
        self.config.write_bytes(b'\xef\xbb\xbf{"user":true}')
        self.reader = Results(str(self.root), loaded_version='1.0.0')
        self.result('installed')

    def result(self, status, **changes):
        values = dict(schema=1, status=status, error=None, helperPid=12345)
        values.update(changes)
        (self.stage / 'result.json').write_text(json.dumps(values))

    def scan(self): return self.reader.scan('2.4.0.2')

    def test_installed_requires_package_identity_hash_and_loaded_version(self):
        reports = self.scan()
        self.assertEqual(reports[0]['status'], 'installed')
        self.assertEqual(reports[0]['version'], '1.0.0')
        self.reader.acknowledge(reports[0])
        self.assertEqual(self.scan(), [])
        self.assertEqual(self.config.read_bytes(), b'\xef\xbb\xbf{"user":true}')
        self.assertEqual(self.ready.read_bytes(), self.new)
        self.assertTrue((self.stage / 'install.json').exists())
        self.assertTrue((self.stage / 'result.json').exists())

    def test_hash_mismatch_missing_package_and_loaded_version_mismatch_never_succeed(self):
        self.target.write_bytes(self.new[:-1] + b'x')
        self.assertEqual(self.scan()[0]['status'], 'failed')
        self.target.unlink()
        self.assertEqual(self.scan()[0]['status'], 'failed')
        self.target.write_bytes(self.new)
        self.reader.loaded_version = '0.1.0'
        self.assertEqual(self.scan()[0]['status'], 'failed')

    def test_meta_version_mismatch_even_when_ticket_hash_matches_is_rejected(self):
        wrong = package('2.0.0')
        self.target.write_bytes(wrong)
        self.ready.write_bytes(wrong)
        meta = manifest(wrong)
        (self.stage / 'release.json').write_text(json.dumps(meta.document()))
        self.ticket.update(size=len(wrong), sha256=hashlib.sha256(wrong).hexdigest())
        (self.stage / 'install.json').write_text(json.dumps(self.ticket))
        self.assertEqual(self.scan()[0]['status'], 'failed')

    def test_rollback_verifies_old_package_and_preserves_diagnostics(self):
        self.result('rolledBack', error='interruptedInstall')
        self.target.write_bytes(self.old)
        self.reader.loaded_version = '0.1.0'
        report = self.scan()[0]
        self.assertEqual(report['status'], 'rolled_back')
        self.reader.acknowledge(report)
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertTrue((self.stage / 'result.json').exists())

    def test_cancelled_is_not_error_and_can_be_followed_by_new_result(self):
        self.target.write_bytes(self.old)
        self.reader.loaded_version = '0.1.0'
        self.result('cancelled')
        report = self.scan()[0]
        self.assertEqual(report['status'], 'cancelled')
        self.reader.acknowledge(report)
        self.assertEqual(self.scan(), [])
        self.result('error', error='installIOError')
        report = self.scan()[0]
        self.assertEqual(report['status'], 'failed')
        self.reader.acknowledge(report)
        self.assertEqual(self.scan(), [])

    def test_failed_result_preserves_backup_and_staging(self):
        backup = Path(str(self.target) + '.old')
        backup.write_bytes(b'unknown backup')
        self.result('error', error='installIOError')
        self.assertEqual(self.scan()[0]['status'], 'failed')
        self.assertEqual(backup.read_bytes(), b'unknown backup')

    def test_unknown_invalid_schema_duplicate_json_and_prepared_are_not_success(self):
        for changes in (dict(status='unknown'), dict(status='prepared'), dict(schema=2), dict(schema=True), dict(helperPid=True)):
            fields = dict(changes)
            status = fields.pop('status', 'installed')
            self.result(status, **fields)
            self.assertEqual(self.scan()[0]['status'], 'failed', changes)
        (self.stage / 'result.json').write_text('{"schema":1,"schema":1}')
        self.assertEqual(self.scan()[0]['status'], 'failed')

    def test_result_without_own_valid_ticket_is_ignored(self):
        (self.stage / 'install.json').write_text('{"schema":1,"target":"elsewhere"}')
        self.assertEqual(self.scan(), [])

    def test_ambiguous_backup_or_temporary_package_prevents_success(self):
        backup = Path(str(self.target) + '.old')
        backup.write_bytes(b'unknown')
        self.assertEqual(self.scan()[0]['status'], 'failed')
        backup.write_bytes(self.old)
        self.assertEqual(self.scan()[0]['status'], 'installed')
        temporary = Path(str(self.target) + '.new')
        temporary.write_bytes(self.new)
        self.assertEqual(self.scan()[0]['status'], 'failed')
        self.assertEqual(temporary.read_bytes(), self.new)

    def test_other_client_result_is_ignored(self):
        self.assertEqual(self.reader.scan('2.4.0.3'), [])
        self.assertEqual(self.reader.scan(None), [])

    def test_result_stamp_changes_for_new_helper_response(self):
        old = self.reader.result_stamp(str(self.ready))
        self.result('prepared', helperPid=67890)
        self.assertNotEqual(self.reader.result_stamp(str(self.ready)), old)

    @unittest.skipUnless(os.name == 'nt', 'Windows native file validation')
    def test_windows_validation_rejects_junction_and_handles_path_as_data(self):
        folder = self.root / "unicode-\u00e1-'-$()-folder"
        folder.mkdir()
        windows_files.safe_path(str(folder / 'not-created.json'))
        junction = self.root / 'junction'
        from test_windows_files_v2 import junction as create_junction
        create_junction(junction, folder)
        try:
            with self.assertRaises(OSError):
                windows_files.safe_path(str(junction / 'not-created.json'))
        finally:
            junction.rmdir()

    @unittest.skipUnless(os.name == 'nt', 'Windows atomic receipt replacement')
    def test_windows_replacement_failure_preserves_previous_receipt(self):
        report = self.scan()[0]
        self.reader.acknowledge(report)
        receipt = self.stage / 'notified.json'
        previous = receipt.read_bytes()
        report['fingerprint'] = 'a' * 64
        with patch.object(windows_files, 'replace_receipt', side_effect=OSError('unavailable')):
            with self.assertRaises(OSError):
                self.reader.acknowledge(report)
        self.assertEqual(receipt.read_bytes(), previous)
        self.assertFalse(list(self.stage.glob('notice-*')))

    def test_missing_windows_validator_fails_closed(self):
        with patch.object(windows_files.os.path, 'isfile', return_value=False):
            with self.assertRaises(OSError):
                windows_files.safe_path(str(self.stage))


if __name__ == '__main__': unittest.main()
