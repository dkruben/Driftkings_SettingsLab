# -*- coding: utf-8 -*-
"""Account profile persistence and native login lifecycle; presentation is Gameface.

Profiles hold a title, an e-mail and a server. Passwords are never stored or loaded by this component;
the player types them on the official World of Tanks login screen.
"""
import os
import weakref

import BigWorld
from external_strings_utils import unicode_from_utf8
from predefined_hosts import g_preDefinedHosts
from realm import CURRENT_REALM
from skeletons.gui.app_loader import GuiGlobalSpaceID

from driftkings._constants import GLOBAL
from driftkings.common.utils import events
from driftkings.core.account_profiles import FILE_NAME, LEGACY_NAME, ProfileFile
from driftkings.core.accounts import AccountError, AccountService
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.core.hooks import on_event
from driftkings.flash.lobby.login import fill_credentials, install_login_hooks, launcher_position, prepare_login
from driftkings.logger import get_logger
from driftkings.settings.definitions.components.account_manager import AccountManagerSettings
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.AccountManager')


config = AccountManagerSettings()


def getPreferencesDir():
    path = unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1]
    return os.path.normpath(os.path.dirname(path))


def profiles_path():
    return os.path.join(getPreferencesDir(), 'driftkings', FILE_NAME)


def legacy_path():
    # Only its existence is reported. The legacy file is never opened, read, copied or replaced.
    return os.path.join(getPreferencesDir(), 'driftkings', LEGACY_NAME)


class AccountsManagerController(object):
    def __init__(self):
        self.callbackID = None
        self.launcher = None
        self.window = None
        self.login = None
        self.active = False
        self.space = None
        on_event(events.LoginView.populate.after, self.loginPopulated)
        install_login_hooks(self)

    def loginPopulated(self, view, *args, **kwargs):
        self.login = weakref.ref(view)
        self.scheduleLauncher()

    def loginDisposed(self, original, view, *args, **kwargs):
        if self.login is not None and self.login() is view:
            self.login = None
            self.closeViews()
        return original(view, *args, **kwargs)

    def loginUpdated(self, original, view, *args, **kwargs):
        result = original(view, *args, **kwargs)
        if self.login is not None and self.login() is view:
            self.scheduleLauncher()
        return result

    def scheduleLauncher(self):
        if self.active and self.canLogin() and self.callbackID is None:
            self.callbackID = callback(0.0, self.showLauncher)

    def showLauncher(self):
        self.callbackID = None
        if not self.active or not settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True):
            return
        if not self.canLogin():
            return
        if self.launcher is None:
            from driftkings.gameface.lobby.account_manager import AccountsWindow
            self.launcher = AccountsWindow(self, launcher=True)
            self.launcher.load()
        else:
            self.launcher.content.refresh()

    def open(self):
        if (self.window is None and self.active and self.canLogin()
            and settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True)):
            from driftkings.gameface.lobby.account_manager import AccountsWindow
            self.window = AccountsWindow(self)
            self.window.load()

    # Abre a janela do gestor no hangar, a partir do painel, para editar os perfis guardados.
    def openManager(self):
        if self.window is None and self.active and self.space == GuiGlobalSpaceID.LOBBY:
            from driftkings.gameface.lobby.account_manager import AccountsWindow
            self.window = AccountsWindow(self)
            self.window.load()

    def canLogin(self):
        return self.login is not None and self.login() is not None and self.space == GuiGlobalSpaceID.LOGIN

    def launcherPosition(self):
        return launcher_position(self.login()) if self.canLogin() else None

    def useAccount(self, account_id):
        """Pre-fills e-mail and server on the official login form. The player types the password there."""
        if not self.canLogin():
            raise AccountError('loginOnly', 'Select an account on the login screen.')
        login = self.login()
        if login.loginManager.isWgcSteam:
            raise AccountError('errorSteam', 'This client uses Steam. Select the account through Steam.')
        email, server, index = service.credentials(account_id)
        prepare_login(login, index)
        fill_credentials(login, email, '')

    # Cancela a abertura pendente e fecha as janelas do gestor.
    def closeViews(self):
        if self.callbackID is not None:
            cancelCallback(self.callbackID)
            self.callbackID = None
        for attribute in ('window', 'launcher'):
            window = getattr(self, attribute)
            setattr(self, attribute, None)
            if window is not None:
                window.destroy()


controller = AccountsManagerController()
service = None


def init():
    global service
    BigWorld.wh_data = ProfileFile(profiles_path(), legacy_path())
    service = AccountService(BigWorld.wh_data, g_preDefinedHosts.shortList, CURRENT_REALM)
    controller.active = True


def onContextEntered(spaceID):
    controller.space = spaceID
    if spaceID == GuiGlobalSpaceID.LOGIN:
        controller.scheduleLauncher()
    else:
        controller.closeViews()


def onContextLeft(spaceID):
    controller.space = None
    controller.closeViews()


def fini():
    controller.active = False
    controller.login = None
    controller.closeViews()
