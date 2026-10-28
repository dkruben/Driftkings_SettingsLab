# -*- coding: utf-8 -*-
"""Delayed work owned by components, with battle and application cleanup."""
from functools import partial

from driftkings.core.diagnostics import diagnostics


class CallbackService(object):
    def __init__(self, backend=None):
        self.backend = backend
        self.pending = {}
        self.events = None

    def start(self):
        if self.events is not None:
            return
        from driftkings.core.battle_events import battleEvents
        self.events = battleEvents
        self.events.ended.connect(self.endBattle)
        try:
            self.events.acquire(self)
        except Exception:
            self.events.ended.disconnect(self.endBattle)
            self.events = None
            raise

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
            # Cancelled/completed registrations must not call a disposed owner,
            # including when the backend already queued the callable.
            if token[0] not in self.pending:
                return
            self.pending.pop(token[0], None)
            if diagnostics.enabled:
                return diagnostics.call('callback.' + owner + '.' + getattr(function, '__name__', 'handler'), method, *args, **kwargs)
            return method(*args, **kwargs)
        token[0] = self.backend.callback(delay, run)
        self.pending[token[0]] = owner
        if diagnostics.enabled:
            diagnostics.count('callback.' + owner + '.scheduled')
        return token[0]

    def cancel(self, token):
        if token in self.pending:
            owner = self.pending.pop(token)
            result = self.backend.cancelCallback(token)
            if diagnostics.enabled:
                diagnostics.count('callback.' + owner + '.cancelled')
            return result

    def snapshot(self):
        owners = {}
        for owner in list(self.pending.values()):
            owners[owner] = owners.get(owner, 0) + 1
        return dict(pending=len(self.pending), owners=owners)

    def cancelOwner(self, owner):
        for token, name in list(self.pending.items()):
            if name == owner:
                self.cancel(token)

    def endBattle(self):
        for token, owner in list(self.pending.items()):
            # Flash battle adapters share the arena lifetime of gameplay components.
            if owner.startswith(('driftkings.battle.', 'driftkings.flash.battle.')):
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
