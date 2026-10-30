# -*- coding: utf-8 -*-
"""Flash contracts, native lifecycle and technology boundaries after migration."""
import ast
import os
import re

from support import CLIENT, ROOT, RuntimeTest, game_source, module, source


class NativeComponent(object):
    def _populate(self):
        pass

    def _dispose(self):
        pass

    def _isDAAPIInited(self):
        return self.ready


class FlashArchitectureTests(RuntimeTest):
    def meta(self):
        return source('flash/battle/meta/base.py', {
            'account_helpers.settings_core.settings_constants': module(GRAPHICS=module()),
            'gui.Scaleform.framework.entities.BaseDAAPIComponent': module(BaseDAAPIComponent=NativeComponent),
            'helpers': module(dependency=module(descriptor=lambda interface: None)),
            'skeletons.account_helpers.settings_core': module(ISettingsCore=object),
            'skeletons.gui.battle_session': module(IBattleSessionProvider=object),
            'driftkings.core.diagnostics': module(diagnostics=module(enabled=False)),
            'driftkings.core.battle_capabilities': module(battle_capabilities=None),
            'driftkings.core.hud_visibility': module(hudVisibility=None),
            'driftkings.settings.service': module(settings_service=None)})

    def test_all_six_runtime_views_resolve_their_real_meta_contract(self):
        catalog = self.load('interface_catalog')
        self.assertEqual(len(catalog.FLASH_COMPONENTS), 6)
        base = module(**self.meta())
        dependencies = {'driftkings.flash.battle.meta.base': base,
                        'driftkings.core.diagnostics': module(diagnostics=module(enabled=False))}
        folder = os.path.join(CLIENT, 'flash', 'battle', 'meta')
        for name in sorted(os.listdir(folder)):
            if name.endswith('.py') and name not in ('__init__.py', 'base.py'):
                api = source('flash/battle/meta/' + name, dependencies)
                dependencies['driftkings.flash.battle.meta.' + name[:-3]] = module(**api)
        registry = self.load('flash.battle.registry').BattleViews()
        for alias, spec in catalog.FLASH_COMPONENTS.items():
            path, name = spec['python'].rsplit('.', 1)
            self.assertTrue(path.startswith('driftkings.flash.battle.'))
            api, _ = game_source(path.replace('driftkings.', '', 1).replace('.', '/') + '.py',
                                 dependencies, real=('driftkings._constants',))
            view = api[name]
            config = module(NAME=spec['section'])
            if name == 'RatingViews':
                declared_alias, view, declared_config = view(config, module()).getBattleViews()[0]
                self.assertEqual(declared_alias, alias)
                self.assertIs(declared_config, config)
            self.assertEqual(view.FLASH_CLASS, spec['as3'])
            registry.register(alias, view, config)
            self.assertRaises(ValueError, registry.register, alias, view, config)
        self.assertEqual(len(registry.definitions), 6)

    def test_daapi_methods_still_exist_in_the_preserved_as3_sources(self):
        methods = set()
        for folder, dirs, files in os.walk(os.path.join(ROOT, 'flash_source', 'battle', 'src')):
            for name in files:
                if name.endswith('.as'):
                    with open(os.path.join(folder, name), 'rb') as stream:
                        methods.update(re.findall(r'function\s+(\w+)\s*\(', stream.read().decode('utf-8')))
        checked = 0
        for folder, dirs, files in os.walk(os.path.join(CLIENT, 'flash', 'battle', 'meta')):
            for name in files:
                if not name.endswith('.py'):
                    continue
                with open(os.path.join(folder, name), 'rb') as stream:
                    tree = ast.parse(stream.read())
                for node in ast.walk(tree):
                    method = None
                    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
                            and node.value.attr == 'flashObject'):
                        method = node.attr
                    elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                          and node.func.attr == '_sendChanged' and node.args):
                        method = ast.literal_eval(node.args[0])
                    if method:
                        checked += 1
                        self.assertIn(method, methods, name + ': ' + method)
        self.assertGreater(checked, 15)

    def test_scalar_cache_resets_for_unready_recreated_and_disposed_views(self):
        cls = self.meta()['ComponentMeta']
        view = cls()
        view.ready = True
        view._populate()
        sent = []
        view.flashObject = module(update=lambda value: sent.append(value))
        view._sendChanged('update', 1)
        view._sendChanged('update', 1)
        self.assertEqual(sent, [1])
        view.ready = False
        view._sendChanged('update', 2)
        view.ready = True
        view._sendChanged('update', 1)
        view.flashObject = module(update=lambda value: sent.append(value))
        view._sendChanged('update', 1)
        self.assertEqual(sent, [1, 1, 1])
        view._dispose()
        self.assertEqual(view._sentValues, {})

    def test_failed_native_setter_does_not_commit_the_cache(self):
        view = self.meta()['ComponentMeta']()
        view.ready = True
        view._populate()
        attempts = []
        def update(value):
            attempts.append(value)
            raise RuntimeError('native setter failed')
        view.flashObject = module(update=update)
        for i in range(2):
            self.assertRaises(RuntimeError, view._sendChanged, 'update', 1)
        self.assertEqual(attempts, [1, 1])
        self.assertEqual(view._sentValues, {})

    def test_package_registration_removes_only_owned_entries_and_closes_handlers(self):
        native = ['native.package']
        existing = ['driftkings.flash.battle']
        packages = {1: native, 2: existing}
        libraries = ['native.swf']
        api = source('flash/battle/registry.py', {
            'constants': module(ARENA_GUI_TYPE=module(RANGE=(1, 2))),
            'gui.override_scaleform_views_manager': module(g_overrideScaleFormViewsConfig=module(battlePackages=packages)),
            'gui.Scaleform.required_libraries_config': module(BATTLE_REQUIRED_LIBRARIES=libraries)})
        closed = []
        class Handler(object):
            def close(self):
                closed.append(True)
        handler = Handler()
        api['BATTLE_HANDLERS'].add(handler)
        registration = api['BattlePackageRegistration']()
        registration.install({'example': (object, object)})
        self.assertIn('driftkings.flash.battle', native)
        registration.uninstall()
        self.assertEqual(native, ['native.package'])
        self.assertEqual(existing, ['driftkings.flash.battle'])
        self.assertEqual(libraries, ['native.swf'])
        self.assertEqual(api['BATTLE_COMPONENTS'], {})
        self.assertEqual(closed, [True])

    def test_registration_service_is_idempotent_and_unwinds_failed_start(self):
        cls = self.load('flash.battle.registry').BattleViews
        events = []
        service = cls(module(install=lambda definitions: events.append('install'),
                             uninstall=lambda: events.append('uninstall')),
                      module(start=lambda: events.append('show'), stop=lambda: events.append('hide')))
        service.start()
        service.start()
        service.stop()
        service.stop()
        self.assertEqual(events, ['show', 'install', 'uninstall', 'hide'])
        def fail(definitions):
            raise RuntimeError('registration failed')
        service.registration.install = fail
        self.assertRaises(RuntimeError, service.start)
        self.assertFalse(service.active)
        self.assertEqual(events[-2:], ['uninstall', 'hide'])

    def test_hud_hooks_activate_and_release_through_the_existing_registry(self):
        hooks = self.load('core.hooks')
        visibility = self.load('core.hud_visibility').HudVisibility()
        visibility.active = True
        registry = self.load('flash.battle.registry')
        registry.BATTLE_COMPONENTS['owned'] = (object, object)
        updates = []
        class BattlePageMeta(object):
            _fullStatsAlias = 'tab'
            components = {'owned': module(as_setComponentVisible=updates.append)}
            def as_setComponentsVisibilityS(self, visible, hidden):
                return visible, hidden
            as_setComponentsVisibilityWithFadeS = as_setComponentsVisibilityS
        api = source('flash/battle/hud_visibility.py', {
            'driftkings.core.hooks': hooks,
            'driftkings.flash.battle.registry': registry,
            'gui.Scaleform.daapi.view.meta.BattlePageMeta': module(BattlePageMeta=BattlePageMeta)})
        api['setattr'] = lambda target, name, value: setattr(target, name, value)
        owner = 'service:flash_test'
        hooks.hooks.current = owner
        api['install'](visibility)
        hooks.hooks.current = None
        page = BattlePageMeta()
        hooks.hooks.activate(owner)
        self.assertEqual(page.as_setComponentsVisibilityS(['owned', 'tab'], []), (['tab'], []))
        self.assertEqual(updates, [True])
        self.assertFalse(visibility.visible)
        page.as_setComponentsVisibilityWithFadeS([], ['owned', 'tab'])
        self.assertTrue(visibility.visible)
        hooks.hooks.deactivate(owner)
        self.assertEqual(page.as_setComponentsVisibilityS(['owned'], []), (['owned'], []))
        self.assertEqual(updates, [True, False])

    def test_page_handler_cancels_discovery_when_page_changes_or_closes(self):
        scheduled, cancelled = [], []
        class NativeHandler(object):
            def __init__(self, *args, **kwargs):
                pass
            def init(self):
                pass
            def fini(self):
                pass
        api = source('flash/battle/handler.py', {
            'BigWorld': module(callback=lambda delay, callback: scheduled.append(callback) or len(scheduled),
                               cancelCallback=cancelled.append),
            'frameworks.wulf': module(WindowLayer=module(VIEW=1)),
            'gui.app_loader.settings': module(APP_NAME_SPACE=module(SF_BATTLE='battle')),
            'gui.Scaleform.daapi.settings.views': module(VIEW_ALIAS=module(BATTLE_PAGES=('first', 'second')),
                                                        VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE={}),
            'gui.Scaleform.framework.package_layout': module(PackageBusinessHandler=NativeHandler),
            'gui.shared': module(EVENT_BUS_SCOPE=module(BATTLE='battle'))})
        handler = api['BattleViewHandler']()
        handler.init()
        handler.onPageLoading(module(alias='first'))
        handler.onPageLoading(module(alias='second'))
        self.assertEqual(cancelled, [1])
        handler.close()
        self.assertEqual(cancelled, [1, 2])
        self.assertIsNone(handler.pending)
        self.assertNotIn(handler, api['BATTLE_HANDLERS'])
        # A callback already queued by the client is harmless after close.
        scheduled[-1]()
        self.assertEqual(len(scheduled), 2)

    def test_no_old_import_paths_or_flash_objects_in_functional_modules(self):
        old = ('driftkings.views.battle', 'driftkings.views.hangar',
               'driftkings.meta.battle', 'driftkings.core.overlay', 'driftkings.views:BattleViews',
               'driftkings.gameface.batalha', 'driftkings.gameface.hangar',
               'driftkings.flash.batalha', 'driftkings.flash.hangar')
        for folder, dirs, files in os.walk(CLIENT):
            for name in files:
                if not name.endswith('.py'):
                    continue
                path = os.path.join(folder, name)
                with open(path, 'rb') as stream:
                    text = stream.read().decode('utf-8-sig')
                for prefix in old:
                    self.assertNotIn(prefix, text, path)
                if os.path.relpath(path, CLIENT).split(os.sep)[0] in ('core', 'battle', 'lobby', 'components'):
                    tree = ast.parse(text.encode('utf-8'), path)
                    self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr == 'flashObject'
                                         for n in ast.walk(tree)), path)

    def test_eager_flash_import_graph_is_acyclic(self):
        graph = {}
        for folder, dirs, files in os.walk(CLIENT):
            for name in files:
                if not name.endswith('.py'):
                    continue
                path = os.path.join(folder, name)
                relative = os.path.relpath(path, CLIENT)[:-3].replace(os.sep, '.')
                key = 'driftkings.' + relative.replace('.__init__', '')
                with open(path, 'rb') as stream:
                    tree = ast.parse(stream.read(), path)
                graph[key] = []
                for node in tree.body:
                    if isinstance(node, ast.ImportFrom) and node.module:
                        graph[key].append(node.module)
                        graph[key].extend(node.module + '.' + a.name for a in node.names)
        visited = set()
        def visit(key, stack):
            self.assertNotIn(key, stack, ' -> '.join(stack + [key]))
            if key in visited:
                return
            for target in graph.get(key, ()):
                if target in graph:
                    visit(target, stack + [key])
            visited.add(key)
        for key in graph:
            if key.startswith('driftkings.flash'):
                visit(key, [])

    def test_numerical_timing_is_independent_of_flash(self):
        timing = self.load('core.aiming_timing')
        self.assertEqual(timing.dispersion_timing(1.0, .5, 2.0), (.5, 100, 0))
        self.assertEqual(timing.dispersion_timing(.25, 1.0, 2.0), (.25, 25, 2.77))
        self.assertEqual(timing.flight_time(400.0, 800.0), .5)

    def test_login_bridge_keeps_native_form_values_and_position_fallback(self):
        class WgcMode(object):
            rememberUser = True
            rememberPassVisible = False
        api = source('flash/lobby/login.py', {
            'gui': module(GUI_SETTINGS=module(igrCredentialsReset=False, isEmpty=lambda key: False)),
            'gui.Scaleform.daapi.view.login.login_modes.wgc_mode': module(WgcMode=WgcMode),
            'gui.Scaleform.daapi.view.login.LoginView': module(LoginView=object),
            'driftkings.core.hooks': module(override=None)})
        calls = []
        login = module(_loginMode=WgcMode(), changeAccount=lambda: calls.append('change'),
                       update=lambda: calls.append('update'), resetToken=lambda: calls.append('reset'),
                       as_setSelectedServerIndexS=lambda index: calls.append(index),
                       as_setDefaultValuesS=lambda data: calls.append(data))
        api['prepare_login'](login, 2)
        self.assertEqual(calls, ['change', 'update', 'reset', 2])
        api['fill_credentials'](login, 'test@example.invalid', 'test-only')
        self.assertEqual(calls[-1]['loginName'], 'test@example.invalid')
        self.assertTrue(calls[-1]['memberMe'])
        self.assertFalse(calls[-1]['memberMeVisible'])
        form = module(parent=module(x=100, y=200), submit=module(x=10, y=20, width=30))
        login.flashObject = module(loginViewStack=module(currentView=form))
        self.assertEqual(api['launcher_position'](login), (152, 220))
        form.keyboardLang = module(x=5)
        self.assertEqual(api['launcher_position'](login), (105, 220))
        del login.flashObject
        self.assertIsNone(api['launcher_position'](login))
