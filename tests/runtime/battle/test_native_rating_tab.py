# -*- coding: utf-8 -*-
"""Native classic TAB: actual Wulf model, ownership, payload, visibility and cleanup."""
import json
import sys

from support import Hooks, RuntimeTest, module, source

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
    def __init__(self, properties=0, commands=0):
        self.properties, self.commands, self.payload = properties, commands, None
        self._initialize()

    def _initialize(self):
        pass

    def _addStringProperty(self, name, value):
        setattr(self, name, value)

    def _addViewModelProperty(self, name, value):
        setattr(self, name, value)

    def _addCommand(self, name):
        return name

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

        self.tab_class = TabView

        class Child(object):
            def __init__(self, settings):
                self.model = settings.model

            def getViewModel(self):
                return self.model

        settings = module(getComponentDict=lambda config: {'enabled': True, 'performance': {'diagnostics': False}})
        catalog = self.load('interface_catalog')
        core = source('gameface/core.py', {'frameworks.wulf': module(ViewModel=Model),
                      'gui.impl.gen': module(R=None), 'driftkings.interface_catalog': catalog})
        api = source('gameface/battle/panel_gameface.py', {
            'frameworks.wulf': module(ViewModel=Model, ViewSettings=lambda resource, model=None: module(model=model)),
            'frameworks.wulf.gui_constants': module(ShowingStatus=module(SHOWING='SHOWING', SHOWN='SHOWN')),
            'gui.impl.pub': module(ViewImpl=Child),
            'gui.impl.battle.battle_page.tab_view': module(TabView=TabView),
            'driftkings.gameface.core': module(payload_model=core['payload_model'], resource_id=lambda value: 77),
            'driftkings.interface_catalog': catalog,
            'driftkings.settings.service': module(settings_service=settings),
            'driftkings._constants': module(GLOBAL=module(ENABLED='enabled'),
                                            TEAM_PANELS=module(PERFORMANCE='performance')),
            'driftkings.core.diagnostics': module(diagnostics=module(enabled=False)),
            'driftkings.core.hooks': hook_api,
        })
        bridge = api['GamefaceLoading'](self.owner)
        hook_api.hooks.current = None
        return bridge, hooks

    def test_random_tab_gets_the_roster_child(self):
        bridge, hooks = self.bridge()
        view = View()
        hooks.get('TabView', '_onLoaded')(lambda view: None, view)
        self.assertEqual(list(view.children), [77])
        self.assertEqual(bridge.active_screens(), set(['tab']))


    def test_native_model_commands_and_duplicate_load(self):
        bridge, hooks = self.bridge()
        view = View()
        loaded = hooks.get('TabView', '_onLoaded')
        loaded(lambda view: 'native', view)
        child = view.children[77]
        self.assertEqual((child.model.properties, child.model.commands), (2, 1))
        self.assertEqual(child.model.DriftkingsUI.name, 'DriftkingsRatingPlayers')
        self.assertEqual(child.model.onPerformance, 'onPerformance')
        self.assertEqual(loaded(lambda view: 'again', view), 'again')
        self.assertIs(view.children[77], child)
        self.assertEqual(len(bridge.children), 1)

    def test_only_classic_context_attaches_and_no_seasonal_hooks_exist(self):
        for kind in ('halloween', 'flash', 'frontline', None):
            self.kind = kind
            bridge, hooks = self.bridge()
            view = View()
            hooks.get('TabView', '_onLoaded')(lambda view: None, view)
            self.assertEqual(view.children, {})
            self.assertFalse(hasattr(bridge, 'watch'))
            self.assertTrue(all(name == 'TabView' for name, event in hooks.overrides))

    def test_payload_native_order_visibility_and_disposal(self):
        bridge, hooks = self.bridge()
        view = View()
        player = lambda ident: module(getVehicleId=lambda: ident)
        view.viewModel = module(playerList=module(getAllies=lambda: [player(2), player(1)],
                                                 getEnemies=lambda: [player(3)]))
        hooks.get('TabView', '_onLoaded')(lambda view: None, view)
        rows = [{'id': ident, 'ally': ident < 3, 'aliases': [str(ident)], 'tab': {'enabled': True}}
                for ident in (1, 2, 3)]
        bridge.update(True, rows)
        model = view.children[77].model
        self.assertEqual(model.payload['order'], {'left': [2, 1], 'right': [3]})
        self.assertEqual(model.payload['screen'], 'tab')
        self.assertEqual(model.payload['rows'], [dict(id=row['id'], ally=row['ally'], aliases=row['aliases'], cfg=row['tab']) for row in rows])
        hooks.get('TabView', '_onHidden')(lambda view: None, view)
        bridge.update(True, rows)
        self.assertEqual(model.payload, {'enabled': False, 'screen': 'tab', 'rows': []})
        self.assertEqual(bridge.active_screens(), set())
        hooks.get('TabView', '_onShown')(lambda view: None, view)
        bridge.update(True, rows)
        self.assertTrue(model.payload['enabled'])
        bridge.dispose()
        self.assertIsNone(view.children[77])
        self.assertEqual(model.payload, {'enabled': False, 'screen': 'tab', 'rows': []})
        bridge.dispose()
        self.assertFalse(bridge.children)

    def test_finalize_reopen_and_foreign_replacement(self):
        bridge, hooks = self.bridge()
        first = View()
        hooks.get('TabView', '_onLoaded')(lambda view: None, first)
        hooks.get('TabView', '_finalize')(lambda view: None, first)
        self.assertFalse(bridge.children)
        second = View()
        hooks.get('TabView', '_onLoaded')(lambda view: None, second)
        foreign = object()
        second.children[77] = foreign
        bridge.update(False, [])
        self.assertFalse(bridge.children)
        bridge.dispose()
        self.assertIs(second.children[77], foreign)

    def test_component_hook_ownership_without_late_extension_hooks(self):
        bridge, _ = self.bridge(real_hooks=True)
        view = self.tab_class()
        view._onLoaded()
        self.assertEqual(list(view.children), [77])
        view._finalize()
        self.assertFalse(bridge.children)
        self.hook_api.hooks.deactivate('driftkings.battle.team_panels')
        stopped = self.tab_class()
        stopped._onLoaded()
        self.assertFalse(stopped.children)
        self.assertFalse(hasattr(bridge, 'watch'))
