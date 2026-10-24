# -*- coding: utf-8 -*-
"""Isolated notifications: a failing consumer cannot prevent other consumers."""
from driftkings.core.diagnostics import diagnostics
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Events')


class Signal(object):
    def __init__(self):
        self.listeners = []

    def connect(self, callback):
        if callback not in self.listeners:
            self.listeners.append(callback)
        return callback

    def disconnect(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def emit(self, *args, **kwargs):
        for callback in tuple(self.listeners):
            if callback not in self.listeners:
                continue
            try:
                if diagnostics.enabled:
                    label = 'event.' + getattr(callback, '__module__', type(callback).__module__) + '.' + getattr(callback, '__name__', type(callback).__name__)
                    diagnostics.call(label, callback, *args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception:
                LOG.exception('Event handler failed: %s', getattr(callback, '__name__', type(callback).__name__))

    __call__ = emit

    def __iadd__(self, callback):
        self.connect(callback)
        return self

    def __isub__(self, callback):
        self.disconnect(callback)
        return self

    def __len__(self):
        return len(self.listeners)

    def clear(self):
        self.listeners[:] = []
