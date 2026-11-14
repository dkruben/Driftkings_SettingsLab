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

    def test_all_seven_runtime_views_resolve_their_real_meta_contract(self):
        catalog = self.load('interface_catalog')
        self.assertEqual(len(catalog.FLASH_COMPONENTS), 7)
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
        self.assertEqual(len(registry.definitions), 7)

    def test_ratings_class_names_are_case_sensitive_and_keep_their_package(self):
        folder = os.path.join(ROOT, 'flash_source', 'battle', 'src', 'driftkings', 'battle', 'components', 'ratings')
        filenames = os.listdir(folder)
        renamed = (('panelrow', 'PanelRow'), ('panelrenderer', 'PanelRenderer'), ('viewbindings', 'ViewBindings'))
        for old, new in renamed:
            self.assertIn(new + '.as', filenames)
            self.assertNotIn(old + '.as', filenames)
            with open(os.path.join(folder, new + '.as'), 'rb') as stream:
                text = stream.read().decode('utf-8')
            self.assertIn('package driftkings.battle.components.ratings', text)
            self.assertIsNotNone(re.search(r'public class ' + new + r'\b', text))
            self.assertIn('public function ' + new + '(', text)
            self.assertIsNone(re.search(r'\b' + old + r'\b', text))
        for filename in ('PanelRenderer.as', 'ratingscreens.as'):
            with open(os.path.join(folder, filename), 'rb') as stream:
                text = stream.read().decode('utf-8')
            for old, new in renamed:
                self.assertIsNone(re.search(r'\b' + old + r'\b', text))
        with open(os.path.join(folder, 'ratingscreens.as'), 'rb') as stream:
            text = stream.read().decode('utf-8')
        self.assertIn('public class ratingscreens extends BattleUIDisplayable', text)
        self.assertIn('new PanelRenderer(state)', text)
        self.assertIn('new ViewBindings(this)', text)

    def test_battle_displayable_name_and_six_subclasses_preserve_contracts(self):
        root = os.path.join(ROOT, 'flash_source', 'battle', 'src', 'driftkings', 'battle')
        self.assertIn('BattleDisplayable.as', os.listdir(os.path.join(root, 'base')))
        self.assertNotIn('battledisplayable.as', os.listdir(os.path.join(root, 'base')))
        with open(os.path.join(root, 'base', 'BattleDisplayable.as'), 'rb') as stream:
            base = stream.read().decode('utf-8')
        self.assertIn('package driftkings.battle.base', base)
        self.assertIn('public class BattleDisplayable extends BattleUIDisplayable', base)
        self.assertIn('public function BattleDisplayable()', base)
        self.assertIn('function as_setBattleHudVisible(value:Boolean):void', base)
        subclasses = []
        for folder, dirs, files in os.walk(root):
            for name in files:
                if not name.endswith('.as'):
                    continue
                with open(os.path.join(folder, name), 'rb') as stream:
                    source_text = stream.read().decode('utf-8')
                self.assertIsNone(re.search(r'\bbattledisplayable\b', source_text))
                if re.search(r'extends\s+BattleDisplayable\b', source_text):
                    subclasses.append(name)
                    self.assertIn('import driftkings.battle.base.BattleDisplayable;', source_text)
        # Independent inheritance contract: do not derive expected subclasses from the implementation.
        self.assertEqual(sorted(subclasses), sorted(('debugpanelui.as', 'distancemarkerui.as',
                         'minimapenhancementsui.as', 'overlayui.as', 'sixthsenseui.as', 'ammohealthui.as')))
        with open(os.path.join(root, 'factory', 'ComponentFactory.as'), 'rb') as stream:
            factory = stream.read().decode('utf-8')
        self.assertIn('var hud:BattleDisplayable = component as BattleDisplayable;', factory)
        self.assertIn('host.registerFlashComponentS(component, alias);', factory)

    def test_component_factory_identity_and_both_entrypoint_calls(self):
        folder = os.path.join(ROOT, 'flash_source', 'battle', 'src')
        factory_folder = os.path.join(folder, 'driftkings', 'battle', 'factory')
        self.assertIn('ComponentFactory.as', os.listdir(factory_folder))
        self.assertNotIn('componentfactory.as', os.listdir(factory_folder))
        with open(os.path.join(factory_folder, 'ComponentFactory.as'), 'rb') as stream:
            factory = stream.read().decode('utf-8')
        self.assertIn('package driftkings.battle.factory', factory)
        self.assertIn('public class ComponentFactory', factory)
        self.assertIn('public static function create(host:Object, aliases:Array, surface:String):void', factory)
        self.assertIn('ComponentCatalog.classes(surface)', factory)
        self.assertNotIn('function ComponentFactory(', factory)
        with open(os.path.join(folder, 'driftkingsbattle.as'), 'rb') as stream:
            root = stream.read().decode('utf-8')
        self.assertIn('import driftkings.battle.factory.ComponentFactory;', root)
        self.assertEqual(root.count('ComponentFactory.create('), 2)
        for surface in ('battle', 'ratings'):
            self.assertIn('ComponentFactory.create(this, aliases, "' + surface + '")', root)
        for value in (factory, root):
            self.assertIsNone(re.search(r'\b(componentfactory|componentcatalog)\b', value))

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
