# -*- coding: utf-8 -*-
"""Exception boundary for callbacks that must not propagate into the client."""
from functools import wraps

from driftkings.logger import get_logger


def log_exceptions(function):
    @wraps(function)
    def guarded(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception:
            get_logger(function.__module__).exception(
                'Callback failed: %s', function.__name__)
            return None
    return guarded
