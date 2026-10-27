# -*- coding: utf-8 -*-
"""Install native login/lobby presentation hooks for the shared lifecycle service."""
from driftkings.core.hooks import override


def install(service):
    from gui.Scaleform.daapi.view.lobby.LobbyView import LobbyView
    from gui.Scaleform.daapi.view.login.LoginView import LoginView
    override(LoginView, '_populate', service.loginPopulated)
    override(LobbyView, '_populate', service.lobbyPopulated)
