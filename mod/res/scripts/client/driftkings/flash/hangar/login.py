# -*- coding: utf-8 -*-
"""Native Scaleform login form bridge used by the accounts service."""
from gui import GUI_SETTINGS
from gui.Scaleform.daapi.view.login.login_modes.wgc_mode import WgcMode
from gui.Scaleform.daapi.view.login.LoginView import LoginView

from driftkings.core.hooks import override


def install_login_hooks(controller):
    override(LoginView, '_dispose', controller.loginDisposed)
    override(LoginView, 'update', controller.loginUpdated)


def launcher_position(login):
    """Read only display coordinates, using the same anchors as AMButton.as.
    The native form owns positioning and scale; no account fields are read.
    WGC's filled form has no keyboard label, so use the submit button's edge.
    """
    try:
        stack = login.flashObject.loginViewStack
        form = stack.currentView
        submit = form.submit
        keyboard = getattr(form, 'keyboardLang', None)
        x = float(keyboard.x) if keyboard is not None else float(submit.x) + float(submit.width) + 12
        return float(form.parent.x) + x, float(form.parent.y) + float(submit.y)
    except (AttributeError, TypeError, ValueError, ReferenceError):
        # Initial population can precede creation of the form's controls.
        return None

def prepare_login(login, index):
    if isinstance(login._loginMode, WgcMode):
        login.changeAccount()
        login.update()
    login.resetToken()
    login.as_setSelectedServerIndexS(index)


def fill_credentials(login, email, password):
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

