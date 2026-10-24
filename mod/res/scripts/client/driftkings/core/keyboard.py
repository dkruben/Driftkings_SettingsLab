# -*- coding: utf-8 -*-
"""Core-owned keyboard subscription for configuration hotkeys."""
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Keyboard')


class KeyboardService(object):
    def __init__(self, input_handler=None, blocked=None):
        self.handler = input_handler
        self.blocked = blocked or self.settingsOpen
        self.callbacks = []
        self.interface_callbacks = []
        self.active = False
        self.downBound = self.upBound = False

    @staticmethod
    def settingsOpen():
        from driftkings.settings.panel import settings
        from driftkings.settings.registry import registry
        return registry.isOpen or settings.window_open

    def subscribe(self, callback, interface=False):
        callbacks = self.interface_callbacks if interface else self.callbacks
        if callback not in callbacks:
            callbacks.append(callback)

    def unsubscribe(self, callback):
        for callbacks in (self.callbacks, self.interface_callbacks):
            if callback in callbacks:
                callbacks.remove(callback)

    def start(self):
        if self.active:
            return
        if self.handler is None:
            from gui import InputHandler
            self.handler = InputHandler.g_instance
        self.active = True
        try:
            self.handler.onKeyDown += self.onKey
            self.downBound = True
            self.handler.onKeyUp += self.onKey
            self.upBound = True
        except Exception:
            self.stop()
            raise

    def stop(self):
        if self.active:
            if self.downBound:
                self.handler.onKeyDown -= self.onKey
                self.downBound = False
            if self.upBound:
                self.handler.onKeyUp -= self.onKey
                self.upBound = False
            self.active = False
        self.callbacks[:] = []
        self.interface_callbacks[:] = []

    def onKey(self, event):
        if not self.active:
            return
        was_blocked = self.blocked()
        # UI listeners run first: opening settings must block gameplay immediately.
        for callback in tuple(self.interface_callbacks):
            if callback in self.interface_callbacks:
                self.dispatch(callback, event)
        if was_blocked or self.blocked():
            return
        for callback in tuple(self.callbacks):
            if callback in self.callbacks and not self.blocked():
                self.dispatch(callback, event)

    @staticmethod
    def dispatch(callback, event):
        try:
            callback(event)
        except Exception:
            LOG.exception('Hotkey handler failed')


keyboard = KeyboardService()
