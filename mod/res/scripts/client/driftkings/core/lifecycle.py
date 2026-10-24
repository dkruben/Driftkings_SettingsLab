# -*- coding: utf-8 -*-
"""Single producers for login and lobby view lifecycle notifications."""
from driftkings.core.hooks import override


class LifecycleService(object):
    def __init__(self):
        self.active = False

    def start(self):
        if self.active:
            return
        from gui.Scaleform.daapi.view.lobby.LobbyView import LobbyView
        from gui.Scaleform.daapi.view.login.LoginView import LoginView
        override(LoginView, '_populate', self.loginPopulated)
        override(LobbyView, '_populate', self.lobbyPopulated)
        self.active = True

    def loginPopulated(self, original, *args, **kwargs):
        from driftkings.common.utils import events
        return events.LoginView.populate(original, *args, **kwargs)

    def lobbyPopulated(self, original, *args, **kwargs):
        from driftkings.common.utils import events
        return events.LobbyView.populate(original, *args, **kwargs)

    def stop(self):
        self.active = False


lifecycle = LifecycleService()
