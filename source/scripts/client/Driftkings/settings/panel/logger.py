# -*- coding: utf-8 -*-
"""[Driftkings.Settings] log channel; uses the client log when available, never logs secrets."""
import logging

CHANNEL = 'Driftkings.Settings'
_fallback = logging.getLogger(CHANNEL)
_state = {'debug': False}

try:
    import BigWorld
    _native = all(hasattr(BigWorld, name) for name in ('logInfo', 'logWarning', 'logError'))
except ImportError:
    BigWorld = None
    _native = False


def _text(message, args):
    if args:
        try:
            message = message % args
        except (TypeError, ValueError):
            message = message + ' ' + repr(args)
    return message


def set_debug(enabled):
    _state['debug'] = bool(enabled)


def debug_enabled():
    return _state['debug']


def info(message, *args):
    message = _text(message, args)
    if _native:
        BigWorld.logInfo(CHANNEL, message, None)
    else:
        _fallback.info('[%s] %s', CHANNEL, message)


def warning(message, *args):
    message = _text(message, args)
    if _native:
        BigWorld.logWarning(CHANNEL, message, None)
    else:
        _fallback.warning('[%s] %s', CHANNEL, message)


def error(message, *args):
    message = _text(message, args)
    if _native:
        BigWorld.logError(CHANNEL, message, None)
    else:
        _fallback.error('[%s] %s', CHANNEL, message)


def exception(message, *args):
    import traceback
    error('%s\n%s', _text(message, args), traceback.format_exc())


def debug(message, *args):
    if _state['debug']:
        info('[DEBUG] ' + message, *args)
