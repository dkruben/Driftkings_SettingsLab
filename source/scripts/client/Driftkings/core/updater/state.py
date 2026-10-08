# -*- coding: utf-8 -*-
"""Observable runtime snapshot. Never stored in configuration or profiles."""
import copy
import logging
from Driftkings import VERSION

IDLE = 'IDLE'
CHECKING = 'CHECKING'
AVAILABLE = 'AVAILABLE'
DOWNLOADING = 'DOWNLOADING'
VERIFYING = 'VERIFYING'
READY = 'READY'
INSTALLING = 'INSTALLING'
RESTART_REQUIRED = 'RESTART_REQUIRED'
ERROR = 'ERROR'
ACTIVE_STATES = frozenset((IDLE, CHECKING, AVAILABLE, DOWNLOADING, VERIFYING, READY, INSTALLING, RESTART_REQUIRED, ERROR))
LOG = logging.getLogger('Driftkings.Updater')


class State(object):
    def __init__(self, installed=VERSION):
        self._data = dict(installedVersion=installed, latestVersion=None, channel='stable',
                          status=IDLE, lastCheck=None, changelog=[], compatible=None, error=None,
                          downloadPercent=None, canDownload=False, canCancel=False,
                          canInstall=False, installBlocked=None, installScheduled=False,
                          cancellingInstall=False, restartDeferred=False, lastInstallResult=None, canRestart=False)
        self._listeners = []

    def snapshot(self):
        return copy.deepcopy(self._data)

    def subscribe(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def update(self, **changes):
        if set(changes) - set(self._data) or changes.get('status', self._data['status']) not in ACTIVE_STATES:
            raise ValueError('Invalid updater state')
        self._data.update(copy.deepcopy(changes))
        for callback in tuple(self._listeners):
            try:
                callback()
            except Exception:
                LOG.exception('Updater observer failed')
