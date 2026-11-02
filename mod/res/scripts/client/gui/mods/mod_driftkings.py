# -*- coding: utf-8 -*-
"""The game calls init/fini; importing this entry point creates no services."""
import logging

_core = None


def init():
    global _core
    if _core is not None:
        return
    from realm import CURRENT_REALM
    if CURRENT_REALM not in ('EU', 'NA', 'ASIA'):
        logging.getLogger('Driftkings.Loader').warning('Unsupported client realm: %s; Driftkings disabled',
                                                       CURRENT_REALM)
        return
    from driftkings.core import Core
    core = Core()
    _core = core
    try:
        core.start()
    except Exception:
        core.stop()
        _core = None
        logging.getLogger('Driftkings.Loader').exception('Driftkings startup failed')


def fini():
    global _core
    core, _core = _core, None
    if core is not None:
        core.stop()
