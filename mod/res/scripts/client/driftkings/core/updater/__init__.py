# -*- coding: utf-8 -*-
"""Public updater API; implementations live in responsibility-specific modules."""
# Retained public dependency exports; covered by the compatibility tests.
import logging
import os
import threading
import time

from driftkings.core.updater.checker import Checker
from driftkings.core.updater.downloader import Downloader
from driftkings.core.updater.service import UpdaterService
from driftkings.core.updater.shared import INTERVAL, LOG
from driftkings.core.updater.state import (AVAILABLE, CHECKING, DOWNLOADING, ERROR, IDLE, INSTALLING, READY,
                                           RESTART_REQUIRED, State, VERIFYING)
from driftkings.core.updater.transport import UnavailableTransport
