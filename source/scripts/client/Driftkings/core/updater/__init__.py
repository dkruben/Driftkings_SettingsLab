# -*- coding: utf-8 -*-
"""Core-owned checks, staging and explicit installation after process exit."""
import logging
import os
import time
import threading
from Driftkings import VERSION
from Driftkings.core.updater.checker import Checker
from Driftkings.core.updater.state import State, IDLE, CHECKING, AVAILABLE, ERROR, DOWNLOADING, VERIFYING, READY, INSTALLING, RESTART_REQUIRED
from Driftkings.core.updater.transport import UnavailableTransport
from Driftkings.core.updater.downloader import Downloader

LOG = logging.getLogger('Driftkings.Updater')
INTERVAL = 4 * 60 * 60


class UpdaterService(object):
    def __init__(self, api=None, transport=None, clock=None, safe_spaces=None, timeout=15.0, staging_root=None,
                 installer=None, callbacks=None, context_policy=None, results=None, notifier=None, file_work=None):
        self.api = api
        self.clock = clock or time.time
        self.safe_spaces = safe_spaces
        self.state = State()
        self.checker = Checker(transport or UnavailableTransport(), timeout)
        self._runtime_transport = transport is None and api is None
        if staging_root is None:
            from Driftkings.core.cache import CONFIG_ROOT
            staging_root = os.path.join(CONFIG_ROOT, 'cache', 'update')
        self.downloader = Downloader(self.checker.transport, staging_root)
        self._ready_path = None
        self.active = False
        self.context = None
        self._generation = 0
        self._last_attempt = None
        self.installer = installer
        self.callbacks = callbacks
        self.context_policy = context_policy
        self._install_token = None
        self._install_pending = False
        self._install_armed = False
        self._install_deadline = None
        self._install_generation = 0
        self.results = results
        self.notifier = notifier
        self._install_ticket = None
        self._previous_result_stamp = None
        self._receipt_error_since = None
        self._cancel_requested = False
        self._restart_requested = False
        self._notified = set()
        self._previous_reports = []
        self.file_work = file_work
        self._prepare_permit = None
        self._prepare_active = False
        self._receipt_busy = False
        self._receipt_proof = None
        self._recovery_busy = False

    def start(self):
        if self.active:
            return
        if self.api is None:
            from Driftkings.settings.panel import settings
            self.api = settings
        if self.safe_spaces is None:
            from skeletons.gui.app_loader import GuiGlobalSpaceID
            self.safe_spaces = (GuiGlobalSpaceID.LOGIN, GuiGlobalSpaceID.LOBBY)
        if self._runtime_transport:
            from Driftkings.core.updater.https_transport import runtime_transport
            self.checker.transport = runtime_transport()
            self.downloader.transport = self.checker.transport
            from Driftkings.core.updater.installer import Installer
            from Driftkings.core.callbacks import callbacks
            self.installer = self.installer or Installer(os.getcwd())
            self.callbacks = self.callbacks or callbacks
            from Driftkings.core.updater.file_work import FileWork
            if self.file_work is None or self.file_work.closed:
                self.file_work = FileWork(self.callbacks)
            from Driftkings.core.updater.results import Results
            self.results = self.results or Results(self.installer.root)
            if self.notifier is None:
                self.notifier = self._runtime_notify
            try:
                from Driftkings.core.updater.context import runtime_context
                self.context_policy = self.context_policy or runtime_context()
            except Exception:
                LOG.warning('Install context unavailable; scheduling disabled')
        if self.file_work is not None and self.file_work.closed:
            from Driftkings.core.updater.file_work import FileWork
            self.file_work = FileWork(self.callbacks)
        self.active = True
        subscribe = getattr(self.context_policy, 'subscribe', None)
        if callable(subscribe):
            try:
                subscribe(self._on_install_context_changed)
            except Exception:
                LOG.warning('Install context events unavailable; scheduling disabled', exc_info=True)
                try:
                    self.context_policy.unsubscribe(self._on_install_context_changed)
                except Exception:
                    pass
                self.context_policy = None
        self.api.updater = self
        from Driftkings.settings.panel import core_page
        core_page.subscribe(self._preferences_changed)
        self._preferences_changed({})
        LOG.info('Starting updater; installed version %s', VERSION)
        if self.results is not None:
            client = getattr(self.api, 'client_version', None)
            if self.file_work is not None:
                try:
                    self.file_work.submit(lambda: self.results.scan(client), self._previous_results_received)
                except Exception as error:
                    self._previous_results_received(None, error)
            else:
                try:
                    self._previous_results_received(self.results.scan(client), None)
                except Exception as error:
                    self._previous_results_received(None, error)
        if self._install_armed:
            if self.installer.process.poll() is None:
                self._install_pending = True
                self.state.update(status=RESTART_REQUIRED, installScheduled=True)
                self._refresh_install_context()
                self._install_generation += 1
                self._schedule_install_poll(1.0)
                return
            self._install_armed = False
        self._recover_staging()

    def stop(self):
        if not self.active:
            return
        self.active = False
        if self._prepare_permit is not None:
            self._prepare_permit.clear()
        if self.file_work is not None:
            self.file_work.close()
        self._receipt_proof = None
        self._receipt_busy = self._prepare_active = self._recovery_busy = False
        self._install_generation += 1
        unsubscribe = getattr(self.context_policy, 'unsubscribe', None)
        if callable(unsubscribe):
            try:
                unsubscribe(self._on_install_context_changed)
            except Exception:
                LOG.warning('Install context cleanup failed', exc_info=True)
        if self._install_token is not None:
            self.callbacks.cancel(self._install_token)
            self._install_token = None
        # Confirmed intent survives normal Core shutdown; the helper must outlive
        # WoT. An unacknowledged preparation is cancelled, never left armed.
        if self._install_pending and not self._install_armed:
            self._cancel_helper()
        self._install_pending = False
        self.context = None
        self._generation += 1
        if not self._install_armed:
            self._ready_path = None
        self.checker.cancel()
        self.downloader.cancel()
        close = getattr(self.checker.transport, 'close', None)
        if callable(close):
            close()
        from Driftkings.settings.panel import core_page
        core_page.unsubscribe(self._preferences_changed)
        self.state.update(status=IDLE, canDownload=False, canCancel=False, downloadPercent=None,
                          canInstall=False, installScheduled=False, installBlocked=None, canRestart=False)
        if getattr(self.api, 'updater', None) is self:
            self.api.updater = None

    def _preferences_changed(self, changes):
        channel = self.api.get('dk.settings', 'updateChannel', 'stable')
        if channel != self.state.snapshot()['channel']:
            if self._install_pending or self._install_armed:
                # The staged version already has explicit consent. Preferences
                # for future checks cannot silently retarget a live helper.
                self.state.update(channel=channel)
                return
            self._ready_path = None
            self.downloader.cancel()
            self._generation += 1
            self.checker.cancel()
            self._last_attempt = None
            self.state.update(channel=channel, status=IDLE, latestVersion=None,
                              changelog=[], compatible=None, error=None, canDownload=False, canCancel=False,
                              downloadPercent=None, canInstall=False, installBlocked=None, installScheduled=False)
            self._recover_staging()

    def onContextEntered(self, space):
        self.context = space
        self._refresh_install_context()
        self._deliver_notifications()
        if self.active and space in self.safe_spaces:
            self.check()

    def onContextLeft(self, space):
        if space == self.context:
            self.context = None
            self._refresh_install_context()

    def check(self, manual=False):
        if (not self.active or self._recovery_busy or self.downloader.busy or getattr(self.checker.transport, 'busy', False) or
                self._install_pending or self._install_armed or
                self.state.snapshot()['status'] in (CHECKING, READY, INSTALLING, RESTART_REQUIRED)):
            return False
        now = self.clock()
        if not manual:
            if not self.api.get('dk.settings', 'autoCheckUpdates', True):
                return False
            if self._last_attempt is not None and 0 <= now - self._last_attempt < INTERVAL:
                return False
            if not getattr(self.checker.transport, 'available', True):
                return False
        self._last_attempt = now
        self._generation += 1
        generation = self._generation
        channel = self.api.get('dk.settings', 'updateChannel', 'stable')
        self.state.update(status=CHECKING, channel=channel, lastCheck=now, error=None, canDownload=False)
        if not self.active or generation != self._generation:
            return False
        LOG.info('Checking for updates')
        def completed(result, error):
            if not self.active or generation != self._generation:
                return
            if error:
                LOG.warning('Update check failed: %s', error)
                self.state.update(status=ERROR, error=error)
            else:
                can_download = bool(result['latestVersion'] and result['compatible'] and
                                    getattr(self.downloader.transport, 'available', True) and
                                    callable(getattr(self.downloader.transport, 'stream', None)))
                self.state.update(status=AVAILABLE if result['latestVersion'] else IDLE, error=None,
                                  canDownload=can_download, **result)
                self._deliver_notifications()
        try:
            return self.checker.check(VERSION, channel, getattr(self.api, 'client_version', None), completed)
        except Exception:
            completed(None, 'checkError')
            return False

    def download(self):
        manifest = self.checker.selected_manifest
        if (not self.active or self.downloader.busy or not self.state.snapshot()['canDownload'] or
                self.state.snapshot()['status'] not in (AVAILABLE, ERROR) or manifest is None or
                not manifest.compatible(getattr(self.api, 'client_version', None)) or
                not manifest.version.allowed(self.api.get('dk.settings', 'updateChannel', 'stable'))):
            return False
        self._generation += 1
        generation = self._generation
        self.state.update(status=DOWNLOADING, error=None, downloadPercent=0,
                          canDownload=False, canCancel=True)
        if not self.active or generation != self._generation:
            return False
        LOG.info('Download started')
        def progress(kind, value):
            if not self.active or generation != self._generation:
                return
            if kind == 'verifying':
                self.state.update(status=VERIFYING, downloadPercent=100)
            elif kind == 'bytes':
                self.state.update(downloadPercent=min(100, int(value * 100 // manifest.size)))
        def completed(path, error):
            if not self.active or generation != self._generation:
                return
            if error:
                if error != 'cancelled':
                    LOG.error('Update download failed: %s', error)
                self.state.update(status=AVAILABLE if error == 'cancelled' else ERROR,
                                  error=None if error == 'cancelled' else error, canDownload=True,
                                  canCancel=False, downloadPercent=None)
            else:
                self._ready_path = path
                LOG.info('Hash verified; update staged')
                self.state.update(status=READY, error=None, canDownload=False,
                                  canCancel=False, downloadPercent=100)
                self._refresh_install_context()
        return self.downloader.start(manifest, completed, progress)

    def cancel_download(self):
        if not self.active:
            return False
        if self.state.snapshot()['status'] == DOWNLOADING and not self.downloader.busy:
            self._generation += 1
            self.state.update(status=AVAILABLE, canDownload=True, canCancel=False, downloadPercent=None)
            return True
        cancelled = self.downloader.cancel()
        if cancelled:
            self.state.update(canCancel=False)
        return cancelled

    def _blocked_reason(self):
        if not self.active or self.installer is None or self.callbacks is None or self.context_policy is None:
            return 'unknownContext'
        try:
            return self.context_policy.blocked_reason(self.context)
        except Exception:
            return 'unknownContext'

    def _safe_install_context(self):
        return self._blocked_reason() is None

    def _on_install_context_changed(self, *args, **kwargs):
        if self.active:
            self._refresh_install_context()
            self._deliver_notifications()

    def _refresh_install_context(self):
        if self._prepare_permit is not None:
            if self._safe_install_context(): self._prepare_permit.set()
            else: self._prepare_permit.clear()
        ready = bool(self._ready_path and not self._install_pending and not self._install_armed)
        reason = self._blocked_reason() if ready or self._install_armed else None
        self.state.update(canInstall=ready and reason is None, installBlocked=reason,
                          canRestart=self._install_armed and reason is None and self.restart_ready())

    def _recover_staging(self):
        if self.installer is None or not self.active or self._install_pending or self._install_armed:
            return
        if self.file_work is not None:
            return self._recover_staging_async()
        try:
            path = self.installer.recover_ready(getattr(self.api, 'client_version', None),
                                                self.api.get('dk.settings', 'updateChannel', 'stable'))
            if path:
                manifest = self.installer.validate_stage(path, getattr(self.api, 'client_version', None),
                                                          self.api.get('dk.settings', 'updateChannel', 'stable'))
                self._ready_path = path
                self.checker.selected_manifest = manifest
                self.state.update(status=READY, latestVersion=manifest.version.text,
                                  changelog=list(manifest.changelog), compatible=True, error=None,
                                  canDownload=False, canCancel=False, downloadPercent=100)
                LOG.info('Recovered verified update staging')
            self._refresh_install_context()
        except Exception:
            LOG.warning('Update staging recovery failed', exc_info=True)

    def schedule_install(self):
        """Explicit backend action for Phase 7. No automatic install or restart."""
        if (not self._ready_path or self._install_pending or self._install_armed or
                self.state.snapshot()['status'] not in (READY, ERROR) or not self._safe_install_context()):
            self._refresh_install_context()
            return False
        self._install_pending = True
        self._install_generation += 1
        self._cancel_requested = False
        self._restart_requested = False
        self._receipt_error_since = None
        self._receipt_proof = None
        self.state.update(status=INSTALLING, error=None, canInstall=False, installBlocked=None,
                          cancellingInstall=False, restartDeferred=False)
        LOG.info('Install preparation requested')
        if not self.active or not self._safe_install_context():
            self._install_pending = False
            if self.active:
                self.state.update(status=READY)
                self._refresh_install_context()
            return False
        if self.file_work is not None:
            return self._prepare_install_async()
        try:
            ticket = os.path.join(os.path.dirname(self._ready_path), 'install.json')
            self._previous_result_stamp = self.results.result_stamp(self._ready_path) if self.results is not None else None
            action = self.installer.resume if os.path.lexists(ticket) else self.installer.schedule
            started = action(self._ready_path, getattr(self.api, 'client_version', None),
                             self.api.get('dk.settings', 'updateChannel', 'stable'), self._safe_install_context)
            if not started:
                self._install_pending = False
                self.state.update(status=READY)
                self._refresh_install_context()
                return False
            self._install_ticket = self.results.ticket(self._ready_path) if self.results is not None else None
            LOG.info('Installer launched')
            self._install_deadline = self.clock() + 15.0
            self._schedule_install_poll(0.25)
            return True
        except Exception:
            LOG.exception('Install preparation failed')
            self._install_failed('installPreparationError')
            return False

    def _cancel_helper(self):
        if self.installer is None:
            return
        try:
            self.installer.cancel(self._ready_path)
        except Exception:
            LOG.warning('Could not cancel installer preparation', exc_info=True)

    def _install_failed(self, error):
        self._install_generation += 1
        self._receipt_proof = None
        self._cancel_helper()
        self._install_pending = False
        self._install_armed = False
        self._cancel_requested = False
        LOG.error('Update installation failed: %s', error)
        if self.active:
            self.state.update(status=ERROR, error=error, installScheduled=False, canInstall=False,
                              cancellingInstall=False)
            self._refresh_install_context()

    def _schedule_install_poll(self, delay):
        generation = self._install_generation
        self._install_token = self.callbacks.schedule(delay, lambda: self._poll_install(generation))

    def _previous_results_received(self, reports, error):
        if not self.active:
            return
        if error is not None:
            LOG.warning('Previous update result inspection failed: %s', error)
            return
        self._previous_reports = reports
        if reports:
            report = reports[-1]
            self.state.update(lastInstallResult={key: report[key] for key in ('status', 'version', 'error')})
            LOG.info('Previous update result detected: %s (%s)', report['status'], report['error'])
            self._deliver_notifications()

    def _recover_staging_async(self):
        if self._recovery_busy:
            return
        self._recovery_busy = True
        generation = self._generation
        client = getattr(self.api, 'client_version', None)
        channel = self.api.get('dk.settings', 'updateChannel', 'stable')
        def task():
            path = self.installer.recover_ready(client, channel)
            return (path, self.installer.validate_stage(path, client, channel) if path else None)
        def completed(value, error):
            self._recovery_busy = False
            if not self.active or self._install_pending or self._install_armed:
                return
            if generation != self._generation:
                self._recover_staging()
                return
            if error is not None:
                LOG.warning('Update staging recovery failed: %s', error)
            elif value[0]:
                path, manifest = value
                self._ready_path = path
                self.checker.selected_manifest = manifest
                self.state.update(status=READY, latestVersion=manifest.version.text,
                                  changelog=list(manifest.changelog), compatible=True, error=None,
                                  canDownload=False, canCancel=False, downloadPercent=100)
                LOG.info('Recovered verified update staging')
            self._refresh_install_context()
            if self.context in self.safe_spaces:
                self.check()
        try:
            self.file_work.submit(task, completed)
        except Exception:
            self._recovery_busy = False
            LOG.exception('Could not queue staging recovery')

    def _prepare_install_async(self):
        generation = self._install_generation
        ready = self._ready_path
        client = getattr(self.api, 'client_version', None)
        channel = self.api.get('dk.settings', 'updateChannel', 'stable')
        permit = threading.Event()
        permit.set()
        self._prepare_permit = permit
        self._prepare_active = True
        try:
            resources = self.installer.resources()
            def task():
                previous = self.results.result_stamp(ready) if self.results is not None else None
                job = self.installer.prepare_install(ready, client, channel, permit.is_set, resources)
                try:
                    ticket = self.results.ticket(ready) if self.results is not None and job is not None else None
                    return dict(job=job, previous=previous, ticket=ticket)
                except Exception:
                    self.installer.discard_preparation(job)
                    raise
            def cleanup(value):
                self.installer.discard_preparation(value['job'])
            def completed(value, error):
                self._prepare_active = False
                self._prepare_permit = None
                if not self.active or generation != self._install_generation:
                    if value is not None: cleanup(value)
                    return
                if error is not None:
                    LOG.error('Background install preparation failed: %s', error)
                    self._install_failed('installPreparationError')
                    return
                if self._cancel_requested or not self._safe_install_context():
                    cleanup(value)
                    cancelled = self._cancel_requested
                    self._install_pending = self._cancel_requested = False
                    self._install_generation += 1
                    changes = dict(status=READY, cancellingInstall=False, installScheduled=False)
                    if cancelled:
                        changes['lastInstallResult'] = dict(status='cancelled', version=self.state.snapshot()['latestVersion'], error=None)
                    self.state.update(**changes)
                    self._refresh_install_context()
                    LOG.info('Preparation discarded before any native helper launch')
                    return
                try:
                    self._previous_result_stamp = value['previous']
                    self._install_ticket = value['ticket']
                    if not self.installer.launch_prepared(value['job'], self._safe_install_context):
                        self._install_pending = False
                        self.state.update(status=READY)
                        self._refresh_install_context()
                        return
                    LOG.info('Installer launched after background validation')
                    self._install_deadline = self.clock() + 15.0
                    self._schedule_install_poll(0.25)
                except Exception:
                    LOG.exception('Prepared installer launch failed')
                    self._install_failed('installPreparationError')
            self.file_work.submit(task, completed, cleanup)
            return True
        except Exception:
            self._prepare_active = False
            permit.clear()
            self._prepare_permit = None
            LOG.exception('Could not queue install preparation')
            self._install_failed('installPreparationError')
            return False

    def _poll_install_async(self, generation):
        if self._receipt_busy:
            return
        self._receipt_busy = True
        ready = self._ready_path
        cancelled = self._cancel_requested
        client = getattr(self.api, 'client_version', None)
        channel = self.api.get('dk.settings', 'updateChannel', 'stable')
        def task():
            before = self.results.proof_signature(ready) if self.results is not None else None
            result = self.installer.result(ready)
            ticket = self.results.ticket(ready) if self.results is not None else None
            stamp = self.results.result_stamp(ready) if self.results is not None else None
            signature = self.results.proof_signature(ready) if self.results is not None else None
            if before != signature:
                raise OSError('Receipt changed during background validation')
            if stamp is not None and result is not None:
                from Driftkings.core.updater.results import fingerprint
                if stamp[0] != fingerprint(result):
                    raise OSError('Receipt content changed during background validation')
            valid = None
            if cancelled and isinstance(result, dict) and result.get('status') == 'cancelled':
                try:
                    self.installer.validate_stage(ready, client, channel)
                    valid = True
                except Exception:
                    valid = False
            return dict(result=result, ticket=ticket, stamp=stamp, signature=signature, stageValid=valid)
        def completed(value, error):
            self._receipt_busy = False
            self._accept_install_probe(generation, value, error)
        try:
            self.file_work.submit(task, completed)
        except Exception as error:
            self._receipt_busy = False
            self._accept_install_probe(generation, None, error)

    def _poll_install(self, generation):
        if generation != self._install_generation:
            return
        self._install_token = None
        if not self.active or not self._install_pending:
            return
        if self.file_work is not None:
            return self._poll_install_async(generation)
        return self._accept_install_probe(generation)

    def _accept_install_probe(self, generation, probe=None, error=None):
        if generation != self._install_generation or not self.active or not self._install_pending:
            return
        try:
            if error is not None:
                raise error
            if probe is not None and self.results is not None:
                if probe['signature'] != self.results.proof_signature(self._ready_path):
                    raise OSError('Receipt changed before client delivery')
            process = self.installer.process
            result = probe['result'] if probe is not None else self.installer.result(self._ready_path)
            # A previous helper's result is never acknowledgement for this PID.
            matching = (isinstance(result, dict) and set(result) == set(('schema', 'status', 'error', 'helperPid')) and
                        type(result.get('schema')) is int and result['schema'] == 1 and
                        type(result.get('helperPid')) is int and result['helperPid'] == process.pid)
            ticket = probe['ticket'] if probe is not None else (self.results.ticket(self._ready_path) if self.results is not None else None)
            if self.results is not None and ticket != self._install_ticket:
                self._install_failed('installTicketChanged')
                return
            stamp = probe['stamp'] if probe is not None else (self.results.result_stamp(self._ready_path) if self.results is not None else None)
            if self.results is not None and stamp == self._previous_result_stamp:
                matching = False
            if probe is not None:
                self._receipt_proof = dict(probe, checkedAt=self.clock()) if matching else None
            if matching and result.get('status') == 'error':
                LOG.error('Native installer rejected operation: %s', result.get('error'))
            if self._cancel_requested:
                if matching and result.get('status') == 'cancelled' and process.poll() == 3:
                    if probe is not None and probe['stageValid'] is None:
                        self._schedule_install_poll(0.05)
                        return
                    valid = True
                    try:
                        if probe is not None:
                            valid = probe['stageValid']
                        else:
                            self.installer.validate_stage(self._ready_path, getattr(self.api, 'client_version', None),
                                                          self.api.get('dk.settings', 'updateChannel', 'stable'))
                    except Exception:
                        valid = False
                        LOG.warning('Cancelled update staging is not eligible for reuse', exc_info=True)
                    self._install_generation += 1
                    self._install_pending = self._install_armed = self._cancel_requested = False
                    manifest = self.checker.selected_manifest
                    can_download = bool(not valid and manifest is not None and
                                        manifest.compatible(getattr(self.api, 'client_version', None)) and
                                        manifest.version.allowed(self.api.get('dk.settings', 'updateChannel', 'stable')))
                    if not valid:
                        self._ready_path = None
                    self.state.update(status=READY if valid else AVAILABLE, canDownload=can_download,
                                      installScheduled=False, cancellingInstall=False,
                                      error=None, lastInstallResult=dict(status='cancelled',
                                                                       version=self.state.snapshot()['latestVersion'], error=None))
                    LOG.info('Install cancelled')
                    self._refresh_install_context()
                    return
                if process.poll() is not None or self.clock() >= self._install_deadline:
                    self._install_failed('installCancelUnconfirmed')
                    return
                self._schedule_install_poll(0.25)
                return
            if process.poll() is not None:
                self._install_failed('installHelperExited')
                return
            if not self._install_armed:
                if not self._safe_install_context():
                    self._install_failed('unsafeContext')
                    return
                if matching and result.get('status') == 'prepared':
                    self._install_armed = True
                    self.state.update(status=RESTART_REQUIRED, installScheduled=True, canInstall=False)
                    self._refresh_install_context()
                    LOG.info('Install scheduled; waiting for WoT process exit')
                    LOG.info('Helper prepared')
                elif matching and result.get('status') == 'error':
                    self._install_failed('installHelperError')
                    return
                elif self.clock() >= self._install_deadline:
                    self._install_failed('installHelperTimeout')
                    return
            if self.active and self._install_pending and generation == self._install_generation:
                self._receipt_error_since = None
                self._schedule_install_poll(1.0 if self._install_armed else 0.25)
        except (IOError, OSError):
            # Windows replacement/sharing can transiently deny a receipt read.
            # Never infer prepared/cancelled; retry only within a bounded window.
            if self._receipt_error_since is None:
                self._receipt_error_since = self.clock()
            expired = self.clock() - self._receipt_error_since >= 15.0
            if not self._install_armed and self.clock() >= self._install_deadline:
                expired = True
            if expired:
                LOG.exception('Install receipt remained unavailable')
                self._install_failed('installMonitorError')
            elif self.active and self._install_pending and generation == self._install_generation:
                self._schedule_install_poll(0.25)
        except Exception:
            LOG.exception('Install monitor failed')
            self._install_failed('installMonitorError')

    def cancel_install(self):
        if not self.active or not self._install_pending or self._cancel_requested or self._restart_requested:
            return False
        try:
            self._receipt_proof = None
            if self._prepare_active:
                self._cancel_requested = True
                if self._prepare_permit is not None: self._prepare_permit.clear()
                self.state.update(cancellingInstall=True, canInstall=False, canRestart=False)
                return True
            self.installer.cancel(self._ready_path)
            self._cancel_requested = True
            self._install_deadline = self.clock() + 15.0
            self.state.update(cancellingInstall=True, canInstall=False, canRestart=False)
            return True
        except Exception:
            LOG.exception('Install cancellation failed')
            self._install_failed('installCancelError')
            return False

    def restart_ready(self):
        if (not self.active or not self._install_armed or self._cancel_requested or self._restart_requested or
                not self.state.snapshot()['installScheduled'] or not self._safe_install_context()):
            return False
        try:
            if self.installer.process.poll() is not None:
                return False
            if self.file_work is not None:
                proof = self._receipt_proof
                if proof is None or not 0 <= self.clock() - proof['checkedAt'] <= 5.0:
                    return False
                if self.results is not None and proof['signature'] != self.results.proof_signature(self._ready_path):
                    return False
                result = proof['result']
                return (result.get('status') == 'prepared' and result.get('helperPid') == self.installer.process.pid and
                        proof['ticket'] == self._install_ticket and proof['stamp'] != self._previous_result_stamp)
            result = self.installer.result(self._ready_path)
            if (not isinstance(result, dict) or type(result.get('schema')) is not int or result['schema'] != 1 or
                    result.get('status') != 'prepared' or result.get('helperPid') != self.installer.process.pid):
                return False
            if self.results is not None and self.results.ticket(self._ready_path) != self._install_ticket:
                return False
            if self.results is not None and self.results.result_stamp(self._ready_path) == self._previous_result_stamp:
                return False
            return True
        except Exception:
            return False

    def claim_restart(self):
        if not self.restart_ready():
            return False
        self._restart_requested = True
        self.state.update(canRestart=False)
        if not self._safe_install_context():
            self._restart_requested = False
            return False
        LOG.info('Restart requested through existing Settings flow')
        return True

    def defer_restart(self):
        if not self.active or not self._install_armed or self._cancel_requested:
            return False
        self.state.update(restartDeferred=True)
        LOG.info('Restart deferred')
        return True

    def _runtime_notify(self, key, version):
        from gui import SystemMessages
        text = self.api.strings.get(key, key).format(version=version or '')
        SystemMessages.pushMessage(text, type=SystemMessages.SM_TYPE.Information)

    def _deliver_notifications(self):
        # LOGIN checks can queue a notice; deliver only after a confirmed lobby.
        if not self.active or not self._safe_install_context():
            return
        snapshot = self.state.snapshot()
        if snapshot['latestVersion'] and snapshot['compatible'] and snapshot['status'] == AVAILABLE:
            identity = ('available', snapshot['latestVersion'])
            if identity not in self._notified and self.notifier is not None:
                try:
                    self.notifier('updates.availableNotice', snapshot['latestVersion'])
                    self._notified.add(identity)
                except Exception:
                    LOG.warning('Update notification unavailable')
        for report in list(self._previous_reports):
            identity = ('result', report['fingerprint'])
            if identity in self._notified or self.notifier is None:
                continue
            try:
                self.notifier('updates.result.' + report['status'], report['version'])
                self._notified.add(identity)
                if self.file_work is not None:
                    def acknowledged(value, error, report=report):
                        if error is not None:
                            LOG.warning('Update notification receipt failed: %s', error)
                        elif report in self._previous_reports:
                            self._previous_reports.remove(report)
                    self.file_work.submit(lambda report=report: self.results.acknowledge(report), acknowledged)
                else:
                    self.results.acknowledge(report)
                    self._previous_reports.remove(report)
                LOG.info('Update %s: %s', report['status'], report['error'])
            except Exception:
                LOG.warning('Update result notification/receipt failed', exc_info=True)
