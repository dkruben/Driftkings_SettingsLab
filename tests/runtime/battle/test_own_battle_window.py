# -*- coding: utf-8 -*-
"""Own battle window: catalog selection, one window per HUD, owned teardown, unchanged payloads."""
from support import gameface_core, module, RuntimeTest, source

FEATURE = 'DriftkingsTeamStrength'
OTHER = 'DriftkingsBattleEfficiency'


class OwnBattleWindowTests(RuntimeTest):
    def setUp(self):
        super(OwnBattleWindowTests, self).setUp()
        self.resource = 42
        self.logged = []
        self.fail_load = False
        test = self

        class Model(object):
            def __init__(self, **kwargs):
                self.properties, self.commands, self.injected = [], [], kwargs
                self._initialize()

            def _initialize(self):
                pass

            def _addStringProperty(self, name, value=''):
                self.properties.append(name)

            def _addViewModelProperty(self, name, value):
                self.properties.append(name)
                setattr(self, name, value)

            def _addCommand(self, name):
                self.commands.append(name)
                return name

        class View(object):
            def __init__(self, layoutID=None, model=None):
                self.layoutID = layoutID
                self.model = model() if model is not None else None
                self.enabled, self.destroyed, self.children = True, False, {}

            def getViewModel(self):
                return self.model

            def getChildView(self, resource):
                return self.children.get(resource)

            def _getChildComponents(self):
                return {}

            def _onLoaded(self, *args, **kwargs):
                pass

            def _getEvents(self):
                return ()

            def _getListeners(self):
                return ()

            def _finalize(self):
                pass

            def setEnabled(self, value):
                self.enabled = value

            def destroy(self):
                self.destroyed = True
                self._finalize()

        class Window(object):
            created = []

            def __init__(self, flags, content=None, layer=None):
                self.flags, self.content, self.layer = flags, content, layer
                self.loaded = self.destroyed = 0
                Window.created.append(self)

            def load(self):
                if test.fail_load:
                    raise RuntimeError('window load failure')
                self.loaded += 1
                # The framework builds the children of the content view while the window loads.
                for position, factory in self.content._getChildComponents().items():
                    self.content.children[position] = factory()

            def destroy(self):
                self.destroyed += 1

        class Hud(object):
            def getChildView(self, resource):
                return None

        self.Model, self.Window, self.Hud = Model, Window, Hud
        self.injections = []
        core = gameface_core(Model, resource_id=lambda path: self.resource,
                             attach_assets=lambda *args: self.injections.append(args))
        core.AssetsModel = lambda name: module(name=name)
        self.log = module(info=lambda *args: self.logged.append(('info', args)),
                          warning=lambda *args: self.logged.append(('warning', args)),
                          exception=lambda *args: self.logged.append(('exception', args)),
                          debug=lambda *args: None)
        self.deps = {
            'driftkings.settings.service': module(settings_service=module(onModSettingsChanged=module(
                connect=lambda *args: None, disconnect=lambda *args: None))),
            'driftkings.gameface.payloads': module(publish_card=lambda child, payload: self.published.append((child, payload))),
            'gui.impl.battle.random.hud': module(RandomHUDView=Hud),
            'frameworks.wulf': module(ViewModel=Model, WindowFlags=module(WINDOW=1, WINDOW_FULLSCREEN=1024),
                                      WindowLayer=module(MARKER=3, TOP_WINDOW=10)),
            'gui.impl.pub.view_component': module(ViewComponent=View),
            'gui.impl.gen': module(R=module(aliases=module(common=module(none=lambda: 0)))),
            'gui.impl.pub.window_impl': module(WindowImpl=Window),
            'gui.shared': module(events=module(GameEvent=module(GUI_VISIBILITY=1, SHOW_CURSOR=2, HIDE_CURSOR=3)),
                                 EVENT_BUS_SCOPE=module(BATTLE=1, GLOBAL=2)),
            'driftkings.gameface.core': core,
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: dict(
                {'resource': 'test'}, **({'transport': 'own_window'} if feature == FEATURE else {}))),
            'GUI': module(mcursor=lambda: module(visible=False)),
        }

    def adapter(self, feature=FEATURE):
        """A fresh adapter installed from the real sources; returns (adapter, hooks, own_window namespace)."""
        hooks = {}
        self.published = []

        def override(cls, name):
            def decorate(function):
                hooks[name] = function
                return function
            return decorate
        deps = dict(self.deps)
        deps['driftkings.core.hooks'] = module(override=override)
        own = source('gameface/battle/own_window.py', deps)
        # Python 2 restricts metadata writes when source() replaces builtins.
        own['setattr'] = lambda target, name, value: setattr(target, name, value)
        # Only the selected feature may import the module; for any other the import would fail here.
        deps['driftkings.gameface.battle'] = module(**({'own_window': module(**dict(
            (key, value) for key, value in own.items() if not key.startswith('__')))} if feature == FEATURE else {}))
        base = source('gameface/battle/common.py', deps)
        base['setattr'] = lambda target, name, value: setattr(target, name, value)
        log = self.log

        class Adapter(base['BattleCardAdapter']):
            def __init__(self):
                super(Adapter, self).__init__(feature, 'namespace', log, 'Test', active=True)
                self.positions = []

            def refresh(self):
                self.publish({'text': 'Allies 1 : 2 Enemies', 'style': {'size': 16}}, {'locked': False, 'x': -58},
                             self.active and self.visible and self.hudVisible)

            def savePosition(self, child, args):
                self.positions.append(args)
        adapter = Adapter()
        adapter.install()
        return adapter, hooks, own

    def open_window(self, hooks, hud=None):
        hud = hud or self.Hud()
        self.assertEqual(hooks['_onLoading'](lambda view, *args: 'native result', hud), 'native result')
        return hud

    def test_other_battle_cards_keep_the_openwg_child(self):
        for feature in (OTHER, 'DriftkingsMainGun', 'test'):
            self.Window.created[:] = []
            del self.injections[:]
            adapter, hooks, _ = self.adapter(feature)
            self.assertEqual(sorted(hooks), ['_getChildComponents'])
            self.assertFalse(hasattr(adapter, 'ownWindows'))
            factories = hooks['_getChildComponents'](lambda parent: {}, self.Hud())
            factories[self.resource]()
            self.assertEqual(len(self.injections), 1)  # OpenWG injection still requested
            self.assertEqual(self.Window.created, [])

    def test_real_catalog_selects_only_team_strength(self):
        import os
        catalog = self.load('interface_catalog').GAMEFACE
        self.assertEqual([name for name, spec in catalog.items() if spec.get('transport') == 'own_window'], [FEATURE])
        hud = [name for name, spec in catalog.items() if spec['context'] == 'battle' and name != FEATURE]
        self.assertEqual(len(hud), 8)
        self.assertTrue(all('transport' not in catalog[name] for name in hud))
        self.assertNotIn('transport', catalog['DriftkingsRatingPlayers'])
        # No environment switch remains in the client sources.
        base = os.path.join(os.path.dirname(os.path.abspath(self.load('interface_catalog').__file__)), 'gameface', 'battle')
        for name in ('common.py', 'own_window.py'):
            with open(os.path.join(base, name), 'rb') as stream:
                self.assertNotIn(b'environ', stream.read())

    def test_catalog_selection_creates_one_owned_window_without_openwg(self):
        adapter, hooks, own = self.adapter()
        self.assertEqual(sorted(hooks), ['_finalize', '_onLoading'])
        self.assertEqual(hooks['_onLoading'].__module__, type(adapter).__module__)
        hud = self.open_window(hooks)
        self.assertEqual(len(self.Window.created), 1)
        window = self.Window.created[0]
        self.assertEqual((window.flags, window.layer, window.loaded), (1 | 1024, 3, 1))
        self.assertEqual(window.content.layoutID, self.resource)
        self.assertIs(adapter.ownWindows[hud], window)
        child = window.content.children[self.resource]
        self.assertIs(adapter.views[window.content], child)
        # Only the root view owns the layout; the card is keyed by the resource but uses the empty alias.
        self.assertEqual(list(window.content.children), [self.resource])
        self.assertEqual(child.layoutID, 0)
        self.assertEqual(self.injections, [])  # no gf_mod_inject
        self.assertEqual(sorted(child.getViewModel().properties), ['DriftkingsUI', 'payload'])
        self.assertEqual(child.getViewModel().commands, ['onSavePosition'])
        self.assertEqual(child.getViewModel().DriftkingsUI.name, FEATURE)
        # A repeated native load of the same HUD does not create a second window.
        self.open_window(hooks, hud)
        self.assertEqual(len(self.Window.created), 1)
        self.assertIn('warning', [level for level, _ in self.logged])
        # Another HUD (next battle) gets its own window.
        other = self.open_window(hooks)
        self.assertEqual(len(self.Window.created), 2)
        self.assertIsNot(adapter.ownWindows[other], window)

    def test_payload_cursor_and_save_position_match_the_hud_child(self):
        def run(feature):
            self.Window.created[:] = []
            adapter, hooks, _ = self.adapter(feature)
            if feature == FEATURE:
                self.open_window(hooks)
                child = self.Window.created[0].content.children[self.resource]
            else:
                parent = self.Hud()
                child = hooks['_getChildComponents'](lambda view: {}, parent)[self.resource]()
                parent.getChildView = lambda resource: child
            child._onLoaded()
            child._showCursor(None)
            child._visibility(module(ctx={'visible': False}))
            child._visibility(module(ctx={'visible': True}))
            adapter.setBattleHudVisible(False)
            adapter.setBattleHudVisible(True)
            child._hideCursor(None)
            child._savePosition({'x': 10, 'y': 20})
            self.assertEqual(len(child._getEvents()), 1)
            self.assertEqual(len(child._getListeners()), 3)
            return [payload for _, payload in self.published], adapter.positions
        native, native_positions = run(OTHER)
        owned, owned_positions = run(FEATURE)
        self.assertTrue(native)
        self.assertEqual(owned, native)
        self.assertEqual(owned_positions, native_positions)
        self.assertEqual(owned_positions, [{'x': 10, 'y': 20}])

    def test_finalize_and_dispose_remove_only_owned_windows(self):
        adapter, hooks, _ = self.adapter()
        first, second = self.open_window(hooks), self.open_window(hooks)
        one, two = self.Window.created
        calls = []
        original = lambda view, *args: calls.append(view) or 'finalized'
        self.assertEqual(hooks['_finalize'](original, first), 'finalized')
        self.assertEqual((one.destroyed, two.destroyed), (1, 0))
        self.assertNotIn(first, adapter.ownWindows)
        # Idempotent, and a HUD that never had a window is left alone.
        hooks['_finalize'](original, first)
        hooks['_finalize'](original, self.Hud())
        self.assertEqual((one.destroyed, two.destroyed, len(calls)), (1, 0, 3))
        child = two.content.children[self.resource]
        adapter.dispose()
        self.assertTrue(child.destroyed)
        self.assertFalse(child.enabled)
        self.assertEqual(two.destroyed, 1)
        self.assertEqual(len(adapter.ownWindows), 0)
        self.assertEqual(len(adapter.views), 0)
        self.assertFalse(adapter.installed)

    def test_failures_stay_inside_the_feature(self):
        adapter, hooks, _ = self.adapter()
        self.resource = -1
        self.open_window(hooks)
        self.assertEqual(self.Window.created, [])
        self.resource = 42
        self.fail_load = True
        hud = self.open_window(hooks)  # the native result is still returned
        self.assertEqual(len(self.Window.created), 1)
        self.assertEqual(self.Window.created[0].destroyed, 1)  # the half-created window is released
        self.assertNotIn(hud, adapter.ownWindows)
        self.assertIn('exception', [level for level, _ in self.logged])
        # A failing destroy does not break the native finalize.
        self.fail_load = False
        hud = self.open_window(hooks)
        window = adapter.ownWindows[hud]

        def broken():
            raise RuntimeError('destroy failure')
        window.destroy = broken
        self.assertEqual(hooks['_finalize'](lambda view: 'finalized', hud), 'finalized')
        self.assertNotIn(hud, adapter.ownWindows)
        # A card finalized by the framework leaves the adapter without stale views.
        hud = self.open_window(hooks)
        content = adapter.ownWindows[hud].content
        content.children[self.resource]._finalize()
        self.assertNotIn(content, adapter.views)
