"""Phase 6: read-only policy and Core-owned installation lifecycle."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core.updater import UpdaterService
from Driftkings.core.updater.context import InstallContext
from Driftkings.core.updater.state import READY, ERROR, INSTALLING, RESTART_REQUIRED, IDLE
from Driftkings.settings.panel.api import SettingsAPI
from Driftkings.settings.panel import core_page
from test_updater_download import Callbacks, manifest, package


class InstallContextTests(unittest.TestCase):
    def setUp(self):
        self.loader = NS(getSpaceID=lambda: 'lobby')
        self.hangar = NS(inited=True, spaceInited=True, isModelLoaded=True)
        self.replay = NS(isPlaying=lambda: False, isLoading=lambda: False)
        self.cap = Mock(player=Mock(return_value=object()), is_in_battle=Mock(return_value=False),
                        current_mode=Mock(return_value='hangar'))
        self.policy = InstallContext('lobby', self.loader, self.hangar, self.replay, self.cap)

    def test_complete_hangar_allows_scheduling(self):
        self.assertIsNone(self.policy.blocked_reason('lobby'))

    def test_login_battle_loading_waiting_unknown_block(self):
        for space in ('login', 'battle', 'battle_loading', 'waiting', None):
            self.assertEqual(self.policy.blocked_reason(space), 'unsafeContext')
        self.loader.getSpaceID = lambda: 'battle'
        self.assertEqual(self.policy.blocked_reason('lobby'), 'unsafeContext')

    def test_missing_player_arena_and_unknown_mode_block(self):
        self.cap.player.return_value = None
        self.assertEqual(self.policy.blocked_reason('lobby'), 'unknownContext')
        self.cap.player.return_value = object()
        self.cap.is_in_battle.return_value = True
        self.assertEqual(self.policy.blocked_reason('lobby'), 'battleContext')
        self.cap.is_in_battle.return_value = False
        self.cap.current_mode.return_value = 'unknown'
        self.assertEqual(self.policy.blocked_reason('lobby'), 'unknownContext')

    def test_replay_blocks_even_without_an_arena(self):
        for method in ('isPlaying', 'isLoading'):
            setattr(self.replay, method, lambda: True)
            self.assertEqual(self.policy.blocked_reason('lobby'), 'replayContext')
            setattr(self.replay, method, lambda: False)
        self.replay.isLoading = lambda: None
        self.assertEqual(self.policy.blocked_reason('lobby'), 'unknownContext')

    def test_incomplete_hangar_and_query_exceptions_block(self):
        for name in ('inited', 'spaceInited', 'isModelLoaded'):
            setattr(self.hangar, name, False)
            self.assertEqual(self.policy.blocked_reason('lobby'), 'loadingContext')
            setattr(self.hangar, name, True)
        self.cap.player.side_effect = RuntimeError('incomplete runtime')
        self.assertEqual(self.policy.blocked_reason('lobby'), 'unknownContext')

    def test_existing_hangar_event_subscription_is_owned_and_removed(self):
        class Event:
            def __init__(self): self.handlers = []
            def __iadd__(self, handler): self.handlers.append(handler); return self
            def __isub__(self, handler): self.handlers.remove(handler); return self
        self.hangar.onVehicleChanged = Event()
        callback = Mock()
        self.policy.subscribe(callback)
        self.policy.subscribe(callback)
        self.assertEqual(self.hangar.onVehicleChanged.handlers, [callback])
        self.policy.unsubscribe(callback)
        self.assertEqual(self.hangar.onVehicleChanged.handlers, [])


class InstallLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.api = SettingsAPI(self.temp.name)
        core_page.install(self.api)
        self.api.client_version = '2.4.0.2'
        self.now = 100.0
        self.reason = None
        self.policy = NS(blocked_reason=lambda space: self.reason if space == 'lobby' else 'unsafeContext')
        self.callbacks = Callbacks()
        self.process = Mock(pid=23456, poll=Mock(return_value=None))
        self.installer = Mock(process=self.process, recover_ready=Mock(return_value=None),
                              schedule=Mock(return_value=True), resume=Mock(return_value=True),
                              result=Mock(return_value=None))
        self.service = UpdaterService(self.api, safe_spaces=('login', 'lobby'), clock=lambda: self.now,
                                      installer=self.installer, callbacks=self.callbacks, context_policy=self.policy)
        self.service.start()
        self.addCleanup(self.service.stop)
        self.service.onContextEntered('lobby')
        self.service._ready_path = str(ROOT / 'build/updater-context-fixture/download-stage/Driftkings.wotmod.ready')
        self.service.state.update(status=READY)
        self.service._refresh_install_context()

    def acknowledge(self):
        self.installer.result.return_value = dict(schema=1, helperPid=self.process.pid, status='prepared', error=None)
        self.callbacks.pump()

    def test_explicit_safe_schedule_and_matching_ack(self):
        self.assertTrue(self.service.state.snapshot()['canInstall'])
        self.assertTrue(self.service.schedule_install())
        self.assertEqual(self.service.state.snapshot()['status'], INSTALLING)
        self.assertFalse(self.service.state.snapshot()['installScheduled'])
        self.assertFalse(self.service.schedule_install())
        self.acknowledge()
        self.assertEqual(self.service.state.snapshot()['status'], RESTART_REQUIRED)
        self.assertTrue(self.service.state.snapshot()['installScheduled'])
        from Driftkings import VERSION
        self.assertEqual(self.service.state.snapshot()['installedVersion'], VERSION)
        self.assertFalse(self.service.check(manual=True))
        self.assertFalse(self.service.download())

    def test_battle_replay_loading_and_unknown_never_launch(self):
        for reason in ('battleContext', 'replayContext', 'loadingContext', 'unknownContext'):
            self.reason = reason
            self.assertFalse(self.service.schedule_install())
        self.installer.schedule.assert_not_called()
        self.installer.resume.assert_not_called()

    def test_missing_policy_disables_install_without_blocking_service(self):
        self.service.context_policy = None
        self.assertFalse(self.service.schedule_install())
        self.assertTrue(self.service.active)

    def test_stale_pid_result_does_not_arm_helper(self):
        self.service.schedule_install()
        self.installer.result.return_value = dict(schema=1, helperPid=1, status='prepared', error=None)
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['status'], INSTALLING)
        self.now += 16
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['error'], 'installHelperTimeout')
        self.installer.cancel.assert_called_once()

    def test_context_change_before_ack_cancels_preparation(self):
        self.service.schedule_install()
        self.service.onContextEntered('battle')
        self.acknowledge()
        self.assertEqual(self.service.state.snapshot()['status'], ERROR)
        self.assertEqual(self.service.state.snapshot()['error'], 'unsafeContext')
        self.assertFalse(self.service.state.snapshot()['canInstall'])
        self.installer.cancel.assert_called_once()

    def test_confirmed_intent_survives_normal_context_leave_and_shutdown(self):
        self.service.schedule_install()
        self.acknowledge()
        self.service.onContextLeft('lobby')
        self.service.stop()
        self.installer.cancel.assert_not_called()
        self.assertEqual(self.callbacks.pending, {})
        self.assertEqual(self.service.state.snapshot()['status'], IDLE)

    def test_unacknowledged_shutdown_cancels_and_late_callback_is_ignored(self):
        self.service.schedule_install()
        callback = list(self.callbacks.pending.values())[0]
        self.service.stop()
        self.installer.cancel.assert_called_once()
        callback()
        self.assertEqual(self.service.state.snapshot()['status'], IDLE)
        self.assertEqual(self.callbacks.pending, {})

    def test_dead_helper_does_not_remain_scheduled(self):
        self.service.schedule_install()
        self.acknowledge()
        self.process.poll.return_value = 1
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['status'], ERROR)
        self.assertFalse(self.service.state.snapshot()['installScheduled'])
        self.assertEqual(self.callbacks.pending, {})

    def test_observer_stop_prevents_launch(self):
        def observer():
            if self.service.state.snapshot()['status'] == INSTALLING:
                self.service.stop()
        self.service.state.subscribe(observer)
        self.assertFalse(self.service.schedule_install())
        self.installer.schedule.assert_not_called()

    def test_recovery_restores_ready_without_launch(self):
        self.installer.recover_ready.return_value = self.service._ready_path
        self.installer.validate_stage.return_value = manifest(package())
        self.service._recover_staging()
        self.assertEqual(self.service.state.snapshot()['latestVersion'], '1.0.0')
        self.assertEqual(self.service.state.snapshot()['status'], READY)
        self.installer.schedule.assert_not_called()

    def test_recovery_error_does_not_block_boot(self):
        self.installer.recover_ready.side_effect = OSError('fixture')
        self.service._recover_staging()
        self.assertTrue(self.service.active)

    def test_restart_service_reattaches_to_confirmed_helper_without_launch(self):
        self.service.schedule_install()
        self.acknowledge()
        self.service.stop()
        self.service.start()
        self.assertEqual(self.service.state.snapshot()['status'], RESTART_REQUIRED)
        self.assertTrue(self.service.state.snapshot()['installScheduled'])
        self.assertEqual(self.installer.schedule.call_count, 1)
        self.assertEqual(len(self.callbacks.pending), 1)

    def test_existing_ticket_routes_through_resume(self):
        folder = Path(self.temp.name) / 'download-stage'
        folder.mkdir()
        (folder / 'install.json').write_text('{}')
        self.service._ready_path = str(folder / 'Driftkings.wotmod.ready')
        self.assertTrue(self.service.schedule_install())
        self.installer.resume.assert_called_once()
        self.installer.schedule.assert_not_called()

    def test_context_event_updates_cached_metadata_without_a_permanent_poll(self):
        self.reason = 'loadingContext'
        self.service._on_install_context_changed()
        self.assertFalse(self.service.state.snapshot()['canInstall'])
        self.reason = None
        self.service._on_install_context_changed()
        self.assertTrue(self.service.state.snapshot()['canInstall'])
        self.assertEqual(self.callbacks.pending, {})

    def test_late_poll_from_old_operation_cannot_affect_new_preparation(self):
        self.service.schedule_install()
        late = list(self.callbacks.pending.values())[0]
        self.service.stop()
        self.service.start()
        self.service.onContextEntered('lobby')
        self.service._ready_path = str(Path(self.temp.name) / 'Driftkings.wotmod.ready')
        self.service.state.update(status=READY)
        self.service.schedule_install()
        pending = dict(self.callbacks.pending)
        late()
        self.assertEqual(self.callbacks.pending, pending)
        self.assertEqual(self.service.state.snapshot()['status'], INSTALLING)

    def test_cancel_before_and_after_prepared_requires_helper_confirmation(self):
        for prepared in (False, True):
            self.service.state.update(status=READY)
            self.assertTrue(self.service.schedule_install())
            if prepared: self.acknowledge()
            self.assertTrue(self.service.cancel_install())
            self.assertFalse(self.service.restart_ready())
            self.assertTrue(self.service.state.snapshot()['cancellingInstall'])
            self.callbacks.pump()
            self.assertTrue(self.service.state.snapshot()['cancellingInstall'])
            self.installer.result.return_value = dict(schema=1, status='cancelled', error=None, helperPid=self.process.pid)
            self.process.poll.return_value = 3
            self.callbacks.pump()
            self.assertEqual(self.service.state.snapshot()['status'], READY)
            self.assertFalse(self.service.state.snapshot()['cancellingInstall'])
            self.assertFalse(self.service.state.snapshot()['installScheduled'])
            self.assertEqual(self.service.state.snapshot()['lastInstallResult']['status'], 'cancelled')
            self.process.poll.return_value = None
            self.installer.result.return_value = None

    def test_more_later_preserves_prepared_and_restart_rechecks_proof(self):
        self.assertFalse(self.service.restart_ready())
        self.service.schedule_install()
        self.acknowledge()
        self.assertTrue(self.service.defer_restart())
        self.assertTrue(self.service.state.snapshot()['installScheduled'])
        self.assertTrue(self.service.restart_ready())
        self.reason = 'replayContext'
        self.assertFalse(self.service.restart_ready())
        self.reason = None
        self.installer.result.return_value['helperPid'] = 42
        self.assertFalse(self.service.restart_ready())
        self.installer.result.return_value['helperPid'] = self.process.pid
        self.assertTrue(self.service.claim_restart())
        self.assertFalse(self.service.claim_restart())
        self.installer.cancel.assert_not_called()

    def test_changed_ticket_never_confirms_prepared(self):
        self.service.results = Mock(ticket=Mock(return_value={'identity': 'original'}))
        self.service.schedule_install()
        self.service.results.ticket.return_value = {'identity': 'changed'}
        self.acknowledge()
        self.assertFalse(self.service.state.snapshot()['installScheduled'])
        self.assertEqual(self.service.state.snapshot()['error'], 'installTicketChanged')

    def test_confirmed_cancellation_remains_cancelled_if_staging_no_longer_valid(self):
        self.service.schedule_install()
        self.acknowledge()
        self.service.cancel_install()
        self.installer.result.return_value = dict(schema=1, status='cancelled', error=None, helperPid=self.process.pid)
        self.process.poll.return_value = 3
        self.installer.validate_stage.side_effect = ValueError('changed staging or channel')
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['status'], 'AVAILABLE')
        self.assertEqual(self.service.state.snapshot()['lastInstallResult']['status'], 'cancelled')
        self.assertIsNone(self.service.state.snapshot()['error'])
        self.assertFalse(self.service.state.snapshot()['canInstall'])

    def test_stale_result_from_reused_pid_and_ticket_cannot_arm_new_generation(self):
        self.service.results = Mock(ticket=Mock(return_value={'identity': 'same'}),
                                    result_stamp=Mock(return_value='old-response'))
        self.service.schedule_install()
        self.acknowledge()
        self.assertEqual(self.service.state.snapshot()['status'], INSTALLING)
        self.assertFalse(self.service.restart_ready())
        self.service.results.result_stamp.return_value = 'new-response'
        self.acknowledge()
        self.assertEqual(self.service.state.snapshot()['status'], RESTART_REQUIRED)

    def test_transient_receipt_sharing_error_retries_without_faking_prepared(self):
        self.service.schedule_install()
        self.installer.result.side_effect = OSError('Windows sharing violation')
        self.callbacks.pump()
        self.assertEqual(self.service.state.snapshot()['status'], INSTALLING)
        self.assertFalse(self.service.state.snapshot()['installScheduled'])
        self.installer.result.side_effect = None
        self.acknowledge()
        self.assertEqual(self.service.state.snapshot()['status'], RESTART_REQUIRED)

    def test_available_notice_once_per_version_and_only_in_safe_lobby(self):
        notices = []
        self.service.notifier = lambda key, version: notices.append((key, version))
        self.service.state.update(status='AVAILABLE', latestVersion='1.0.0', compatible=True)
        self.reason = 'loadingContext'
        self.service._deliver_notifications()
        self.assertEqual(notices, [])
        self.reason = None
        self.service._deliver_notifications()
        self.service._deliver_notifications()
        self.assertEqual(notices, [('updates.availableNotice', '1.0.0')])

    def test_previous_result_notified_once_and_acknowledged(self):
        self.service.results = Mock()
        report = dict(status='installed', version='1.0.0', error=None, fingerprint='receipt')
        self.service._previous_reports = [report]
        self.service.notifier = Mock()
        self.service._deliver_notifications()
        self.service._deliver_notifications()
        self.service.notifier.assert_called_once_with('updates.result.installed', '1.0.0')
        self.service.results.acknowledge.assert_called_once_with(report)


if __name__ == '__main__': unittest.main()
