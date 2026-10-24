# -*- coding: utf-8 -*-
"""Updater service installation behavior; state is owned by UpdaterService."""
import os
import threading

from driftkings.core.updater.shared import LOG
from driftkings.core.updater.state import ERROR, INSTALLING, READY


class InstallMixin(object):
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
        self.state.update(status=INSTALLING, error=None, canInstall=False, installBlocked=None, cancellingInstall=False, restartDeferred=False)
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
            started = action(self._ready_path, getattr(self.api, 'client_version', None), self.api.get('dk.settings', 'updateChannel', 'stable'), self._safe_install_context)
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
            self.state.update(status=ERROR, error=error, installScheduled=False, canInstall=False, cancellingInstall=False)
            self._refresh_install_context()

    def _schedule_install_poll(self, delay):
        generation = self._install_generation
        self._install_token = self.callbacks.schedule(delay, lambda: self._poll_install(generation))

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
        try:
            if self.installer.request_restart(self._ready_path) is not True:
                self._restart_requested = False
                return False
            if not self._safe_install_context():
                self.revoke_restart()
                return False
        except Exception:
            LOG.exception('Could not prepare coordinated updater restart')
            self._restart_requested = False
            self._refresh_install_context()
            return False
        LOG.info('Coordinated restart requested; helper will reopen WoT after installation')
        return True

    def revoke_restart(self):
        """Undo consent when client shutdown fails; never leave a relaunch armed."""
        try:
            self.installer.revoke_restart(self._ready_path)
            self._restart_requested = False
            self._refresh_install_context()
        except Exception:
            LOG.exception('Could not revoke coordinated restart')
            self._install_failed('restartPreparationError')

    def defer_restart(self):
        if not self.active or not self._install_armed or self._cancel_requested:
            return False
        self.state.update(restartDeferred=True)
        LOG.info('Restart deferred')
        return True
