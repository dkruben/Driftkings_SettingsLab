"""Slow owned IO must not block client callbacks or authorize stale restart."""
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core.updater.file_work import FileWork
from Driftkings.core.updater import UpdaterService
from Driftkings.core.updater.results import Results
from Driftkings.core.updater.state import READY, RESTART_REQUIRED
from test_updater_download import Callbacks
from test_updater_installer import InstallerFixtures


def until(callbacks, predicate):
    deadline = time.monotonic() + 5
    while not predicate() and time.monotonic() < deadline:
        callbacks.pump()
        time.sleep(0.005)
    assert predicate(), 'Background work did not complete'


class FileWorkTests(unittest.TestCase):
    def setUp(self):
        self.callbacks = Callbacks()
        self.work = FileWork(self.callbacks)
        self.addCleanup(self.work.close)

    def test_slow_io_does_not_block_client_and_completion_uses_client_thread(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        entered = threading.Event()
        delivered = []
        def task():
            self.assertNotEqual(threading.get_ident(), self.callbacks.thread)
            entered.set()
            gate.wait(3)
            return 42
        self.work.submit(task, lambda value, error: delivered.append((threading.get_ident(), value, error)))
        self.assertTrue(entered.wait(1))
        marker = []
        self.callbacks.schedule(0, lambda: marker.append(True))
        self.callbacks.pump()
        self.assertEqual(marker, [True])
        self.assertEqual(delivered, [])
        gate.set()
        until(self.callbacks, lambda: bool(delivered))
        self.assertEqual(delivered, [(self.callbacks.thread, 42, None)])

    def test_stop_discards_late_preparation_without_delivering_callback(self):
        gate = threading.Event()
        entered = threading.Event()
        cleaned = threading.Event()
        self.addCleanup(gate.set)
        delivered = Mock()
        def task():
            entered.set()
            gate.wait(3)
            return 42
        self.work.submit(task, delivered, lambda value: cleaned.set())
        self.assertTrue(entered.wait(1))
        self.work.close()
        gate.set()
        self.assertTrue(cleaned.wait(1))
        self.assertEqual(self.callbacks.pending, {})
        delivered.assert_not_called()

    def test_bounded_concurrency_and_failed_job_does_not_leak_slot(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        for _ in range(4): self.work.submit(lambda: gate.wait(3), Mock())
        with self.assertRaises(RuntimeError): self.work.submit(Mock(), Mock())
        gate.set()
        until(self.callbacks, lambda: not self.work.jobs)
        delivered = Mock()
        def failure(): raise OSError('fixture')
        self.work.submit(failure, delivered)
        until(self.callbacks, lambda: delivered.called)
        self.assertIsInstance(delivered.call_args.args[1], OSError)
        self.assertEqual(self.work.jobs, [])


class BackgroundInstallerTests(InstallerFixtures, unittest.TestCase):
    def test_preparation_never_launches_and_context_is_rechecked_on_client(self):
        job = self.installer.prepare_install(str(self.ready), '2.4.0.2', 'stable', lambda: True,
                                            self.installer.resources())
        self.launcher.assert_not_called()
        self.assertFalse(self.installer.launch_prepared(job, lambda: False))
        self.assertFalse((self.stage / 'install.json').exists())
        self.assertEqual(self.target.read_bytes(), self.old)
        self.assertEqual(self.ready.read_bytes(), self.data)

    def test_changed_target_between_preparation_and_launch_is_rejected(self):
        job = self.installer.prepare_install(str(self.ready), '2.4.0.2', 'stable', lambda: True,
                                            self.installer.resources())
        self.target.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.installer.launch_prepared(job, lambda: True)
        self.launcher.assert_not_called()
        self.assertFalse((self.stage / 'install.json').exists())
        self.assertEqual(self.target.read_bytes(), b'changed')


class BackgroundServiceTests(InstallerFixtures, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.callbacks = Callbacks()
        self.now = 100
        self.reason = None
        self.policy = NS(blocked_reason=lambda space: self.reason if space == 'lobby' else 'unsafeContext')
        self.results = Results(str(self.root))
        self.launcher.return_value.pid = 23456
        self.api = NS(client_version='2.4.0.2', get=lambda mod, key, default: default)
        self.service = UpdaterService(self.api, safe_spaces=('login', 'lobby'), clock=lambda: self.now,
                                      installer=self.installer, callbacks=self.callbacks, results=self.results,
                                      context_policy=self.policy, file_work=FileWork(self.callbacks))
        self.service.start()
        self.addCleanup(self.service.stop)
        self.service.onContextEntered('lobby')
        until(self.callbacks, lambda: self.service.state.snapshot()['status'] == READY)

    def prepared(self):
        self.assertTrue(self.service.schedule_install())
        until(self.callbacks, lambda: self.launcher.called)
        (self.stage / 'result.json').write_text('{"schema":1,"status":"prepared","error":null,"helperPid":23456}')
        until(self.callbacks, lambda: self.service.state.snapshot()['status'] == RESTART_REQUIRED)
        self.assertTrue(self.service.restart_ready())

    def test_prepared_proof_allows_restart_without_slow_receipt_reads_on_client(self):
        main = threading.get_ident()
        original = self.results.ticket
        def ticket(*args):
            self.assertNotEqual(threading.get_ident(), main)
            return original(*args)
        with patch.object(self.results, 'ticket', side_effect=ticket):
            self.prepared()
            self.assertTrue(self.service.claim_restart())
            self.assertFalse(self.service.claim_restart())

    def test_expired_proof_and_battle_context_block_restart(self):
        self.prepared()
        self.now += 6
        self.assertFalse(self.service.claim_restart())
        until(self.callbacks, lambda: self.service.restart_ready())
        self.reason = 'battleContext'
        self.assertFalse(self.service.claim_restart())

    def test_restart_consent_is_pid_bound_one_shot_and_can_be_revoked(self):
        import json
        import os
        self.prepared()
        self.assertTrue(self.service.claim_restart())
        marker = self.stage / 'restart.install'
        self.assertEqual(json.loads(marker.read_text()), dict(schema=1, helperPid=23456, parentPid=os.getpid()))
        self.assertFalse(self.service.claim_restart())
        self.service.revoke_restart()
        self.assertFalse(marker.exists())
        until(self.callbacks, lambda: self.service.restart_ready())
        self.assertTrue(self.service.claim_restart())

    def test_restart_marker_write_failure_never_authorizes_shutdown(self):
        self.prepared()
        with patch.object(self.installer, 'request_restart', side_effect=OSError('write failed')):
            self.assertFalse(self.service.claim_restart())
        self.assertFalse(self.service._restart_requested)
        self.assertFalse((self.stage / 'restart.install').exists())

    def test_live_receipt_recheck_prevents_marker_for_changed_acknowledgement(self):
        self.prepared()
        (self.stage / 'result.json').write_text('{"schema":1,"status":"prepared","error":null,"helperPid":1}')
        self.assertFalse(self.installer.request_restart(str(self.ready)))
        self.assertFalse((self.stage / 'restart.install').exists())

    def test_stale_marker_is_removed_before_rearming_interrupted_ticket(self):
        self.prepared()
        (self.stage / 'restart.install').write_text('{"schema":1,"helperPid":1,"parentPid":2}')
        self.installer.process.poll.return_value = 1
        self.assertTrue(self.installer.resume(str(self.ready), '2.4.0.2', 'stable', lambda: True))
        self.assertFalse((self.stage / 'restart.install').exists())

    def test_changed_receipt_invalidates_restart_before_next_poll(self):
        self.prepared()
        (self.stage / 'result.json').write_text('{"schema":1,"status":"error","error":"fixture","helperPid":23456}')
        self.assertFalse(self.service.claim_restart())

    def test_slow_receipt_validation_leaves_client_responsive_and_proof_expires(self):
        self.prepared()
        gate = threading.Event()
        entered = threading.Event()
        self.addCleanup(gate.set)
        original = self.results.ticket
        def slow(*args):
            entered.set()
            gate.wait(3)
            return original(*args)
        with patch.object(self.results, 'ticket', side_effect=slow):
            self.callbacks.pump()
            self.assertTrue(entered.wait(1))
            self.now += 6
            marker = []
            self.callbacks.schedule(0, lambda: marker.append(True))
            self.callbacks.pump()
            self.assertEqual(marker, [True])
            self.assertFalse(self.service.claim_restart())
            gate.set()
            until(self.callbacks, lambda: not self.service._receipt_busy)
        self.assertTrue(self.service.restart_ready())

    def test_game_resources_and_context_are_accessed_only_on_client_thread(self):
        main = threading.get_ident()
        reader = self.installer.resource_reader
        policy = self.policy.blocked_reason
        def resources(name):
            self.assertEqual(threading.get_ident(), main)
            return reader(name)
        def context(space):
            self.assertEqual(threading.get_ident(), main)
            return policy(space)
        self.installer.resource_reader = resources
        self.policy.blocked_reason = context
        self.prepared()

    def test_stop_during_preparation_discards_late_files_and_never_launches(self):
        gate = threading.Event()
        entered = threading.Event()
        finished = threading.Event()
        self.addCleanup(gate.set)
        original = self.installer.prepare_install
        def prepare(*args):
            job = original(*args)
            entered.set()
            gate.wait(3)
            return job
        discard = self.installer.discard_preparation
        def cleanup(job):
            discard(job)
            finished.set()
        with patch.object(self.installer, 'prepare_install', side_effect=prepare), \
                patch.object(self.installer, 'discard_preparation', side_effect=cleanup):
            self.assertTrue(self.service.schedule_install())
            self.assertTrue(entered.wait(1))
            self.service.stop()
            gate.set()
            self.assertTrue(finished.wait(1))
        self.launcher.assert_not_called()
        self.assertFalse((self.stage / 'install.json').exists())
        self.assertFalse((self.stage / 'Driftkings.UpdateInstaller.exe').exists())
        self.assertEqual(self.callbacks.pending, {})
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_context_change_during_slow_preparation_never_launches(self):
        gate = threading.Event()
        entered = threading.Event()
        self.addCleanup(gate.set)
        original = self.installer.prepare_install
        def prepare(*args):
            entered.set()
            gate.wait(3)
            return original(*args)
        with patch.object(self.installer, 'prepare_install', side_effect=prepare):
            self.assertTrue(self.service.schedule_install())
            self.assertTrue(entered.wait(1))
            self.service.onContextEntered('battle')
            gate.set()
            until(self.callbacks, lambda: not self.service._prepare_active)
        self.launcher.assert_not_called()
        self.assertFalse(self.service.state.snapshot()['installScheduled'])
        self.assertEqual(self.target.read_bytes(), self.old)

    def test_cancel_during_slow_preparation_returns_ready_without_native_launch(self):
        gate = threading.Event()
        entered = threading.Event()
        self.addCleanup(gate.set)
        original = self.installer.prepare_install
        def prepare(*args):
            entered.set()
            gate.wait(3)
            return original(*args)
        with patch.object(self.installer, 'prepare_install', side_effect=prepare):
            self.assertTrue(self.service.schedule_install())
            self.assertTrue(entered.wait(1))
            self.assertTrue(self.service.cancel_install())
            gate.set()
            until(self.callbacks, lambda: not self.service._prepare_active)
        self.launcher.assert_not_called()
        self.assertEqual(self.service.state.snapshot()['status'], READY)
        self.assertFalse((self.stage / 'install.json').exists())
