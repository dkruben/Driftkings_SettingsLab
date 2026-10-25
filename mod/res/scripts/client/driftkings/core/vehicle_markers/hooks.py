# -*- coding: utf-8 -*-
"""Reversible after-observers. Original calls and exceptions retain their behaviour."""


class Hooks(object):
    def __init__(self, logger):
        self.logger = logger
        self.entries = []

    def after(self, owner, name, observer):
        original = getattr(owner, name)
        original = getattr(original, 'im_func', original)
        logger = self.logger

        def wrapped(*args, **kwargs):
            result = original(*args, **kwargs)
            try:
                observer(result, *args, **kwargs)
            except Exception:
                logger.exception('[Driftkings.VehicleMarkers] Observer failed: %s', name)
            return result

        setattr(owner, name, wrapped)
        self.entries.append((owner, name, original, wrapped))

    def around(self, owner, name, handler):
        original = getattr(owner, name)
        original = getattr(original, 'im_func', original)

        def wrapped(*args, **kwargs):
            return handler(original, *args, **kwargs)

        setattr(owner, name, wrapped)
        self.entries.append((owner, name, original, wrapped))

    def clear(self):
        restored = retained = 0
        for owner, name, original, wrapped in reversed(self.entries):
            # Do not remove a hook subsequently installed by another mod.
            current = getattr(owner, name)
            if getattr(current, 'im_func', current) is wrapped:
                setattr(owner, name, original)
                restored += 1
            else:
                retained += 1
        self.entries = []
        return restored, retained
