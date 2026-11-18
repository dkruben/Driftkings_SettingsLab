# -*- coding: utf-8 -*-
"""Temporary HangarClock lifecycle diagnostics.

Disabled by default (ENABLED = False). When disabled nothing is installed and nothing is logged.
When enabled it only logs lifecycle events and state changes, never per second, and it never
interrupts the clock: every diagnostic callback is isolated. Remove this module and its calls in
gameface/lobby/main.py to retire the instrumentation.
"""
import time
import weakref

from driftkings.logger import get_logger

ENABLED = False

LOG = get_logger('driftkings.gameface.lobby.clock_diagnostics')
TAG = '[Driftkings][ClockDiag]'
# One identifier per client start, so logs from separate launches can be told apart.
SESSION = time.strftime('%Y%m%dT%H%M%S', time.localtime())

_sequence = [0]
_ids = weakref.WeakKeyDictionary()
_last = {}
_failed = [False]


def identify(instance, prefix):
    """Stable label (prefix#n) assigned once per live instance."""
    try:
        if instance not in _ids:
            _sequence[0] += 1
            _ids[instance] = _sequence[0]
        return '%s#%d' % (prefix, _ids[instance])
    except Exception:
        return prefix + '#?'


def changed(label, state):
    """True only when the observed state differs from the last logged state for this label."""
    if _last.get(label) == state:
        return False
    _last[label] = state
    return True


def forget(label):
    _last.pop(label, None)


def _report_failure(message):
    if not _failed[0]:
        _failed[0] = True
        LOG.exception('%s %s; diagnostics continue silently', TAG, message)


def emit(event, **fields):
    """Log one lifecycle event; a logging failure is reported once and never propagates."""
    if not ENABLED:
        return
    try:
        parts = ' '.join('%s=%s' % (key, fields[key]) for key in sorted(fields))
        LOG.info('%s %s %s', TAG, event, parts)
    except Exception:
        _report_failure('logging failed')


def guarded(function):
    """Run a diagnostic callback without ever raising into the game code."""
    def wrapper(*args, **kwargs):
        if not ENABLED:
            return None
        try:
            return function(*args, **kwargs)
        except Exception:
            _report_failure('callback failed')
            return None
    wrapper.__name__ = getattr(function, '__name__', 'diagnostic')
    return wrapper


def payload_summary(payload):
    """Non-sensitive card summary: visibility, prestige policy and format count only."""
    config = payload.get('config') or {}
    return dict(visible=config.get('visible'), hidePrestige=config.get('hidePrestige'),
                formats=len(config.get('formats') or []))


def mode_name():
    """Class name of the current prebattle entity (e.g. the Frontline or Onslaught entity). No account data."""
    from gui.prb_control.dispatcher import g_prbLoader
    dispatcher = g_prbLoader.getDispatcher() if g_prbLoader else None
    if dispatcher is None:
        return 'none'
    entity = dispatcher.getEntity()
    return type(entity).__name__ if entity is not None else 'none'


def install_lifecycle(RandomHangar):
    """Install the diagnostic overrides. Called only when ENABLED is True.

    main.py already observes _getChildComponents, _onShown, _onHidden and the ClockView lifecycle.
    This adds only RandomHangar._onLoading/_finalize, which own the PrebattleEvent.SWITCHED
    listener and make hangar creation and destruction visible.
    """
    from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
    from driftkings.core.hooks import override

    listeners = weakref.WeakKeyDictionary()
    emit('session.started', session=SESSION, state='active')

    def make_switch_handler(label):
        @guarded
        def on_switched(event=None):
            current = mode_name()
            if changed(label + '.mode', current):
                emit('mode.switched', hangar=label, mode=current)
        return on_switched

    @override(RandomHangar, '_onLoading')
    def hangar_loading(original, hangar, *args, **kwargs):
        result = original(hangar, *args, **kwargs)
        if ENABLED and hangar not in listeners:
            try:
                label = identify(hangar, 'RandomHangar')
                handler = make_switch_handler(label)
                g_eventBus.addListener(events.PrebattleEvent.SWITCHED, handler, scope=EVENT_BUS_SCOPE.LOBBY)
                listeners[hangar] = handler
                emit('hangar.loaded', hangar=label, mode=mode_name())
            except Exception:
                _report_failure('could not attach the mode listener')
        return result

    @override(RandomHangar, '_finalize')
    def hangar_finalize(original, hangar, *args, **kwargs):
        handler = listeners.pop(hangar, None)
        if handler is not None:
            label = identify(hangar, 'RandomHangar')
            try:
                g_eventBus.removeListener(events.PrebattleEvent.SWITCHED, handler, scope=EVENT_BUS_SCOPE.LOBBY)
            except Exception:
                _report_failure('could not remove the mode listener')
            forget(label + '.mode')
            emit('hangar.destroyed', hangar=label)
        return original(hangar, *args, **kwargs)
