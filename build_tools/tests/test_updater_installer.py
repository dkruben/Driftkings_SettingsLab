"""Installer fixtures live under local build/: never the real game installation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings import VERSION
from Driftkings.core.updater.installer import Installer, READY, HELPER_RESOURCE, digest
from test_updater_download import package, manifest

FIXTURES = ROOT / 'build/updater-tests'


class InstallerFixtures:
    def setUp(self):
        FIXTURES.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=FIXTURES)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'mods/configs/Driftkings/cache/update/download-fixture'
        self.stage.mkdir(parents=True)
        self.data = package()
        self.ready = self.stage / READY
        self.ready.write_bytes(self.data)
        (self.stage / 'release.json').write_text(json.dumps(manifest(self.data).document()))
        self.target = self.root / 'mods/2.4.0.2/Driftkings.wotmod'
        self.target.parent.mkdir(parents=True)
        self.old = package(VERSION)
        self.target.write_bytes(self.old)
        self.config = self.root / 'mods/configs/Driftkings/user.json'
        self.config.write_bytes(b'\xef\xbb\xbf{"unchanged":true}')
        self.launcher = Mock(return_value=Mock(poll=Mock(return_value=None)))
        self.binary = b'MZ' + b'local-fixture'
        self.info = dict(schema=1, size=len(self.binary), sha256=hashlib.sha256(self.binary).hexdigest())
        self.reader = lambda name: self.binary if name == HELPER_RESOURCE else json.dumps(self.info).encode()
        self.installer = Installer(str(self.root), self.reader, self.launcher)


class InstallerTests(InstallerFixtures, unittest.TestCase):
    def test_binary_creation_preserves_newlines_and_sets_binary_flag(self):
        self.binary = b'MZ\x00\n\r\n\x1a\xff'
        self.info.update(size=len(self.binary), sha256=hashlib.sha256(self.binary).hexdigest())
        original = os.open
        with patch('Driftkings.core.updater.installer.os.open', wraps=original) as opened:
            self.assertTrue(self.schedule())
        self.assertEqual((self.stage / 'Driftkings.UpdateInstaller.exe').read_bytes(), self.binary)
        if os.name == 'nt':
            self.assertTrue(all(call.args[1] & os.O_BINARY for call in opened.call_args_list))

    def test_changed_written_helper_never_launches_and_removes_only_preparation(self):
        original = os.fsync
        def corrupt(descriptor):
            original(descriptor)
            helper = self.stage / 'Driftkings.UpdateInstaller.exe'
            if helper.exists():
                data = helper.read_bytes()
                helper.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
        with patch('Driftkings.core.updater.installer.os.fsync', side_effect=corrupt):
            with self.assertRaises(ValueError):
                self.schedule()
        self.launcher.assert_not_called()
        self.assertFalse((self.stage / 'Driftkings.UpdateInstaller.exe').exists())
        self.assertFalse((self.stage / 'install.json').exists())
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(self.ready.read_bytes(), self.data)

    def schedule(self, safe=lambda: True, **changes):
        return self.installer.schedule(str(self.ready), changes.get('client', '2.4.0.2'),
                                       changes.get('channel', 'stable'), safe)

    def test_unsafe_or_unknown_context_blocks_before_any_write(self):
        for safe in (lambda: False, lambda: None, None, lambda: 1):
            self.assertFalse(self.schedule(safe))
        self.launcher.assert_not_called()
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(set(p.name for p in self.stage.iterdir()), {READY, 'release.json'})

    def test_safe_schedule_uses_only_owned_executable_no_shell_and_leaves_package_configs(self):
        self.assertTrue(self.schedule())
        args, kwargs = self.launcher.call_args
        self.assertEqual(args[0], [str(self.stage / 'Driftkings.UpdateInstaller.exe'), str(self.stage), str(os.getpid())])
        self.assertFalse(kwargs['shell'])
        self.assertEqual(kwargs['creationflags'], 0x08000000)
        ticket = json.loads((self.stage / 'install.json').read_text())
        self.assertEqual(ticket['installedSha256'], hashlib.sha256(self.old).hexdigest())
        self.assertFalse(any(key in ticket for key in ('download', 'command', 'target', 'helper')))
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(self.config.read_bytes(), b'\xef\xbb\xbf{"unchanged":true}')
        self.assertIsNone(self.installer.result(str(self.ready)))
        self.assertFalse(self.schedule())
        self.assertEqual(self.launcher.call_count, 1)

    def test_context_change_during_preparation_prevents_launch(self):
        values = iter([True, False])
        self.assertFalse(self.schedule(lambda: next(values)))
        self.launcher.assert_not_called()
        self.assertFalse((self.stage / 'install.json').exists())
        self.assertFalse((self.stage / 'Driftkings.UpdateInstaller.exe').exists())

    def test_new_explicit_schedule_clears_only_its_previous_cancel_marker(self):
        self.installer.cancel(str(self.ready))
        self.assertTrue((self.stage / 'cancel.install').exists())
        self.assertTrue(self.schedule())
        self.assertFalse((self.stage / 'cancel.install').exists())
        self.assertEqual(self.config.read_bytes(), b'\xef\xbb\xbf{"unchanged":true}')

    def test_downgrade_incompatibility_wrong_channel_are_rejected(self):
        for client in (None, '2.4.0.3'):
            with self.assertRaises(ValueError): self.schedule(client=client)
        with self.assertRaises(ValueError):
            self.installer.validate_stage(str(self.ready), '2.4.0.2', 'stable', '1.0.0')
        data = package('1.0.0-beta.1')
        self.ready.write_bytes(data)
        (self.stage / 'release.json').write_text(json.dumps(manifest(data, version='1.0.0-beta.1', channel='beta').document()))
        with self.assertRaises(ValueError): self.schedule()

    def test_tampered_stage_cannot_be_scheduled(self):
        self.ready.write_bytes(self.data[:-1] + b'x')
        with self.assertRaises(ValueError): self.schedule()
        self.launcher.assert_not_called()

    def test_local_helper_hash_mismatch_cannot_be_launched(self):
        self.info['sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.schedule()
        self.launcher.assert_not_called()

    def test_staging_path_and_existing_transactions_are_not_overwritten(self):
        with self.assertRaises(ValueError):
            self.installer.validate_stage(str(self.target), '2.4.0.2', 'stable')
        (self.stage / 'install.json').write_text('{}')
        with self.assertRaises(ValueError): self.schedule()
        self.assertEqual((self.stage / 'install.json').read_text(), '{}')

    def test_unknown_backup_blocks_new_transaction(self):
        backup = Path(str(self.target) + '.old')
        backup.write_bytes(self.old)
        with self.assertRaises(ValueError): self.schedule()
        self.assertEqual(backup.read_bytes(), self.old)

    def test_launch_failure_removes_only_own_preparation_files(self):
        self.launcher.side_effect = OSError('fixture')
        with self.assertRaises(OSError): self.schedule()
        self.assertEqual(set(p.name for p in self.stage.iterdir()), {READY, 'release.json'})
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_interrupted_transaction_can_resume_without_rewriting_ticket_or_backup(self):
        self.assertTrue(self.schedule())
        ticket = (self.stage / 'install.json').read_bytes()
        self.installer.process.poll.return_value = 1
        backup = Path(str(self.target) + '.old')
        backup.write_bytes(self.old)
        self.assertFalse(self.installer.resume(str(self.ready), '2.4.0.2', 'stable', lambda: False))
        self.assertTrue(self.installer.resume(str(self.ready), '2.4.0.2', 'stable', lambda: True))
        self.assertEqual((self.stage / 'install.json').read_bytes(), ticket)
        self.assertEqual(backup.read_bytes(), self.old)

    def test_resume_refuses_tampered_helper_or_ticket(self):
        self.assertTrue(self.schedule())
        self.installer.process.poll.return_value = 1
        helper = self.stage / 'Driftkings.UpdateInstaller.exe'
        helper.write_bytes(b'MZtampered')
        with self.assertRaises(ValueError):
            self.installer.resume(str(self.ready), '2.4.0.2', 'stable', lambda: True)
        helper.write_bytes(self.binary)
        ticket_path = self.stage / 'install.json'
        ticket = json.loads(ticket_path.read_text())
        ticket['command'] = 'must never run'
        ticket_path.write_text(json.dumps(ticket))
        with self.assertRaises(ValueError):
            self.installer.resume(str(self.ready), '2.4.0.2', 'stable', lambda: True)
        self.assertEqual(self.launcher.call_count, 1)

    def test_recovery_ignores_partial_corrupt_and_already_installed_without_deleting(self):
        self.assertEqual(self.installer.recover_ready('2.4.0.2', 'stable'), str(self.ready))
        broken = self.stage.parent / 'download-broken'
        broken.mkdir()
        (broken / READY).write_bytes(b'not zip')
        (broken / 'release.json').write_text('{}')
        (broken / 'Driftkings.wotmod.download').write_bytes(b'partial')
        self.assertEqual(self.installer.recover_ready('2.4.0.2', 'stable'), str(self.ready))
        (self.stage / 'result.json').write_text('{"status":"installed"}')
        self.assertIsNone(self.installer.recover_ready('2.4.0.2', 'stable'))
        self.assertEqual((broken / 'Driftkings.wotmod.download').read_bytes(), b'partial')
        self.assertIsNone(self.installer.recover_ready(None, 'stable'))


@unittest.skipUnless(os.name == 'nt', 'Windows native transaction tests')
class NativeInstallerTests(InstallerFixtures, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / 'build_tools'))
        from build_updater_helper import build
        cls.helper = build()
        FIXTURES.mkdir(parents=True, exist_ok=True)
        harness = FIXTURES / 'Parent.cs'
        harness.write_text('using System; class Parent { static void Main() { Console.ReadLine(); } }')
        cls.parent_binary = FIXTURES / 'WorldOfTanks.exe'
        compiler = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
        subprocess.check_call([str(compiler), '/nologo', '/out:' + str(cls.parent_binary), str(harness)])
        fault = FIXTURES / 'Fault.cs'
        fault.write_text('''using System;
using System.IO;
class Fault {
    static int Main(string[] args) {
        string target = args[0], temporary = target + ".new", backup = target + ".old";
        bool rollback = false;
        try {
            Installer.ReplaceVerified(target, temporary, backup,
                () => { throw new IOException("injected post-replace verification failure"); },
                path => File.ReadAllText(path) == "complete-old",
                () => {}, () => {}, () => { rollback = true; });
        } catch (IOException) { }
        return rollback && File.ReadAllText(target) == "complete-old" && !File.Exists(backup) ? 0 : 1;
    }
}''')
        cls.fault_binary = FIXTURES / 'Fault.exe'
        subprocess.check_call([str(compiler), '/nologo', '/main:Fault', '/reference:System.Web.Extensions.dll',
                               '/reference:System.IO.Compression.dll', '/out:' + str(cls.fault_binary),
                               str(fault), str(ROOT / 'source/updater/Installer.cs')])

    def setUp(self):
        super().setUp()
        self.parents = []
        self.helpers = []
        self.addCleanup(self.close_processes)
        binary = self.root / 'win64/WorldOfTanks.exe'
        binary.parent.mkdir()
        shutil.copyfile(self.parent_binary, binary)
        self.parent = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, creationflags=0x08000000)
        self.parents.append(self.parent)
        shutil.copyfile(self.helper, self.stage / 'Driftkings.UpdateInstaller.exe')
        self.ticket = dict(schema=1, gameVersion='2.4.0.2', version='1.0.0', size=len(self.data),
                           sha256=hashlib.sha256(self.data).hexdigest(), installedVersion=VERSION,
                           installedSize=len(self.old), installedSha256=hashlib.sha256(self.old).hexdigest())
        self.write_ticket()

    def write_ticket(self):
        (self.stage / 'install.json').write_text(json.dumps(self.ticket))

    def close_processes(self):
        for process in self.parents + self.helpers:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            if process.stdin is not None: process.stdin.close()

    def launch(self, pid=None):
        helper = subprocess.Popen([str(self.stage / 'Driftkings.UpdateInstaller.exe'), str(self.stage),
                                   str(self.parent.pid if pid is None else pid)], creationflags=0x08000000)
        self.helpers.append(helper)
        return helper

    def prepared(self):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                result = self.installer.result(str(self.ready))
            except OSError:
                # The helper publishes atomically; Windows may transiently deny
                # opening the receipt while it replaces it. No acknowledgement yet.
                result = None
            if result:
                self.assertEqual(result['status'], 'prepared', result)
                return
            time.sleep(0.02)
        self.fail('No helper acknowledgement')

    def exit_parent(self):
        self.parent.stdin.write(b'closed\n')
        self.parent.stdin.flush()
        self.parent.wait(timeout=10)

    # The Python boundary tests run separately above. Native fixtures have an
    # existing helper/ticket and exercise the real executable transaction only.
    def test_native_waits_for_process_exit_then_atomically_installs(self):
        helper = self.launch()
        self.prepared()
        self.assertIsNone(helper.poll())
        self.assertEqual(self.target.read_bytes(), self.old)
        with self.assertRaises(PermissionError): self.ready.write_bytes(b'tampered')
        self.exit_parent()
        self.assertEqual(helper.wait(timeout=10), 0)
        self.assertEqual(self.target.read_bytes(), self.data)
        self.assertEqual(self.installer.result(str(self.ready))['status'], 'installed')
        self.assertFalse(Path(str(self.target) + '.old').exists())
        self.assertFalse(Path(str(self.target) + '.new').exists())
        self.assertEqual(self.config.read_bytes(), b'\xef\xbb\xbf{"unchanged":true}')

    def test_native_stage_hash_revalidated_before_acknowledgement(self):
        self.ready.write_bytes(self.data[:-1] + b'x')
        helper = self.launch()
        self.assertEqual(helper.wait(timeout=10), 1)
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(self.installer.result(str(self.ready))['status'], 'error')

    def test_native_rejects_non_game_parent(self):
        helper = self.launch(os.getpid())
        self.assertEqual(helper.wait(timeout=10), 1)
        self.assertIsNone(self.installer.result(str(self.ready)))
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_native_concurrent_helper_cannot_overwrite_active_ack(self):
        first = self.launch()
        self.prepared()
        second = self.launch()
        self.assertEqual(second.wait(timeout=10), 1)
        self.assertEqual(self.installer.result(str(self.ready))['status'], 'prepared')
        self.exit_parent()
        self.assertEqual(first.wait(timeout=10), 0)

    def test_native_other_game_instance_defers_install(self):
        helper = self.launch()
        self.prepared()
        other = subprocess.Popen([str(self.root / 'win64/WorldOfTanks.exe')], stdin=subprocess.PIPE,
                                 creationflags=0x08000000)
        self.parents.append(other)
        self.exit_parent()
        self.assertEqual(helper.wait(timeout=10), 1)
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(self.installer.result(str(self.ready))['status'], 'error')

    def test_native_target_changed_after_ack_is_preserved(self):
        helper = self.launch()
        self.prepared()
        self.target.write_bytes(b'external change')
        self.exit_parent()
        self.assertEqual(helper.wait(timeout=10), 1)
        self.assertEqual(self.target.read_bytes(), b'external change')
        self.assertFalse(Path(str(self.target) + '.old').exists())

    def test_native_recovers_interrupted_replace_from_verified_backup(self):
        Path(str(self.target) + '.old').write_bytes(self.old)
        self.target.write_bytes(b'interrupted fixture')
        helper = self.launch()
        self.prepared()
        self.exit_parent()
        self.assertEqual(helper.wait(timeout=10), 2)
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(self.installer.result(str(self.ready))['status'], 'rolledBack')

    def test_native_unknown_backup_is_preserved(self):
        backup = Path(str(self.target) + '.old')
        backup.write_bytes(b'unknown')
        helper = self.launch()
        self.prepared()
        self.exit_parent()
        self.assertEqual(helper.wait(timeout=10), 1)
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(backup.read_bytes(), b'unknown')

    def test_native_completed_transaction_recovers_backup_cleanup(self):
        Path(str(self.target) + '.old').write_bytes(self.old)
        self.target.write_bytes(self.data)
        helper = self.launch()
        self.prepared()
        self.exit_parent()
        self.assertEqual(helper.wait(timeout=10), 0)
        self.assertEqual(self.target.read_bytes(), self.data)
        self.assertFalse(Path(str(self.target) + '.old').exists())

    def test_native_post_replace_failure_restores_complete_old_file(self):
        target = self.root / 'fault.wotmod'
        target.write_text('complete-old')
        Path(str(target) + '.new').write_text('complete-new')
        self.assertEqual(subprocess.run([str(self.fault_binary), str(target)], timeout=10).returncode, 0)
        self.assertEqual(target.read_text(), 'complete-old')
        self.assertFalse(Path(str(target) + '.old').exists())

    def test_native_reparse_stage_is_rejected_without_mutating_target(self):
        actual = self.stage.parent / 'download-actual'
        self.stage.rename(actual)
        result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(self.stage), str(actual)],
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        helper = self.launch()
        self.assertEqual(helper.wait(timeout=10), 1)
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertFalse((actual / 'result.json').exists())

    def test_native_locked_target_fails_without_losing_installed_package(self):
        helper = self.launch()
        self.prepared()
        # Windows Python holds this file with sharing that denies File.Replace.
        with self.target.open('rb'):
            self.exit_parent()
            self.assertEqual(helper.wait(timeout=10), 1)
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertFalse(Path(str(self.target) + '.new').exists())
        self.assertFalse(Path(str(self.target) + '.old').exists())

    def test_native_ticket_cannot_supply_paths_or_commands(self):
        self.ticket['target'] = 'elsewhere'
        self.write_ticket()
        helper = self.launch()
        self.assertEqual(helper.wait(timeout=10), 1)
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_native_cancel_preparation_exits_while_parent_is_alive(self):
        helper = self.launch()
        self.prepared()
        self.installer.cancel(str(self.ready))
        self.assertEqual(helper.wait(timeout=10), 3)
        self.assertIsNone(self.parent.poll())
        self.assertEqual(self.installer.result(str(self.ready))['status'], 'cancelled')
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_service_with_real_helper_confirms_prepared_and_cancelled(self):
        from Driftkings.core.updater import UpdaterService
        from Driftkings.core.updater.results import Results
        from Driftkings.core.updater.state import RESTART_REQUIRED, READY
        from test_updater_download import Callbacks
        binary = self.helper.read_bytes()
        metadata = json.dumps(dict(schema=1, size=len(binary), sha256=hashlib.sha256(binary).hexdigest())).encode()
        self.installer.resource_reader = lambda name: binary if name == HELPER_RESOURCE else metadata
        def launch(args, **options):
            # Only the process-ID boundary is substituted: Python is not WoT.
            # The owned executable/ticket/paths/result/cancel flow are production.
            args[2] = str(self.parent.pid)
            helper = subprocess.Popen(args, **options)
            self.helpers.append(helper)
            return helper
        self.installer.launcher = launch
        api = SimpleNamespace(client_version='2.4.0.2', get=lambda mod, key, default: default)
        callbacks = Callbacks()
        policy = SimpleNamespace(blocked_reason=lambda space: None if space == 'lobby' else 'unsafeContext')
        service = UpdaterService(api, safe_spaces=('login', 'lobby'), installer=self.installer,
                                 callbacks=callbacks, context_policy=policy, results=Results(str(self.root)))
        service.start()
        self.addCleanup(service.stop)
        service.onContextEntered('lobby')
        self.assertEqual(service.state.snapshot()['status'], READY)
        self.assertTrue(service.schedule_install())
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and service.state.snapshot()['status'] != RESTART_REQUIRED:
            callbacks.pump()
            time.sleep(0.02)
        self.assertEqual(service.state.snapshot()['status'], RESTART_REQUIRED)
        self.assertTrue(service.restart_ready())
        self.assertTrue(service.cancel_install())
        self.assertFalse(service.restart_ready())
        while time.monotonic() < deadline and service.state.snapshot()['cancellingInstall']:
            callbacks.pump()
            time.sleep(0.02)
        self.assertEqual(service.state.snapshot()['status'], READY)
        self.assertFalse(service.state.snapshot()['installScheduled'])
        self.assertEqual(service.state.snapshot()['lastInstallResult']['status'], 'cancelled')
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertIsNone(self.parent.poll())


if __name__ == '__main__':
    unittest.main()
