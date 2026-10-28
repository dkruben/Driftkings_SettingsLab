# -*- coding: utf-8 -*-
"""Halloween TAB (TabScreen): a separate allies table, hooked late, never the native rows."""
import io
import json
import os
import sys

from support import CLIENT, Hooks, RuntimeTest, module, source

MODULE = 'halloween.gui.impl.battle.full_stats'


class View(object):
    def __init__(self):
        self.children = {}
        self.showingStatus = 'SHOWN'

    def setChildView(self, resource, child):
        self.children[resource] = child

    def getChildView(self, resource):
        return self.children.get(resource)

    def _onLoaded(self):
        pass

    def _onShown(self):
        pass

    def _onHidden(self):
        pass

    def _finalize(self):
        pass


class Model(object):
    def __init__(self):
        self.payload = None

    def transaction(self):
        model = self

        class Transaction(object):
            def __enter__(self):
                return model

            def __exit__(self, *args):
                return False
        return Transaction()

    def _setString(self, index, value):
        self.payload = json.loads(value)


class GamefaceTabTests(RuntimeTest):
    def setUp(self):
        super(GamefaceTabTests, self).setUp()
        self.kind = 'classic'
        self.addCleanup(sys.modules.pop, MODULE, None)
        sys.modules.pop(MODULE, None)

    def bridge(self, real_hooks=False):
        hooks = Hooks()
        if real_hooks:
            hook_api = self.load('core.hooks')
            hook_api.hooks.current = 'driftkings.battle.team_panels'
            hook_api.hooks.activate(hook_api.hooks.current)
        else:
            hook_api = module(override=hooks.override, hooks=module(current='driftkings.battle.team_panels'))
        self.hook_api = hook_api
        self.refreshes = []
        self.owner = module(active=True, tabKind=lambda: self.kind,
                            refresh=lambda: self.refreshes.append(1), config=None)

        class TabView(View):
            pass

        class Child(object):
            def __init__(self, settings):
                self.model = Model()

            def getViewModel(self):
                return self.model

        settings = module(getComponentDict=lambda config: {'performance': {'diagnostics': False}})
        api = source('gameface/battle/panel_gameface.py', {
            'frameworks.wulf': module(ViewModel=type('ViewModel', (object,), {'__init__': lambda self, **kwargs: None}),
                                      ViewSettings=lambda resource, model=None: None),
            'frameworks.wulf.gui_constants': module(ShowingStatus=module(SHOWING='SHOWING', SHOWN='SHOWN')),
            'gui.impl.pub': module(ViewImpl=Child),
            'gui.impl.battle.battle_page.tab_view': module(TabView=TabView),
            'driftkings.gameface.core': module(attach_assets=lambda *args: None, resource_id=lambda value: 77),
            'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'tab'}),
            'driftkings.settings.service': module(settings_service=settings),
            'driftkings._constants': module(GLOBAL=module(ENABLED='enabled'),
                                            TEAM_PANELS=module(PERFORMANCE='performance')),
            'driftkings.core.diagnostics': module(diagnostics=module(enabled=False)),
            'driftkings.core.hooks': hook_api,
        })
        bridge = api['GamefaceLoading'](self.owner)
        hook_api.hooks.current = None
        return bridge, hooks

    def screen_module(self):
        class TabScreen(View):
            pass
        sys.modules[MODULE] = module(TabScreen=TabScreen)
        return TabScreen

    def test_random_tab_gets_the_roster_child(self):
        bridge, hooks = self.bridge()
        view = View()
        hooks.get('TabView', '_onLoaded')(lambda view: None, view)
        self.assertEqual(list(view.children), [77])
        self.assertEqual(bridge.active_screens(), set(['tab']))

    def test_halloween_does_not_use_the_classic_tab(self):
        self.kind = 'halloween'
        bridge, hooks = self.bridge()
        view = View()
        hooks.get('TabView', '_onLoaded')(lambda view: None, view)
        self.assertEqual(view.children, {})

    def test_late_hooks_use_the_active_component_owner(self):
        self.kind = 'halloween'
        bridge, _ = self.bridge(real_hooks=True)
        screen = self.screen_module()
        bridge.watch('halloween')
        self.assertIsNone(self.hook_api.hooks.current)
        view = screen()
        view._onLoaded()
        self.assertEqual(list(view.children), [77])
        view._onHidden()
        self.assertEqual(bridge.active_screens(), set())
        view._onShown()
        self.assertEqual(bridge.active_screens(), set(['tab']))
        view._finalize()
        self.assertEqual(bridge.active_screens(), set())
        self.hook_api.hooks.deactivate('driftkings.battle.team_panels')
        stopped = screen()
        stopped._onLoaded()
        self.assertEqual(stopped.children, {})

    def test_tab_screen_is_hooked_only_once_its_module_is_loaded(self):
        bridge, hooks = self.bridge()
        bridge.watch('halloween')
        self.assertNotIn(('TabScreen', '_onLoaded'), hooks.overrides)
        self.screen_module()
        bridge.watch('classic')
        self.assertNotIn(('TabScreen', '_onLoaded'), hooks.overrides)
        bridge.watch('halloween')
        bridge.watch('halloween')
        self.assertIn(('TabScreen', '_onLoaded'), hooks.overrides)
        self.assertEqual(bridge.watched, set(['halloween']))

    def test_tab_screen_attaches_only_in_halloween(self):
        bridge, hooks = self.bridge()
        self.screen_module()
        bridge.watch('halloween')
        loaded = hooks.get('TabScreen', '_onLoaded')
        view = View()
        loaded(lambda view: None, view)
        self.assertEqual(view.children, {})
        self.kind = 'halloween'
        loaded(lambda view: None, view)
        self.assertEqual(list(view.children), [77])

    def test_halloween_payload_is_a_separate_sorted_table(self):
        self.kind = 'halloween'
        bridge, hooks = self.bridge()
        self.screen_module()
        bridge.watch('halloween')
        # The TabScreen has no playerList: reading the native model would raise.
        view = View()
        hooks.get('TabScreen', '_onLoaded')(lambda view: None, view)
        summary = {'enabled': True, 'name': 'a', 'stats': True}
        rows = [{'id': 2, 'index': 1, 'ally': True, 'aliases': [], 'tab': {}, 'summary': dict(summary, name='b')},
                {'id': 1, 'index': 0, 'ally': True, 'aliases': [], 'tab': {}, 'summary': summary},
                {'id': 3, 'index': 2, 'ally': True, 'aliases': [], 'tab': {}, 'summary': dict(summary, enabled=False)}]
        bridge.update(True, rows)
        payload = view.children[77].model.payload
        self.assertEqual((payload['screen'], payload['enabled']), ('hwTab', True))
        self.assertEqual([(row['id'], row['name']) for row in payload['rows']], [(1, 'a'), (2, 'b')])
        bridge.update(False, rows)
        self.assertEqual(view.children[77].model.payload, {'enabled': False, 'screen': 'tab', 'rows': []})

    def test_the_extension_is_never_imported_by_the_mod(self):
        path = os.path.join(CLIENT, 'gameface', 'battle', 'panel_gameface.py')
        with io.open(path, encoding='utf-8') as stream:
            text = stream.read()
        self.assertNotIn('import halloween', text)
        self.assertNotIn('from halloween', text)
