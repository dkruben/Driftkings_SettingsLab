# -*- coding: utf-8 -*-
"""Compose updater responsibilities around one service-owned state."""
import os
import time

from driftkings.core.updater.checker import Checker
from driftkings.core.updater.checking import CheckMixin
from driftkings.core.updater.downloader import Downloader
from driftkings.core.updater.installation import InstallMixin
from driftkings.core.updater.lifecycle import LifecycleMixin
from driftkings.core.updater.receipts import ReceiptMixin
from driftkings.core.updater.staging import StagingMixin
from driftkings.core.updater.state import State
from driftkings.core.updater.transport import UnavailableTransport


class UpdaterService(LifecycleMixin, CheckMixin, StagingMixin, InstallMixin, ReceiptMixin):
    def __init__(self, api=None, transport=None, clock=None, safe_spaces=None, timeout=15.0, staging_root=None,
                 installer=None, callbacks=None, context_policy=None, results=None, notifier=None, file_work=None):
        self.api = api
        self.clock = clock or time.time
        self.safe_spaces = safe_spaces
        self.state = State()
        self.checker = Checker(transport or UnavailableTransport(), timeout)
        self._runtime_transport = transport is None and api is None
        if staging_root is None:
            from driftkings.core.cache import CONFIG_ROOT
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


# Retain the public class identity for reflection and existing importers.
UpdaterService.__module__ = 'driftkings.core.updater'
