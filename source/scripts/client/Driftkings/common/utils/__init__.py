# -*- coding: utf-8 -*-
import BigWorld

from . import events
from .abstract import *
from .chat import *
from .colorRatting import *
from .game import *
from .iter import *
from .logger import *
from .monkeypatch import *
from .wgUtils import *


def __import_delayed():
    from . import delayed
    import Driftkings.common
    import sys
    globals()['delayed'] = sys.modules['Driftkings.common.delayed'] = Driftkings.common.delayed = delayed


def initializeDelayedImports():
    # Called by the root package after its public functions are available.
    BigWorld.callback(0, __import_delayed)
