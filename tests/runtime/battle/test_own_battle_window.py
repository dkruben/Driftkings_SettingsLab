# -*- coding: utf-8 -*-
"""Shared own battle window: catalog selection, one window per HUD for every selected card,
independent models and payloads, owned teardown."""
from support import gameface_core, module, RuntimeTest, source

FEATURE = 'DriftkingsTeamStrength'
HEALTH = 'DriftkingsOwnHealth'
OTHER = 'unselected-test-card'
OWN = (FEATURE, HEALTH, 'DriftkingsBattleEfficiency', 'DriftkingsMainGun', 'DriftkingsMarksOnGunBattle',
       'DriftkingsTargetInformation', 'DriftkingsPenetration', 'DriftkingsFlightTime', 'DriftkingsAimingCountdown')


class OwnBattleWindowTests(RuntimeTest):
    def setUp(self):
        super(OwnBattleWindowTests, self).setUp()
        self.host_resource = 'mods/driftkings/battle_hud/window'
        self.host_id = 142
        self.resources = dict((name, 42 + index) for index, name in enumerate(OWN))
        self.resources[self.host_resource] = self.host_id
        self.logged = []
        self.settings_signals = []
        self.fail_load = False
        self.fail_feature = None
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
                    child = factory()
                    if child is not None:  # like ViewComponent: a failed child is reported and skipped
                        self.content.children[position] = child

            def destroy(self):
                self.destroyed += 1

        class Hud(object):
            def getChildView(self, resource):
                return None

        self.Model, self.Window, self.Hud = Model, Window, Hud
        self.injections = []
        core = gameface_core(Model, resource_id=lambda path: self.resources.get(path, 50),
                             attach_assets=lambda *args: self.injections.append(args))

        def assets(name):
            if name == test.fail_feature:
                raise RuntimeError('model failure')
            return module(name=name)
        core.AssetsModel = assets
        self.log = module(info=lambda *args: self.logged.append(('info', args)),
                          warning=lambda *args: self.logged.append(('warning', args)),
                          exception=lambda *args: self.logged.append(('exception', args)),
                          debug=lambda *args: None)
        self.deps = {
            'driftkings.settings.service': module(settings_service=module(onModSettingsChanged=module(
                connect=lambda *args: self.settings_signals.append(('connect', args)),
                disconnect=lambda *args: self.settings_signals.append(('disconnect', args))))),
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
            'driftkings.interface_catalog': module(BATTLE_HUD_HOST={'resource': self.host_resource}, gameface_spec=lambda feature: dict(
                {'resource': feature}, **({'transport': 'own_window'} if feature in OWN else {}))),
            'GUI': module(mcursor=lambda: module(visible=False)),
        }

    def session(self):
        """The real own_window module, shared by every adapter of this session, and the declared hooks."""
        self.hooks = {}
        self.published = []
        hooks = self.hooks

        def override(cls, name):
            def decorate(function):
                hooks.setdefault(name, []).append(function)
                return function
            return decorate
        self.session_deps = dict(self.deps)
        self.session_deps['driftkings.core.hooks'] = module(override=override)
        self.own = source('gameface/battle/own_window.py', self.session_deps)
        # Python 2 restricts metadata writes when source() replaces builtins.
        self.own['setattr'] = lambda target, name, value: setattr(target, name, value)
        return self.own

    def adapter(self, feature=FEATURE):
        """A fresh adapter installed from the real sources."""
        if not hasattr(self, 'own'):
            self.session()
        deps = dict(self.session_deps)
        # Only selected features may import the module; for any other the import would fail here.
        deps['driftkings.gameface.battle'] = module(**({'own_window': module(**dict(
            (key, value) for key, value in self.own.items() if not key.startswith('__')))} if feature in OWN else {}))
        base = source('gameface/battle/common.py', deps)
        base['setattr'] = lambda target, name, value: setattr(target, name, value)
        log, test = self.log, self

        class Adapter(base['BattleCardAdapter']):
            def __init__(self):
                super(Adapter, self).__init__(feature, 'namespace', log, feature, active=True)
                self.positions = []
                self.data = {'text': feature}

            def refresh(self):
                self.publish(dict(self.data), {'locked': False, 'x': -58},
                             self.active and self.visible and self.hudVisible)

            def savePosition(self, child, args):
                self.positions.append(args)
        adapter = Adapter()
        adapter.install()
        return adapter

    def load_hud(self, hud=None):
        """The native HUD loads: every feature's hook runs around the original."""
        hud = hud or self.Hud()
        for hook in self.hooks['_onLoading']:
            self.assertEqual(hook(lambda view, *args: 'native result', hud), 'native result')
        return hud

    def finalize_hud(self, hud):
        calls = []
        for hook in self.hooks['_finalize']:
            self.assertEqual(hook(lambda view, *args: calls.append(view) or 'finalized', hud), 'finalized')
        return calls

    def sent(self, child):
        return [payload for target, payload in self.published if target is child]

    def test_missing_neutral_resource_never_falls_back_to_feature(self):
        self.resources[self.host_resource] = -1
        adapter = self.adapter()
        hud = self.load_hud()
        self.assertEqual(self.Window.created, [])
        self.assertFalse(self.own['_windows'])

    def test_other_battle_cards_keep_the_openwg_child(self):
        for feature in (OTHER, 'test'):
            self.Window.created[:] = []
            del self.injections[:]
            self.session()
            adapter = self.adapter(feature)
            self.assertEqual(sorted(self.hooks), ['_getChildComponents'])
            self.assertFalse(hasattr(adapter, 'ownWindows'))
            factories = self.hooks['_getChildComponents'][0](lambda parent: {}, self.Hud())
            factories[50]()
            self.assertEqual(len(self.injections), 1)  # OpenWG injection still requested
            self.assertEqual(self.Window.created, [])

    def test_real_catalog_selects_all_nine_hud_cards(self):
        import os
        catalog = self.load('interface_catalog').GAMEFACE
        self.assertEqual(sorted(name for name, spec in catalog.items() if spec.get('transport') == 'own_window'),
                         sorted(OWN))
        hud = [name for name, spec in catalog.items() if spec['context'] == 'battle' and name not in OWN]
        self.assertEqual(len(hud), 0)
        self.assertTrue(all('transport' not in catalog[name] for name in hud))
        self.assertEqual(catalog['DriftkingsRatingPlayers']['transport'], 'native_document')
        self.assertNotEqual(catalog[FEATURE]['resource'], catalog[HEALTH]['resource'])
        self.assertNotEqual(catalog[FEATURE]['owner'], catalog[HEALTH]['owner'])
        self.session()
        self.assertNotIn('HOST_FEATURE', self.own)
        adapter = self.adapter()
        hud = self.load_hud()
        self.assertEqual(self.Window.created[-1].content.layoutID, self.host_id)
        # No environment switch remains in the client sources.
        base = os.path.join(os.path.dirname(os.path.abspath(self.load('interface_catalog').__file__)), 'gameface', 'battle')
        for name in ('common.py', 'own_window.py'):
            with open(os.path.join(base, name), 'rb') as stream:
                self.assertNotIn(b'environ', stream.read())

    def test_nine_cards_share_one_window_and_keep_independent_state_across_battles(self):
        adapters = [self.adapter(feature) for feature in OWN]
        hud = self.load_hud()
        self.load_hud(hud)
        self.assertEqual(len(self.Window.created), 1)
        window = self.Window.created[0]
        self.assertEqual(sorted(window.content.children), sorted(self.resources[name] for name in OWN))
        children = [window.content.children[self.resources[feature]] for feature in OWN]
        self.assertEqual(len(set(type(child.model) for child in children)), 9)
        for adapter, child, feature in zip(adapters, children, OWN):
            self.assertIs(adapter.ownWindows[hud], window)
            self.assertEqual(child.layoutID, 0)
            self.assertEqual(child.model.injected, {'properties': 2, 'commands': 1})
            self.assertEqual(child.model.DriftkingsUI.name, feature)
            child._onLoaded()
        for index, (adapter, child) in enumerate(zip(adapters, children)):
            before = [len(self.sent(other)) for other in children]
            child._showCursor(None)
            child._savePosition({'x': index, 'y': index + 10})
            child._visibility(module(ctx={'visible': False}))
            self.assertFalse(self.sent(child)[-1]['config']['visible'])
            child._visibility(module(ctx={'visible': True}))
            self.assertEqual(adapter.positions, [{'x': index, 'y': index + 10}])
            self.assertEqual(self.sent(child)[-1]['text'], OWN[index])
            for other_index, other in enumerate(children):
                if other is not child:
                    self.assertEqual(len(self.sent(other)), before[other_index])
            child._hideCursor(None)
        self.assertEqual(self.injections, [])
        self.finalize_hud(hud)
        self.assertEqual(window.destroyed, 1)
        # The framework finalizes child views as it destroys their parent.
        for child in children:
            child._finalize()
        self.assertTrue(all(not adapter.views for adapter in adapters))
        second = self.load_hud()
        self.assertEqual(len(self.Window.created), 2)
        self.assertEqual(len(adapters[0].ownWindows[second].content.children), 9)
        for adapter in adapters:
            adapter.dispose()
        self.assertEqual(self.Window.created[1].destroyed, 1)
        self.assertFalse(self.own['_cards'])
        self.assertFalse(self.own['_windows'])
        self.assertTrue(all(not adapter.views for adapter in adapters))

    def test_one_window_hosts_two_independent_cards_without_openwg(self):
        strength, health = self.adapter(FEATURE), self.adapter(HEALTH)
        self.assertEqual(sorted(self.hooks), ['_finalize', '_onLoading'])
        self.assertEqual([len(self.hooks[name]) for name in ('_onLoading', '_finalize')], [2, 2])
        self.assertEqual(self.hooks['_onLoading'][0].__module__, type(strength).__module__)
        hud = self.load_hud()
        # Two features, two hooks, one window.
        self.assertEqual(len(self.Window.created), 1)
        window = self.Window.created[0]
        self.assertEqual((window.flags, window.layer, window.loaded), (1 | 1024, 3, 1))
        self.assertEqual(window.content.layoutID, self.host_id)  # the host document, whichever feature opened it
        self.assertIs(strength.ownWindows[hud], window)
        self.assertIs(health.ownWindows[hud], window)
        self.assertEqual(sorted(window.content.children), [42, 43])
        first, second = window.content.children[42], window.content.children[43]
        self.assertIsNot(first, second)
        self.assertIs(strength.views[window.content], first)
        self.assertIs(health.views[window.content], second)
        # Only the root view owns the layout; cards are keyed by their resource and use the empty alias.
        self.assertEqual((first.layoutID, second.layoutID), (0, 0))
        self.assertEqual(self.injections, [])  # no gf_mod_inject for either
        for child, name in ((first, FEATURE), (second, HEALTH)):
            self.assertEqual(sorted(child.getViewModel().properties), ['DriftkingsUI', 'payload'])
            self.assertEqual(child.getViewModel().commands, ['onSavePosition'])
            self.assertEqual(child.getViewModel().DriftkingsUI.name, name)
        self.assertIsNot(first.getViewModel(), second.getViewModel())
        self.assertIsNot(type(first.getViewModel()), type(second.getViewModel()))
        # A repeated native load of the same HUD does not create a second window or new cards.
        self.load_hud(hud)
        self.assertEqual(len(self.Window.created), 1)
        self.assertIs(window.content.children[42], first)
        # Another HUD (next battle) gets its own window with its own two cards.
        other = self.load_hud()
        self.assertEqual(len(self.Window.created), 2)
        self.assertIsNot(strength.ownWindows[other], window)
        self.assertEqual(sorted(self.Window.created[1].content.children), [42, 43])
        self.assertIsNot(self.Window.created[1].content.children[43], second)

    def test_payload_visibility_and_position_are_independent(self):
        strength, health = self.adapter(FEATURE), self.adapter(HEALTH)
        self.load_hud()
        content = self.Window.created[0].content
        first, second = content.children[42], content.children[43]
        first._onLoaded()
        self.assertEqual(self.sent(second), [])  # one card loading does not publish for the other
        second._onLoaded()
        self.assertEqual(self.sent(first)[-1]['text'], FEATURE)
        self.assertEqual(self.sent(second)[-1]['text'], HEALTH)
        # Data and settings of one component reach only its own card.
        before = len(self.sent(second))
        strength.data = {'text': 'Allies 1 : 2 Enemies'}
        strength.onSettingsChanged()
        self.assertEqual(self.sent(first)[-1]['text'], 'Allies 1 : 2 Enemies')
        self.assertEqual(len(self.sent(second)), before)
        strength.setVisible(False)
        self.assertFalse(self.sent(first)[-1]['config']['visible'])
        self.assertTrue(self.sent(second)[-1]['config']['visible'])
        strength.setVisible(True)
        # The V key reaches every card through its own listener; the cursor state is per card.
        for child in (first, second):
            self.assertEqual(len(child._getListeners()), 3)
            child._visibility(module(ctx={'visible': False}))
        self.assertFalse(self.sent(first)[-1]['config']['visible'])
        self.assertFalse(self.sent(second)[-1]['config']['visible'])
        first._visibility(module(ctx={'visible': True}))
        self.assertTrue(self.sent(first)[-1]['config']['visible'])
        self.assertFalse(self.sent(second)[-1]['config']['visible'])
        second._visibility(module(ctx={'visible': True}))
        second._showCursor(None)
        self.assertTrue(self.sent(second)[-1]['config']['draggable'])
        self.assertFalse(self.sent(first)[-1]['config']['draggable'])
        # A dragged position is saved by the component that owns the card.
        second._savePosition({'x': 10, 'y': 20})
        first._savePosition({'x': 1, 'y': 2})
        self.assertEqual(health.positions, [{'x': 10, 'y': 20}])
        self.assertEqual(strength.positions, [{'x': 1, 'y': 2}])

    def test_payloads_match_the_hud_child(self):
        def run(feature):
            self.Window.created[:] = []
            self.session()
            adapter = self.adapter(feature)
            adapter.data = {'text': 'same', 'style': {'size': 16}}
            if feature in OWN:
                self.load_hud()
                child = self.Window.created[0].content.children[self.resources[feature]]
            else:
                parent = self.Hud()
                child = self.hooks['_getChildComponents'][0](lambda view: {}, parent)[50]()
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
            return self.sent(child), adapter.positions
        native = run(OTHER)
        self.assertTrue(native[0])
        for feature in OWN:
            self.assertEqual(run(feature), native)

    def test_window_does_not_depend_on_the_host_feature_being_installed(self):
        adapters = [self.adapter(feature) for feature in OWN if feature != FEATURE]
        hud = self.load_hud()
        window = self.Window.created[0]
        self.assertEqual(window.content.layoutID, self.host_id)
        self.assertEqual(sorted(window.content.children), sorted(self.resources[adapter.feature] for adapter in adapters))
        for adapter in adapters:
            child = window.content.children[self.resources[adapter.feature]]
            child._onLoaded()
            self.assertEqual(self.sent(child)[-1]['text'], adapter.feature)
        self.finalize_hud(hud)
        self.assertEqual(window.destroyed, 1)

    def test_finalize_and_dispose_release_cards_and_the_window(self):
        strength, health = self.adapter(FEATURE), self.adapter(HEALTH)
        first_hud, second_hud = self.load_hud(), self.load_hud()
        one, two = self.Window.created
        # Both features finalize the same HUD: the window is destroyed once, the native finalize runs for each.
        self.assertEqual(len(self.finalize_hud(first_hud)), 2)
        self.assertEqual((one.destroyed, two.destroyed), (1, 0))
        self.assertNotIn(first_hud, strength.ownWindows)
        self.finalize_hud(first_hud)
        self.finalize_hud(self.Hud())  # a HUD that never had a window is left alone
        self.assertEqual((one.destroyed, two.destroyed), (1, 0))
        # Disposing one component removes only its card; the window and the other card stay.
        a, b = two.content.children[42], two.content.children[43]
        b._onLoaded()
        strength.dispose()
        self.assertTrue(a.destroyed)
        self.assertFalse(a.enabled)
        self.assertFalse(b.destroyed)
        self.assertEqual(two.destroyed, 0)
        self.assertEqual(len(strength.views), 0)
        self.assertFalse(strength.installed)
        before = len(self.sent(b))
        health.refresh()
        self.assertEqual(len(self.sent(b)), before + 1)
        self.assertEqual([card[0] for card in self.own['_cards']], [health])
        # The next battle hosts only the remaining card.
        third = self.load_hud()
        self.assertEqual(list(strength.ownWindows[third].content.children), [43])
        # The last component takes every remaining window with it; nothing stays referenced.
        health.dispose()
        self.assertTrue(b.destroyed)
        self.assertEqual(two.destroyed, 1)
        self.assertEqual(len(health.ownWindows), 0)
        self.assertEqual(self.own['_cards'], [])
        self.assertEqual(len(health.views), 0)
        health.dispose()  # idempotent
        self.assertEqual(two.destroyed, 1)

    def test_failures_stay_inside_one_feature(self):
        strength, health = self.adapter(FEATURE), self.adapter(HEALTH)
        # No document resource: no window, the native load still returns.
        self.resources[self.host_resource] = -1
        self.load_hud()
        self.assertEqual(self.Window.created, [])
        self.resources[self.host_resource] = self.host_id
        # A window that fails to load is released and not retained.
        self.fail_load = True
        hud = self.load_hud()
        self.assertTrue(self.Window.created)
        self.assertTrue(all(window.destroyed == 1 for window in self.Window.created))
        self.assertNotIn(hud, strength.ownWindows)
        self.assertIn('exception', [level for level, _ in self.logged])
        self.fail_load = False
        self.Window.created[:] = []
        # One card failing to build does not remove the window or the other card.
        self.fail_feature = HEALTH
        hud = self.load_hud()
        window = strength.ownWindows[hud]
        self.assertEqual(list(window.content.children), [42])
        self.assertEqual(len(health.views), 0)
        child = window.content.children[42]
        child._onLoaded()
        self.assertEqual(self.sent(child)[-1]['text'], FEATURE)
        self.fail_feature = None
        # An unavailable or duplicated card resource skips only that card.
        self.resources[HEALTH] = 42
        self.assertEqual(list(strength.ownWindows[self.load_hud()].content.children), [42])
        self.resources[HEALTH] = -1
        self.assertEqual(list(strength.ownWindows[self.load_hud()].content.children), [42])
        self.resources[HEALTH] = 43
        # A failing destroy does not break the native finalize.
        hud = self.load_hud()
        window = strength.ownWindows[hud]

        def broken():
            raise RuntimeError('destroy failure')
        window.destroy = broken
        self.assertEqual(len(self.finalize_hud(hud)), 2)
        self.assertNotIn(hud, strength.ownWindows)
        # A card finalized by the framework leaves its adapter without stale views.
        hud = self.load_hud()
        content = strength.ownWindows[hud].content
        content.children[43]._finalize()
        self.assertNotIn(content, health.views)
        self.assertIn(content, strength.views)


    def test_repeated_install_and_loading_preserve_one_window_and_nine_models(self):
        adapters = [self.adapter(feature) for feature in OWN]
        before = dict((name, len(handlers)) for name, handlers in self.hooks.items())
        for adapter in adapters:
            adapter.install()
        self.assertEqual(dict((name, len(handlers)) for name, handlers in self.hooks.items()), before)
        hud = self.load_hud()
        self.load_hud(hud)
        self.assertEqual(len(self.Window.created), 1)
        window = self.Window.created[0]
        self.assertEqual((window.flags, window.layer), (1025, 3))
        self.assertEqual(len(window.content.children), 9)
        for child in window.content.children.values():
            self.assertEqual(child.layoutID, 0)  # only the host loads HTML
            self.assertEqual(child.model.properties, ['payload', 'DriftkingsUI'])
            self.assertEqual(child.model.commands, ['onSavePosition'])
        self.assertEqual(self.injections, [])

    def test_before_dispose_error_does_not_block_other_cleanup(self):
        strength, health = self.adapter(FEATURE), self.adapter(HEALTH)
        hud = self.load_hud()
        window = self.Window.created[0]
        first, second = window.content.children[42], window.content.children[43]
        first._onLoaded()
        second._onLoaded()
        attempts = []

        def broken():
            attempts.append('beforeDispose')
            raise RuntimeError('beforeDispose failure')
        strength.beforeDispose = broken
        strength.dispose()
        self.assertFalse(strength.installed)
        self.assertTrue(first.destroyed)
        self.assertEqual(len(strength.views), 0)
        self.assertEqual(strength._disposeFailures, ['beforeDispose'])
        self.assertEqual([event for event, _ in self.settings_signals], ['connect', 'connect', 'disconnect'])
        self.assertEqual([card[0] for card in self.own['_cards']], [health])
        before = len(self.sent(second))
        health.refresh()
        self.assertEqual(len(self.sent(second)), before + 1)
        self.assertIn(hud, self.own['_windows'])
        strength.dispose()
        self.assertEqual(attempts, ['beforeDispose'])
        health.dispose()
        self.assertTrue(second.destroyed)
        self.assertEqual(self.own['_cards'], [])
        self.assertEqual(window.destroyed, 1)

    def test_child_destroy_error_does_not_block_bookkeeping_or_other_cards(self):
        strength, health = self.adapter(FEATURE), self.adapter(HEALTH)
        hud = self.load_hud()
        window = self.Window.created[0]
        first, second = window.content.children[42], window.content.children[43]
        attempts = []

        def broken():
            attempts.append('child.destroy')
            raise RuntimeError('child destroy failure')
        first.destroy = broken
        strength.dispose()
        self.assertFalse(first.enabled)
        self.assertFalse(first.destroyed)  # failed release must not be reported as successful
        self.assertFalse(strength.installed)
        self.assertEqual(len(strength.views), 0)
        self.assertEqual(strength._disposeFailures, ['child.destroy'])
        self.assertEqual([card[0] for card in self.own['_cards']], [health])
        self.assertFalse(second.destroyed)
        self.assertIn(hud, self.own['_windows'])
        strength.dispose()
        self.assertEqual(attempts, ['child.destroy'])
        health.dispose()
        self.assertTrue(second.destroyed)
        self.assertEqual(window.destroyed, 1)
        self.assertEqual(strength._disposeFailures, ['child.destroy'])
        self.assertIn('release not confirmed', str(self.logged))

    def test_destroy_failure_drops_handle_and_allows_second_initialization(self):
        """Current policy, not a successful destroy: G3 must decide whether retaining a handle is safer."""
        strength, health = self.adapter(FEATURE), self.adapter(HEALTH)
        hud = self.load_hud()
        old = self.Window.created[0]
        attempts = []

        def broken():
            attempts.append('destroy')
            raise RuntimeError('window destroy failure')
        old.destroy = broken
        self.assertEqual(len(self.finalize_hud(hud)), 2)
        self.assertEqual(attempts, ['destroy'])
        self.assertEqual(old.destroyed, 0)
        self.assertNotIn(hud, self.own['_windows'])
        self.assertIn('exception', [level for level, _ in self.logged])
        # Same native context can be loaded again because the failed window is no longer recorded.
        self.load_hud(hud)
        new = self.own['_windows'][hud]
        self.assertIsNot(old, new)
        self.assertEqual(new.loaded, 1)
        self.assertEqual(len(new.content.children), 2)
        self.assertEqual(old.destroyed, 0)  # no automatic retry, not evidence of resource recovery
        # Explicitly model framework finalization; Window stub does not cascade child finalizers.
        for child in old.content.children.values():
            child._finalize()
        strength.dispose()
        health.dispose()
        self.assertEqual(new.destroyed, 1)

    def test_cleanup_continues_after_before_dispose_error(self):
        """G1-PY-DISPOSE invariant is now an ordinary regression test."""
        adapter = self.adapter()
        self.load_hud()

        def broken():
            raise RuntimeError('beforeDispose failure')
        adapter.beforeDispose = broken
        adapter.dispose()
        self.assertFalse(adapter.installed, 'G3: cleanup must finish despite beforeDispose failure')
        self.assertEqual(adapter.views, {})
        self.assertEqual(self.own['_cards'], [])

    def test_cleanup_continues_after_child_destroy_error(self):
        """G1-PY-CHILD invariant is now an ordinary regression test."""
        adapter = self.adapter()
        self.load_hud()
        child = self.Window.created[0].content.children[42]

        def broken():
            raise RuntimeError('child destroy failure')
        child.destroy = broken
        adapter.dispose()
        self.assertFalse(adapter.installed, 'G3: cleanup bookkeeping must finish after child destroy failure')
        self.assertEqual(adapter.views, {})
        self.assertEqual(self.own['_cards'], [])


    def test_cleanup_attempts_all_children_and_logs_each_independent_failure(self):
        adapter = self.adapter()
        huds = [self.load_hud(), self.load_hud()]
        first, second = [self.Window.created[i].content.children[42] for i in range(2)]
        attempts = []

        def before():
            attempts.append('before')
            raise RuntimeError('before failure')

        def disconnect():
            attempts.append('disconnect')
            raise RuntimeError('disconnect failure')

        def disable(value):
            attempts.append('disable')
            raise RuntimeError('disable failure')

        def destroy():
            attempts.append('destroy')
            raise RuntimeError('destroy failure')
        adapter.beforeDispose, adapter.disconnectSignals = before, disconnect
        first.setEnabled, first.destroy = disable, destroy
        adapter.dispose()
        self.assertTrue(second.destroyed)
        self.assertFalse(first.destroyed)
        self.assertEqual(sorted(adapter._disposeFailures),
                         ['beforeDispose', 'child.destroy', 'child.setEnabled', 'disconnectSignals'])
        failures = [args for level, args in self.logged if level == 'exception']
        self.assertEqual(len(failures), 4)
        self.assertEqual(attempts.count('before'), 1)
        self.assertEqual(attempts.count('disconnect'), 1)
        self.assertEqual(attempts.count('disable'), 1)
        self.assertEqual(attempts.count('destroy'), 1)
        self.assertFalse(adapter.installed)
        self.assertEqual(len(adapter.views), 0)
        self.assertEqual(self.own['_cards'], [])
        self.assertTrue(all(window.destroyed == 1 for window in self.Window.created))
        adapter.dispose()
        self.assertEqual(len(attempts), 4)
        self.assertEqual(len(self.own['_windows']), 0)
        self.assertEqual(len(huds), 2)

    def test_ownership_lookup_failure_does_not_destroy_replacement_or_block_other_parent(self):
        adapter = self.adapter()
        huds = [self.load_hud(), self.load_hud(), self.load_hud()]
        windows = list(self.Window.created)
        first, second, replaced = [window.content.children[42] for window in windows]

        def broken(resource):
            raise RuntimeError('ownership lookup failure')
        windows[0].content.getChildView = broken
        foreign = module(destroy=lambda: self.fail('foreign replacement was destroyed'))
        windows[2].content.children[42] = foreign
        adapter.dispose()
        self.assertFalse(first.destroyed)
        self.assertTrue(second.destroyed)
        self.assertFalse(replaced.destroyed)
        self.assertEqual(adapter._disposeFailures, ['child.ownership'])
        self.assertEqual(adapter.views, {})
        self.assertEqual(len(self.own['_windows']), 0)
        self.assertEqual(len(huds), 3)

    def test_missing_resource_identity_is_diagnosed_without_guessing_child_ownership(self):
        adapter = self.adapter()
        hud = self.load_hud()
        window = self.Window.created[0]
        child = window.content.children[42]

        def broken():
            raise RuntimeError('resource resolution failure')
        adapter.resourceID = broken
        adapter.dispose()
        self.assertFalse(child.destroyed)
        self.assertEqual(adapter._disposeFailures, ['resourceID', 'child.ownership'])
        self.assertIn('release not confirmed', str(self.logged))
        self.assertEqual(adapter.views, {})
        self.assertFalse(adapter.installed)
        self.assertNotIn(hud, self.own['_windows'])
        self.assertEqual(window.destroyed, 1)

    def test_registration_retires_even_if_adapter_dispose_implementation_raises(self):
        self.session()
        attempts = []

        def broken():
            attempts.append('dispose')
            raise RuntimeError('unexpected adapter failure')
        adapter = module(dispose=broken, title='external test adapter', log=self.log)
        self.own['install'](adapter, object)
        adapter.dispose()
        self.assertEqual(self.own['_cards'], [])
        self.assertIn('retiring registration', str(self.logged))
        adapter.dispose()
        self.assertEqual(attempts, ['dispose'])

    def test_multiple_failing_cards_still_retire_the_last_shared_window(self):
        adapters = [self.adapter(feature) for feature in OWN]
        hud = self.load_hud()
        window = self.Window.created[0]

        def broken():
            raise RuntimeError('injected failure')
        adapters[0].beforeDispose = broken
        window.content.children[self.resources[OWN[1]]].destroy = broken
        adapters[2].disconnectSignals = broken
        for adapter in adapters:
            adapter.dispose()
        self.assertEqual(self.own['_cards'], [])
        self.assertNotIn(hud, self.own['_windows'])
        self.assertEqual(window.destroyed, 1)
        self.assertTrue(all(not adapter.installed and not adapter.views for adapter in adapters))
        self.assertTrue(all(window.content.children[self.resources[name]].destroyed for name in OWN[2:]))
        for adapter in adapters:
            adapter.dispose()
        self.assertEqual(window.destroyed, 1)

    def test_reentrant_dispose_does_not_destroy_the_host_twice(self):
        adapter = self.adapter()
        hud = self.load_hud()
        window = self.Window.created[0]
        child = window.content.children[42]
        original = child.destroy

        def destroy():
            adapter.dispose()
            original()
        child.destroy = destroy
        adapter.dispose()
        self.assertTrue(child.destroyed)
        self.assertEqual(window.destroyed, 1)
        self.assertEqual(self.own['_cards'], [])
        self.assertNotIn(hud, self.own['_windows'])

    def test_failed_window_destroy_does_not_block_other_windows_or_retry(self):
        adapter = self.adapter()
        huds = [self.load_hud(), self.load_hud()]
        first, second = self.Window.created
        attempts = []

        def broken():
            attempts.append('window.destroy')
            raise RuntimeError('window destroy failure')
        first.destroy = broken
        adapter.dispose()
        self.assertEqual(first.destroyed, 0)
        self.assertEqual(second.destroyed, 1)
        self.assertEqual(len(self.own['_windows']), 0)
        self.assertEqual(self.own['_cards'], [])
        self.assertIn('handle removed without retry', str(self.logged))
        self.assertIn('window release not confirmed', str(self.logged))
        adapter.dispose()
        for hud in huds:
            self.finalize_hud(hud)
        self.assertEqual(attempts, ['window.destroy'])
        self.assertEqual(second.destroyed, 1)
