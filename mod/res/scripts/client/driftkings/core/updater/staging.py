# -*- coding: utf-8 -*-
"""Updater service staging behavior; state is owned by UpdaterService."""
from driftkings._constants import SETTINGS_MOD_ID
from driftkings.core.updater.shared import LOG
from driftkings.core.updater.state import AVAILABLE, DOWNLOADING, ERROR, READY, VERIFYING


class StagingMixin(object):
    def download(self):
        manifest = self.checker.selected_manifest
        if (not self.active or self.downloader.busy or not self.state.snapshot()['canDownload'] or
                self.state.snapshot()['status'] not in (AVAILABLE, ERROR) or manifest is None or
                not manifest.compatible(getattr(self.api, 'client_version', None)) or
                not manifest.version.allowed(self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable'))):
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
                self.state.update(downloadPercent=min(100, int(value * 100 // manifest.payload_size)))
        def completed(path, error):
            if not self.active or generation != self._generation:
                return
            if error:
                if error != 'cancelled':
                    LOG.error('Update download failed: %s', error)
                self.state.update(status=AVAILABLE if error == 'cancelled' else ERROR, error=None if error == 'cancelled' else error, canDownload=True, canCancel=False, downloadPercent=None)
            else:
                self._ready_path = path
                LOG.info('Hash verified; update staged')
                self.state.update(status=READY, error=None, canDownload=False, canCancel=False, downloadPercent=100)
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

    def _recover_staging(self):
        if self.installer is None or not self.active or self._install_pending or self._install_armed:
            return
        if self.file_work is not None:
            return self._recover_staging_async()
        try:
            path = self.installer.recover_ready(getattr(self.api, 'client_version', None), self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable'))
            if path:
                manifest = self.installer.validate_stage(path, getattr(self.api, 'client_version', None), self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable'))
                self._ready_path = path
                self.checker.selected_manifest = manifest
                self.state.update(status=READY, latestVersion=manifest.version.text, changelog=list(manifest.changelog), compatible=True, error=None, canDownload=False, canCancel=False, downloadPercent=100)
                LOG.info('Recovered verified update staging')
            self._refresh_install_context()
        except Exception:
            LOG.warning('Update staging recovery failed', exc_info=True)

    def _recover_staging_async(self):
        if self._recovery_busy:
            return
        self._recovery_busy = True
        generation = self._generation
        client = getattr(self.api, 'client_version', None)
        channel = self.api.get(SETTINGS_MOD_ID, 'updateChannel', 'stable')
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
                self.state.update(status=READY, latestVersion=manifest.version.text, changelog=list(manifest.changelog), compatible=True, error=None, canDownload=False, canCancel=False, downloadPercent=100)
                LOG.info('Recovered verified update staging')
            self._refresh_install_context()
            if self.context in self.safe_spaces:
                self.check()
        try:
            self.file_work.submit(task, completed)
        except Exception:
            self._recovery_busy = False
            LOG.exception('Could not queue staging recovery')
