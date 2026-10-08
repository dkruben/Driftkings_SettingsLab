# -*- coding: utf-8 -*-
from Event import SafeEvent, EventManager

_manager = EventManager()


class _EventWrapper(object):
    def __init__(self):
        self.event = SafeEvent(_manager)

    def __call__(self, handler):
        self.event += handler
        return handler


class ModEvent(object):
    def __init__(self):
        self.before = _EventWrapper()
        self.after = _EventWrapper()
        self._final = _EventWrapper()

    def __call__(self, func, *args, **kwargs):
        self.before.event(*args, **kwargs)
        result = func(*args, **kwargs)
        self.after.event(*args, **kwargs)
        self._final.event(*args, **kwargs)
        return result


from . import game, player_avatar, lobby_view, login_view  # noqa: E402
# Event namespaces retain their public names; source modules use snake_case.
PlayerAvatar, LobbyView, LoginView = player_avatar, lobby_view, login_view


@game.fini._final
def fini(*_, **__):
    _manager.clear()
