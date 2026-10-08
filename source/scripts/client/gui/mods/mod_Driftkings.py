# -*- coding: utf-8 -*-
"""Single game entry point; Core owns the application lifecycle."""
from Driftkings.core import Core

_core = Core()


def init():
    _core.start()


def fini():
    _core.stop()
