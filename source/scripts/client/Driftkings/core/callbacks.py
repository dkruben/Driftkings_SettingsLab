# -*- coding: utf-8 -*-
"""Delayed work owned by components, with battle and application cleanup."""
from functools import partial


class CallbackService(object):
    def __init__(self, backend=None):
        self.backend = backend
        self.pending = {}
        self.events = None

    def start(self):
        if self.events is not None:
            return
        from Driftkings.core.battle_events import battleEvents
        self.events = battleEvents
        self.events.ended.connect(self.endBattle)
        self.events.acquire(self)

    def schedule(self, delay, method, *args, **kwargs):
        if self.backend is None:
            import BigWorld
            self.backend = BigWorld
        function = method
        while isinstance(function, partial):
            function = function.func
        owner = getattr(function, '__module__', '')
        token = [None]
        def run():
            self.pending.pop(token[0], None)
            return method(*args, **kwargs)
        token[0] = self.backend.callback(delay, run)
        self.pending[token[0]] = owner
        return token[0]

    def cancel(self, token):
        if token in self.pending:
            self.pending.pop(token)
            return self.backend.cancelCallback(token)

    def cancelOwner(self, owner):
        for token, name in list(self.pending.items()):
            if name == owner:
                self.cancel(token)

    def endBattle(self):
        for token, owner in list(self.pending.items()):
            if owner.startswith('Driftkings.battle.'):
                self.cancel(token)

    def stop(self):
        if self.events is not None:
            self.events.ended.disconnect(self.endBattle)
            self.events.release(self)
            self.events = None
        for token in list(self.pending):
            self.cancel(token)


callbacks = CallbackService()
callback = callbacks.schedule
cancelCallback = callbacks.cancel
