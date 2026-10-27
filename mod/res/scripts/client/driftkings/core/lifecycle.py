# -*- coding: utf-8 -*-
"""Single producers for login and lobby view lifecycle notifications."""


class LifecycleService(object):
    def __init__(self):
        self.active = False

    def start(self):
        if self.active:
            return
        from driftkings.flash.lifecycle import install
        install(self)
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
