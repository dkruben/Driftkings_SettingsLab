# -*- coding: utf-8 -*-
"""Settings logging compatibility facade using the shared mod format."""
import sys

from driftkings.logger import get_logger

CHANNEL = 'Driftkings.Settings'
_fallback = get_logger(CHANNEL)
_state = {'debug': False}

def _location():
    frame = sys._getframe(2)
    return {
        'driftkings_filename': frame.f_code.co_filename.replace('\\', '/').rsplit('/', 1)[-1],
        'driftkings_lineno': frame.f_lineno}


def set_debug(enabled):
    _state['debug'] = bool(enabled)
    from driftkings.core.diagnostics import diagnostics
    diagnostics.reporter = lambda message: info('Performance: %s', message)
    diagnostics.configure(enabled)


def info(message, *args):
    _fallback.info(message, *args, extra=_location())


def warning(message, *args):
    _fallback.warning(message, *args, extra=_location())


def error(message, *args):
    _fallback.error(message, *args, extra=_location())


def exception(message, *args):
    _fallback.exception(message, *args, extra=_location())


def debug(message, *args):
    if _state['debug']:
        # Explicit panel debug mode remains visible at the client's INFO level.
        location = _location()
        location['driftkings_levelname'] = 'DEBUG'
        _fallback.info(message, *args, extra=location)
