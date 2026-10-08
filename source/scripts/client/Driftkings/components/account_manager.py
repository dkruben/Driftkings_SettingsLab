# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL
from Driftkings.settings.service import settings_service
"""Account persistence and native login lifecycle; presentation is Gameface."""
import base64
import json
import logging
import os
import weakref
import zlib

import BigWorld
from gui import GUI_SETTINGS
from external_strings_utils import unicode_from_utf8
from gui.Scaleform.daapi.view.login.LoginView import LoginView
from gui.Scaleform.daapi.view.login.login_modes.wgc_mode import WgcMode
from predefined_hosts import g_preDefinedHosts
from skeletons.gui.app_loader import GuiGlobalSpaceID

from Driftkings.common.utils.filesystem import atomicWrite, recoverFile
from Driftkings.core.accounts import AccountService, AccountError
from Driftkings.core.callbacks import callback, cancelCallback
from Driftkings.core.hooks import override
from Driftkings.settings.templates.components.account_manager import AccountManagerSettings as ConfigsInterface

LOG = logging.getLogger('Driftkings.AccountManager')
config = ConfigsInterface()


def getPreferencesDir():
    path = unicode_from_utf8(BigWorld.wg_getPreferencesFilePath())[1]
    return os.path.normpath(os.path.dirname(path))


class UserAccounts(object):
    def __init__(self):
        self.path = os.path.join(getPreferencesDir(), 'Driftkings', 'accounts.manager')
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
        override(LoginView, '_populate', self.loginPopulated)
        override(LoginView, '_dispose', self.loginDisposed)
        override(LoginView, 'update', self.loginUpdated)

    def loginPopulated(self, original, view, *args, **kwargs):
        result = original(view, *args, **kwargs)
        self.login = weakref.ref(view)
        self.scheduleLauncher()
        return result

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
            from Driftkings.views.hangar.account_manager import AccountsWindow
            self.launcher = AccountsWindow(self, launcher=True)
            self.launcher.load()
        else:
            self.launcher.content.refresh()

    def open(self):
        if self.window is None and self.active and self.canLogin() and settings_service.getComponentDict(config).get(GLOBAL.ENABLED, True):
            from Driftkings.views.hangar.account_manager import AccountsWindow
            self.window = AccountsWindow(self)
            self.window.load()

    def canLogin(self):
        return self.login is not None and self.login() is not None and self.space == GuiGlobalSpaceID.LOGIN

    def launcherPosition(self):
        """Read only display coordinates, using the same anchors as AMButton.as.
        The native form owns positioning and scale; no account fields are read.
        WGC's filled form has no keyboard label, so use the submit button's edge.
        """
        if not self.canLogin():
            return None
        try:
            stack = self.login().flashObject.loginViewStack
            form = stack.currentView
            submit = form.submit
            keyboard = getattr(form, 'keyboardLang', None)
            x = float(keyboard.x) if keyboard is not None else float(submit.x) + float(submit.width) + 12
            return float(form.parent.x) + x, float(form.parent.y) + float(submit.y)
        except (AttributeError, TypeError, ValueError, ReferenceError):
            # Initial population can precede creation of the form's controls.
            return None

    def useAccount(self, account_id, auto_enter):
        if not self.canLogin():
            raise AccountError('Return to the login screen to select an account.')
        login = self.login()
        if login.loginManager.isWgcSteam:
            raise AccountError('This client uses Steam. Select the account through Steam.')
        email, password, server, index = service.credentials(account_id)
        # Explicitly leave the WGC stored-account mode before choosing credentials.
        # Authentication, queueing and errors still belong to the native login API.
        if isinstance(login._loginMode, WgcMode):
            login.changeAccount()
        login.resetToken()
        login.as_setSelectedServerIndexS(index)
        if auto_enter:
            login.onLogin(email, password, server, False)
        else:
            mode = login._loginMode
            login.as_setDefaultValuesS({
                'loginName': email,
                'pwd': password,
                'memberMe': mode.rememberUser,
                'memberMeVisible': mode.rememberPassVisible,
                'isIgrCredentialsReset': GUI_SETTINGS.igrCredentialsReset,
                'showRecoveryLink': not GUI_SETTINGS.isEmpty('recoveryPswdURL'),
                'keyboardLang': getattr(login, '_LoginView__lang', ''),
                'capsLockState': getattr(login, '_LoginView__capsLockState', False)
                })

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
    service = AccountService(BigWorld.wh_data, BigWorld.wg_cpdata, BigWorld.wg_ucpdata, g_preDefinedHosts.shortList)
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
