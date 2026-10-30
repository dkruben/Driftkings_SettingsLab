# -*- coding: utf-8 -*-
"""Architecture boundaries and runtime contracts of the centralized bridge."""
import ast
import os

from support import CLIENT, Hooks, RuntimeTest, game_source, module, source


class GamefaceArchitectureTests(RuntimeTest):
    def test_catalog_modules_execute_with_stubbed_game_boundaries(self):
        catalog = self.load('interface_catalog')
        for spec in catalog.GAMEFACE.values():
            relative = spec['python'].replace('driftkings.', '', 1).replace('.', '/') + '.py'
            game_source(relative, {'driftkings.interface_catalog': catalog})

    def test_catalog_implementations_exist_in_the_correct_context(self):
        catalog = self.load('interface_catalog').GAMEFACE
        self.assertEqual(len(catalog), 18)
        resources = set()
        owners = set()
        for name, spec in catalog.items():
            context = 'battle' if spec['context'] in ('battle', 'tab') else 'lobby'
            self.assertTrue(spec['python'].startswith('driftkings.gameface.' + context + '.'), name)
            path = os.path.join(CLIENT, *spec['python'].split('.')[1:]) + '.py'
            self.assertTrue(os.path.isfile(path), path)
            self.assertNotIn(spec['resource'], resources)
            resources.add(spec['resource'])
            if spec['owner'] is not None:
                self.assertNotIn(spec['owner'], owners)
                owners.add(spec['owner'])

    def test_view_implementations_do_not_escape_the_gameface_package(self):
        for folder, dirs, files in os.walk(CLIENT):
            if os.path.relpath(folder, CLIENT).split(os.sep)[0] == 'gameface':
                continue
            for name in files:
                if not name.endswith('.py'):
                    continue
                path = os.path.join(folder, name)
                with open(path, 'rb') as stream:
                    tree = ast.parse(stream.read(), path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        self.assertNotIn(node.module, ('gui.impl.pub', 'gui.impl.pub.view_component'), path)
                        if node.module == 'frameworks.wulf':
                            self.assertFalse(set(a.name for a in node.names) &
                                             set(('ViewModel', 'ViewSettings')), path)

    def test_eager_gameface_imports_have_no_cycles(self):
        graph = {}
        base = os.path.join(CLIENT, 'gameface')
        for folder, dirs, files in os.walk(base):
            for name in files:
                if not name.endswith('.py'):
                    continue
                path = os.path.join(folder, name)
                key = 'driftkings.' + os.path.relpath(path, CLIENT)[:-3].replace(os.sep, '.')
                with open(path, 'rb') as stream:
                    tree = ast.parse(stream.read(), path)
                graph[key] = []
                for node in tree.body:
                    if isinstance(node, ast.ImportFrom) and node.module:
                        graph[key].append(node.module)
                        graph[key].extend(node.module + '.' + a.name for a in node.names)
        def visit(key, stack):
            self.assertNotIn(key, stack, ' -> '.join(stack + [key]))
            for target in graph.get(key, ()):
                if target in graph:
                    visit(target, stack + [key])
        for key in graph:
            visit(key, [])

    def test_shared_packages_import_without_the_game_engine(self):
        for name in ('gameface', 'gameface.battle', 'gameface.lobby',
                     'gameface.payloads', 'gameface.registry'):
            self.assertIsNotNone(self.load(name))

    def test_native_tab_hooks_preserve_hud_service_ownership_and_cleanup(self):
        visibility = self.load('core.hud_visibility').HudVisibility()
        visibility.active = True
        hooks = Hooks()
        class TabView(object):
            pass
        api = source('gameface/battle/hud_visibility.py', {
            'driftkings.core.hooks': module(override=hooks.override),
            'gui.impl.battle.battle_page.tab_view': module(TabView=TabView)})
        # Python 2 restricts metadata writes from the stubbed builtins namespace.
        api['setattr'] = lambda target, name, value: setattr(target, name, value)
        api['install'](visibility)
        shown = hooks.get('TabView', '_onShown')
        hidden = hooks.get('TabView', '_onHidden')
        self.assertEqual(shown.__module__, type(visibility).__module__)
        view = object()
        self.assertEqual(shown(lambda view: 'shown', view), 'shown')
        self.assertFalse(visibility.visible)
        visibility.block('native', True)
        def failing_original(view):
            raise RuntimeError('native finalization failed')
        self.assertRaises(RuntimeError, hidden, failing_original, view)
        self.assertTrue(visibility.visible)
        self.assertEqual(visibility.blockers, set())
        visibility.active = False
        shown(lambda view: None, view)
        self.assertTrue(visibility.visible)

    def test_hangar_installer_uses_explicit_resource_and_routes_visibility(self):
        hooks = Hooks()
        class RandomHangar(object):
            pass
        api = source('gameface/lobby/common.py', {
            'driftkings.core.hooks': module(override=hooks.override),
            'driftkings.core.settings_controller': module(SettingsController=object),
            'driftkings.gameface.payloads': module(publish_card=None),
            'gui.impl.lobby.hangar.random.random_hangar': module(RandomHangar=RandomHangar),
            'driftkings.gameface.core': module(INVALID_RES_ID=-1, resource_id=lambda key: 42)})
        api['setattr'] = lambda target, name, value: setattr(target, name, value)
        calls = []
        component = module(g_controller=module(setVisible=lambda parent, value: calls.append(value)))
        api['install_card'](lambda: component, lambda parent, resource: (parent, resource),
                            'driftkings.lobby.example', 'mods/driftkings/example/model')
        parent = object()
        children = hooks.get('RandomHangar', '_getChildComponents')(lambda parent: {1: 'native'}, parent)
        self.assertEqual(children[1], 'native')
        self.assertEqual(children[42](), (parent, 42))
        hooks.get('RandomHangar', '_onShown')(lambda parent: None, parent)
        hooks.get('RandomHangar', '_onHidden')(lambda parent: None, parent)
        self.assertEqual(calls, [True, False])

    def test_resource_resolution_uses_the_native_tree_and_rejects_unknown_keys(self):
        class Resource(object):
            def __getattr__(self, name):
                return self
            def __call__(self):
                return 42
        catalog = self.load('interface_catalog')
        api = source('gameface/core.py', {
            'frameworks.wulf': module(ViewModel=object),
            'gui.impl.gen': module(R=Resource()),
            'openwg_gameface': module(gf_mod_inject=lambda *a, **k: None),
            'driftkings.interface_catalog': catalog})
        for spec in catalog.GAMEFACE.values():
            self.assertEqual(api['resource_id'](spec['resource']), 42)
        self.assertRaises(ValueError, api['resource_id'], 'mods/driftkings/missing/model')

    def test_payload_cache_commits_only_after_successful_transaction(self):
        publish = self.load('gameface.payloads').publish_card
        values = []
        class Transaction(object):
            fail = False
            def __enter__(self):
                return self
            def _setString(self, index, value):
                values.append(value)
            def __exit__(self, *args):
                if self.fail:
                    raise RuntimeError('native transaction failed')
        transaction = Transaction()
        view = module(_lastPayload=None, getViewModel=lambda: module(transaction=lambda: transaction))
        first = {'config': {'visible': True}, 'value': 1}
        self.assertTrue(publish(view, first))
        self.assertFalse(publish(view, first))
        self.assertEqual(len(values), 1)
        transaction.fail = True
        self.assertRaises(RuntimeError, publish, view, {'value': 2})
        self.assertIs(view._lastPayload, first)

    def test_window_registry_rejects_duplicates_and_preserves_native_entries(self):
        definitions = {}
        added = []
        factory = module(getSettings=definitions.get,
                         addSettings=lambda d: (definitions.update({d.alias: d}), added.append(d.alias)))
        api = source('gameface/registry.py', {
            'helpers': module(dependency=module(instance=lambda interface: module(entitiesFactory=factory))),
            'skeletons.gui.impl': module(IGuiLoader=object)})
        registry = api['WindowViews']()
        registry.registerModule(module(getWindowViews=lambda: (module(alias='settings'),)))
        registry.start()
        registry.start()
        self.assertEqual(added, ['settings'])
        registry.registerModule(module(getWindowViews=lambda: (module(alias='settings'),)))
        self.assertRaises(ValueError, registry.start)
        registry.stop()
        self.assertEqual(registry.definitions, [])
        self.assertIn('settings', definitions)
