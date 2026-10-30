# -*- coding: utf-8 -*-
"""Updater service lifecycle behavior; state is owned by UpdaterService."""
import os

from driftkings._constants import SETTINGS_MOD_ID
from driftkings import VERSION
from driftkings.core.updater.shared import LOG
from driftkings.core.updater.state import IDLE, RESTART_REQUIRED


class LifecycleMixin(object):
    def start(self):
        if self.active:
            return
        if self.api is None:
            from driftkings.settings.panel import settings
            self.api = settings
        if self.safe_spaces is None:
            from skeletons.gui.app_loader import GuiGlobalSpaceID
            self.safe_spaces = (GuiGlobalSpaceID.LOGIN, GuiGlobalSpaceID.LOBBY)
        if self._runtime_transport:
            from driftkings.core.updater.https_transport import runtime_transport
            self.checker.transport = runtime_transport()
            self.downloader.transport = self.checker.transport
            from driftkings.core.callbacks import callbacks
            from driftkings.core.updater.installer import Installer
            self.installer = self.installer or Installer(os.getcwd())
            from driftkings.core.updater import windows_files
            if os.name == 'nt':
                try:
                    windows_files.initialize(self.installer.resource_reader, self.installer.root)
                except Exception:
                    LOG.warning('Windows file validation unavailable; receipt operations fail closed', exc_info=True)
            self.callbacks = self.callbacks or callbacks
            from driftkings.core.updater.file_work import FileWork
            if self.file_work is None or self.file_work.closed:
                self.file_work = FileWork(self.callbacks)
            from driftkings.core.updater.results import Results
            self.results = self.results or Results(self.installer.root)
            if self.notifier is None:
                self.notifier = self._runtime_notify
            try:
                from driftkings.core.updater.context import runtime_context
                self.context_policy = self.context_policy or runtime_context()
            except Exception:
                LOG.warning('Install context unavailable; scheduling disabled')
        if self.file_work is not None and self.file_work.closed:
            from driftkings.core.updater.file_work import FileWork
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
                    LOG.debug('Install context unsubscribe failed during cleanup', exc_info=True)
                self.context_policy = None
        self.api.updater = self
        from driftkings.settings.panel import core_page
        core_page.subscribe(self._preferences_changed)
        self._preferences_changed({})
        LOG.info('Starting updater; installed version %s', VERSION)
        if self.results is not None:
            client = getattr(self.api, 'client_version', None)
            results = self.results
            def scan():
                # Prune first: removed folders are ones scan() skips or only warns about.
                try:
                    results.prune()
                except Exception:
                    LOG.warning('Update cache cleanup failed', exc_info=True)
                return results.scan(client)
            if self.file_work is not None:
                try:
                    self.file_work.submit(scan, self._previous_results_received)
                except Exception as error:
                    self._previous_results_received(None, error)
            else:
                try:
                    self._previous_results_received(scan(), None)
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
        from driftkings.settings.panel import core_page
        core_page.unsubscribe(self._preferences_changed)
        self.state.update(status=IDLE, canDownload=False, canCancel=False, downloadPercent=None,
                          canInstall=False, installScheduled=False, installBlocked=None, canRestart=False)
        if getattr(self.api, 'updater', None) is self:
            self.api.updater = None

    def _preferences_changed(self, changes):
        channel = self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable')
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
            self.state.update(channel=channel, status=IDLE, latestVersion=None, changelog=[], compatible=None, error=None, canDownload=False, canCancel=False, downloadPercent=None, canInstall=False, installBlocked=None, installScheduled=False)
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
        self.state.update(canInstall=ready and reason is None, installBlocked=reason, canRestart=self._install_armed and reason is None and self.restart_ready())
