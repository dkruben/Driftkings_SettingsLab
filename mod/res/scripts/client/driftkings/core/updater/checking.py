# -*- coding: utf-8 -*-
"""Updater service checking behavior; state is owned by UpdaterService."""
from driftkings import VERSION
from driftkings._constants import SETTINGS_MOD_ID
from driftkings.core.updater.shared import INTERVAL, LOG
from driftkings.core.updater.state import AVAILABLE, CHECKING, ERROR, IDLE, INSTALLING, READY, RESTART_REQUIRED


class CheckMixin(object):
    def check(self, manual=False):
        if (not self.active or self._recovery_busy or self.downloader.busy or getattr(self.checker.transport, 'busy', False) or
                self._install_pending or self._install_armed or
                self.state.snapshot()['status'] in (CHECKING, READY, INSTALLING, RESTART_REQUIRED)):
            return False
        now = self.clock()
        if not manual:
            if not self.api.get(SETTINGS_MOD_ID, 'autoCheckUpdates', True):
                return False
            if self._last_attempt is not None and 0 <= now - self._last_attempt < INTERVAL:
                return False
            if not getattr(self.checker.transport, 'available', True):
                return False
        self._last_attempt = now
        self._generation += 1
        generation = self._generation
        channel = self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable')
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
