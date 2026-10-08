# -*- coding: utf-8 -*-
"""Standalone Gameface windows for account selection and editing."""
import json
import re
from importlib import import_module

from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags, WindowLayer
from gui.impl.gen import R
from gui.impl.pub import ViewImpl
from gui.impl.pub.window_impl import WindowImpl

from Driftkings.core.accounts import AccountError
from Driftkings.ui.gameface import resource_id

RESOURCE = 'mods/Driftkings/AccountManager/window'


def _component():
    return import_module('Driftkings.components.account_manager')


def labels():
    translations = _component().config.i18n
    result = {}
    for name, key in (('title', 'accountManager'), ('add', 'add'), ('edit', 'edit'),
                      ('delete', 'delete'), ('enter', 'enter'), ('save', 'save'),
                      ('cancel', 'cancel'), ('server', 'server'), ('name', 'nick'),
                      ('showPassword', 'showPassword'), ('autoEnter', 'autoEnter'),
                      ('confirmDelete', 'acceptDeleteAccount'), ('email', 'email'),
                      ('password', 'password'), ('empty', 'empty'), ('keepPassword', 'keepPassword'),
                      ('loginOnly', 'loginOnly'), ('error', 'error'), ('manage', 'manageYourAccount')):
        value = translations.get('UI_setting_' + key, name)
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        result[name] = re.sub('<[^>]*>', '', value)
    result['close'] = 'X'
    return result


class AccountsModel(ViewModel):
    __slots__ = ('onAction',)

    def __init__(self):
        super(AccountsModel, self).__init__(properties=1, commands=1)

    def _initialize(self):
        super(AccountsModel, self)._initialize()
        self._addStringProperty('payload', '{}')
        self.onAction = self._addCommand('onAction')


class AccountsView(ViewImpl):
    def __init__(self, controller, launcher=False):
        self.controller = controller
        self.launcher = launcher
        self.live = False
        self.editing = None
        self.message = ''
        settings = ViewSettings(resource_id(RESOURCE))
        settings.flags = ViewFlags.VIEW
        settings.model = AccountsModel()
        super(AccountsView, self).__init__(settings)

    def _getEvents(self):
        return ((self.getViewModel().onAction, self.onAction),)

    def _onLoading(self, *args, **kwargs):
        super(AccountsView, self)._onLoading(*args, **kwargs)
        self.live = True
        self.refresh()

    def _finalize(self):
        self.live = False
        self.editing = None
        self.controller = None
        super(AccountsView, self)._finalize()

    def refresh(self):
        if not self.live:
            return
        service = _component().service
        payload = {'launcher': self.launcher, 'labels': labels(), 'message': self.message,
                   'canLogin': self.controller.canLogin(), 'editing': self.editing,
                   'tooltipContent': R.views.common.tooltip_window.simple_tooltip_content.SimpleTooltipContent(),
                   'tooltipDecorator': R.views.common.tooltip_window.tooltip_window.TooltipWindow()}
        if not self.launcher:
            payload['accounts'] = service.rows()
            payload['servers'] = [{'id': index, 'label': host[1]} for index, host in enumerate(service.hosts())]
            if getattr(service.store, 'read_error', False):
                payload['message'] = 'The accounts file could not be read. The original file was preserved.'
        with self.getViewModel().transaction() as model:
            model._setString(0, json.dumps(payload))

    def onAction(self, args):
        if not self.live:
            return
        try:
            raw = args.get('data', '{}')
            if len(raw) > 16384:
                raise ValueError('Invalid request')
            data = json.loads(raw)
            action = data.get('action')
            if action == 'layout':
                self.getParentWindow().place(data.get('x'), data.get('y'))
                return
            self.message = ''
            if action == 'open':
                self.controller.open()
                return
            if action == 'close':
                self.getParentWindow().destroy()
                return
            service = _component().service
            if action == 'add':
                self.editing = {'id': '', 'title': '', 'email': '', 'cluster': 0}
            elif action == 'edit':
                self.editing = service.edit(data['id'])
            elif action == 'cancel':
                self.editing = None
            elif action == 'save':
                service.save(data.get('id'), data.get('title', ''), data.get('email', ''),
                             data.get('password', ''), data.get('cluster', -1))
                self.editing = None
            elif action == 'delete' and data.get('confirmed') is True:
                service.delete(data['id'])
            elif action == 'enter':
                self.controller.useAccount(data['id'], data.get('autoEnter') is True)
                if self.live:
                    self.getParentWindow().destroy()
                return
        except AccountError as error:
            self.message = str(error)
        except Exception:
            self.message = labels()['error']
        self.refresh()


class AccountsWindow(WindowImpl):
    def __init__(self, controller, launcher=False):
        self.controller = controller
        self.launcher = launcher
        self._accountsReady = False
        self._launcherPosition = (24, 80)
        flags = WindowFlags.WINDOW if launcher else WindowFlags.WINDOW | WindowFlags.WINDOW_MODAL
        super(AccountsWindow, self).__init__(flags, content=AccountsView(controller, launcher),
                                            layer=WindowLayer.WINDOW if launcher else WindowLayer.TOP_WINDOW)

    def _onReady(self):
        super(AccountsWindow, self)._onReady()
        self._accountsReady = True
        self.place()

    def place(self, x=None, y=None):
        if self.launcher:
            anchor = self.controller.launcherPosition()
            if anchor is not None:
                x, y = anchor
            if x is not None and y is not None:
                self._launcherPosition = (max(0, min(16384, int(x))), max(0, min(16384, int(y))))
        if not self._accountsReady:
            return
        if self.launcher:
            self.move(*self._launcherPosition)
        else:
            self.center()

    def _finalize(self):
        self._accountsReady = False
        attribute = 'launcher' if self.launcher else 'window'
        if getattr(self.controller, attribute) is self:
            setattr(self.controller, attribute, None)
        super(AccountsWindow, self)._finalize()
