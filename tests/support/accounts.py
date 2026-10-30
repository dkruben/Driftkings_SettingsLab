# -*- coding: utf-8 -*-
"""Explicit account-manager boundaries; no automatic WG attribute creation."""
import json
import os
from support import module, source


class Store(object):
    def __init__(self):
        self.accounts = [dict(id='first', title='Example', email='test@example.com',
                              password='fictional-secret', cluster=0, realm='NA', server='auto')]
        self.read_error = False
        self.saved = True

    def write_accounts(self):
        return self.saved


def service(test, store=None):
    api = test.load('core.accounts')
    store = store or Store()
    return api.AccountService(store, lambda value: value, lambda value: value,
                              lambda: [('auto', 'Automatic', 0, None)], 'NA')


def component(test, directory, callbacks=None):
    callbacks = callbacks or module(callback=lambda delay, handler: 1, cancelCallback=lambda ident: None)
    log = module(error=lambda *args: None)
    constants = test.load('_constants')
    return source('components/account_manager.py', {
        'BigWorld': module(wg_getPreferencesFilePath=lambda: os.path.join(directory, 'preferences.xml'),
                           wg_cpdata=lambda value: value, wg_ucpdata=lambda value: value),
        'external_strings_utils': module(unicode_from_utf8=lambda value: (None, value)),
        'helpers': module(getClientLanguage=lambda: 'en'),
        'predefined_hosts': module(g_preDefinedHosts=module(shortList=lambda: [('auto', 'Automatic', 0, None)])),
        'realm': module(CURRENT_REALM='NA'),
        'skeletons.gui.app_loader': module(GuiGlobalSpaceID=module(LOGIN=1)),
        'driftkings._constants': constants,
        'driftkings.common.utils': module(events=module(LoginView=module(populate=module(after=object())))),
        'driftkings.common.utils.filesystem': test.load('common.utils.filesystem'),
        'driftkings.core.accounts': test.load('core.accounts'),
        'driftkings.core.callbacks': callbacks,
        'driftkings.core.hooks': module(on_event=lambda *args: None),
        'driftkings.i18n': module(catalog=module(section=lambda *args: {})),
        'driftkings.logger': module(get_logger=lambda name: log),
        'driftkings.settings.service': module(settings_service=module(getComponentDict=lambda config: {'enabled': True})),
        'driftkings.settings.settings_data': module(defaults=lambda name: {'accountManager': {'enabled': True}}),
        'driftkings.flash.lobby.login': module(fill_credentials=lambda *args: None, install_login_hooks=lambda owner: None,
                                               launcher_position=lambda login: (10, 20), prepare_login=lambda *args: None)})


class Model(object):
    def __init__(self, *args, **kwargs):
        self.payload = None

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def _setString(self, index, value):
        self.payload = json.loads(value)


class View(object):
    def __init__(self, settings):
        self.model = Model()
        self.finalized = False

    def getViewModel(self):
        return self.model

    def getParentWindow(self):
        return self.parent

    def _finalize(self):
        self.finalized = True


def presentation(test, accounts, owner):
    component = module(service=accounts, config=module(i18n={}))
    log = module(exception=lambda *args: None)
    api = source('gameface/lobby/account_manager.py', {
        'importlib': module(import_module=lambda name: component),
        'frameworks.wulf': module(ViewFlags=module(VIEW=1), ViewModel=Model,
                                  ViewSettings=lambda resource: module(),
                                  WindowFlags=module(WINDOW=1, WINDOW_MODAL=2, WINDOW_FULLSCREEN=4),
                                  WindowLayer=module(WINDOW=1, TOP_WINDOW=2)),
        'gui.impl.gen': module(R=module(views=module(common=module(tooltip_window=module(
            simple_tooltip_content=module(SimpleTooltipContent=lambda: 1),
            tooltip_window=module(TooltipWindow=lambda: 2)))))),
        'gui.impl.pub': module(ViewImpl=View),
        'gui.impl.pub.window_impl': module(WindowImpl=object),
        'driftkings.core.accounts': test.load('core.accounts'),
        'driftkings.gameface.core': module(resource_id=lambda name: 1),
        'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'accounts'}),
        'driftkings.logger': module(get_logger=lambda name: log)})
    view = api['AccountsView'](owner)
    view.live = True
    return view
