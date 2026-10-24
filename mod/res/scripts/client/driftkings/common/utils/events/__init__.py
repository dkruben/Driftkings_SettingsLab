# -*- coding: utf-8 -*-
"""Shared lifecycle contracts with explicit before/after phases."""
from driftkings.core.signals import Signal


class _EventWrapper(object):
    def __init__(self):
        self.event = Signal()

    def __call__(self, handler):
        return self.event.connect(handler)


class ModEvent(object):
    def __init__(self):
        self.before = _EventWrapper()
        self.after = _EventWrapper()

    def __call__(self, original, *args, **kwargs):
        self.before.event(*args, **kwargs)
        result = original(*args, **kwargs)
        self.after.event(*args, **kwargs)
        return result


from driftkings.common.utils.events import lobby_view, login_view, player_avatar

PlayerAvatar, LobbyView, LoginView = player_avatar, lobby_view, login_view
