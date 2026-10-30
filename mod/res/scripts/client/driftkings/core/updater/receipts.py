# -*- coding: utf-8 -*-
"""Updater service receipts behavior; state is owned by UpdaterService."""
from driftkings._constants import SETTINGS_MOD_ID
from driftkings.core.updater.shared import LOG
from driftkings.core.updater.state import AVAILABLE, READY, RESTART_REQUIRED


class ReceiptMixin(object):
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

    def _poll_install_async(self, generation):
        if self._receipt_busy:
            return
        self._receipt_busy = True
        ready = self._ready_path
        cancelled = self._cancel_requested
        client = getattr(self.api, 'client_version', None)
        channel = self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable')
        def task():
            before = self.results.proof_signature(ready) if self.results is not None else None
            result = self.installer.result(ready)
            ticket = self.results.ticket(ready) if self.results is not None else None
            stamp = self.results.result_stamp(ready) if self.results is not None else None
            signature = self.results.proof_signature(ready) if self.results is not None else None
            if before != signature:
                raise OSError('Receipt changed during background validation')
            if stamp is not None and result is not None:
                from driftkings.core.updater.results import fingerprint
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
            matching = (isinstance(result, dict) and set(result) == set(('schema', 'status', 'error', 'helperPid')) and type(result.get('schema')) is int and result['schema'] == 1 and type(result.get('helperPid')) is int and result['helperPid'] == process.pid)
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
                            self.installer.validate_stage(self._ready_path, getattr(self.api, 'client_version', None), self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable'))
                    except Exception:
                        valid = False
                        LOG.warning('Cancelled update staging is not eligible for reuse', exc_info=True)
                    self._install_generation += 1
                    self._install_pending = self._install_armed = self._cancel_requested = False
                    manifest = self.checker.selected_manifest
                    can_download = bool(not valid and manifest is not None and manifest.compatible(getattr(self.api, 'client_version', None)) and manifest.version.allowed(self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable')))
                    if not valid:
                        self._ready_path = None
                    self.state.update(status=READY if valid else AVAILABLE, canDownload=can_download, installScheduled=False, cancellingInstall=False, error=None, lastInstallResult=dict(status='cancelled', version=self.state.snapshot()['latestVersion'], error=None))
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
                if self._install_armed:
                    self._refresh_install_context()
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
