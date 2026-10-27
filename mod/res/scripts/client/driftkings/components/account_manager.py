# -*- coding: utf-8 -*-
"""Account persistence and native login lifecycle; presentation is Gameface."""
import base64
import json
import os
import weakref
import zlib

import BigWorld
from external_strings_utils import unicode_from_utf8
from helpers import getClientLanguage
from predefined_hosts import g_preDefinedHosts
from realm import CURRENT_REALM
from skeletons.gui.app_loader import GuiGlobalSpaceID

from driftkings._constants import GLOBAL, HANGAR_PREFERENCES
from driftkings.common.utils import events
from driftkings.common.utils.filesystem import atomicWrite, recoverFile
from driftkings.core.accounts import AccountError, AccountService
from driftkings.core.callbacks import callback, cancelCallback
from driftkings.core.hooks import on_event
from driftkings.i18n import catalog
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.settings.settings_data import defaults

from driftkings.flash.lobby.login import fill_credentials, install_login_hooks, launcher_position, prepare_login

LOG = get_logger('Driftkings.AccountManager')


class AccountsConfiguration(object):
    """Use hangar-owned settings without registering a separate settings page."""
    @property
    def data(self):
        try:
            settings = settings_service.getComponentDict(HANGAR_PREFERENCES)
        except KeyError:
            # Login can initialize before the hangar settings component.
            settings = defaults(HANGAR_PREFERENCES.NAME)
        return settings['accountManager']

    @property
    def i18n(self):
        return catalog.section('account_manager', str(getClientLanguage()).lower())


config = AccountsConfiguration()


def getPreferencesDir():
    path = unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1]
    return os.path.normpath(os.path.dirname(path))


class UserAccounts(object):
    def __init__(self):
        self.path = os.path.join(getPreferencesDir(), 'driftkings', 'accounts.manager')
        self.accounts = []
        self.read_error = False
        if os.path.isfile(self.path) or os.path.isfile(self.path + '.previous'):
            self.renew_accounts()

    def renew_accounts(self):
        try:
            recoverFile(self.path)
            with open(self.path, 'rb') as stream:
                raw = stream.read()
            if not raw:
                self.accounts = []
                self.read_error = False
                return
            try:
                decoded = zlib.decompress(base64.b64decode(BigWorld.wg_ucpdata(raw)))
                accounts = json.loads(decoded.decode('utf-8'))
            except Exception:
                accounts = json.loads(raw.decode('utf-8-sig'))
            if not isinstance(accounts, list) or any(not isinstance(item, dict) or
                    not all(key in item for key in ('id', 'title', 'email', 'password', 'cluster')) for item in accounts):
                raise ValueError('Invalid account records')
            self.accounts = accounts
            self.read_error = False
        except Exception as error:
            self.read_error = True
            LOG.error('Could not read accounts.manager (%s); existing file preserved', type(error).__name__)

    def write_accounts(self):
        if self.read_error:
            return False
        try:
            directory = os.path.dirname(self.path)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            payload = json.dumps(self.accounts).encode('utf-8')
            data = BigWorld.wg_cpdata(base64.b64encode(zlib.compress(payload)))
            atomicWrite(self.path, data)
            return True
        except Exception as error:
            LOG.error('Could not save accounts.manager (%s); credentials are not logged', type(error).__name__)
            return False


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
        if self.window is None and self.active and self.canLogin() and settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True):
            from driftkings.gameface.lobby.account_manager import AccountsWindow
            self.window = AccountsWindow(self)
            self.window.load()

    def canLogin(self):
        return self.login is not None and self.login() is not None and self.space == GuiGlobalSpaceID.LOGIN

    def launcherPosition(self):
        return launcher_position(self.login()) if self.canLogin() else None

    def useAccount(self, account_id, auto_enter):
        if not self.canLogin():
            raise AccountError('loginOnly', 'Select an account on the login screen.')
        login = self.login()
        if login.loginManager.isWgcSteam:
            raise AccountError('errorSteam', 'This client uses Steam. Select the account through Steam.')
        email, password, server, index = service.credentials(account_id)
        prepare_login(login, index)
        if auto_enter:
            login.onLogin(email, password, server, False)
        else:
            fill_credentials(login, email, password)

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
    BigWorld.wh_data = UserAccounts()
    service = AccountService(BigWorld.wh_data, BigWorld.wg_cpdata, BigWorld.wg_ucpdata, g_preDefinedHosts.shortList, CURRENT_REALM)
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
