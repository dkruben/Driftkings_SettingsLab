# -*- coding: utf-8 -*-
"""Halloween TAB (TabScreen): the roster bridge must not attach to it nor write into it."""
import io
import os

from support import CLIENT, Hooks, RuntimeTest, module, source


class View(object):
    def __init__(self):
        self.children = {}
        self.showingStatus = 'SHOWN'

    def setChildView(self, resource, child):
        self.children[resource] = child

    def getChildView(self, resource):
        return self.children.get(resource)


class GamefaceTabTests(RuntimeTest):
    def bridge(self, supported):
        hooks = Hooks()
        self.refreshes = []
        self.owner = module(active=True, supports=lambda screen: screen in supported,
                            refresh=lambda: self.refreshes.append(1), config=None)

        class TabView(object):
            pass

        api = source('gameface/battle/panel_gameface.py', {
            'frameworks.wulf': module(ViewModel=type('ViewModel', (object,), {'__init__': lambda self, **kwargs: None}),
                                      ViewSettings=lambda resource, model=None: None),
            'frameworks.wulf.gui_constants': module(ShowingStatus=module(SHOWING='SHOWING', SHOWN='SHOWN')),
            'gui.impl.pub': module(ViewImpl=type('ViewImpl', (object,), {'__init__': lambda self, *args: None})),
            'gui.impl.battle.battle_page.tab_view': module(TabView=TabView),
            'driftkings.gameface.core': module(attach_assets=lambda *args: None, resource_id=lambda value: 77),
            'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'tab'}),
            'driftkings.settings.service': module(settings_service=None),
            'driftkings.core.diagnostics': module(diagnostics=module(enabled=False)),
            'driftkings.core.hooks': module(override=hooks.override),
        })
        return api['GamefaceLoading'](self.owner), hooks

    def test_random_tab_gets_the_roster_child(self):
        bridge, hooks = self.bridge(('tab',))
        view = View()
        hooks.get('TabView', '_onLoaded')(lambda view: None, view)
        self.assertEqual(list(view.children), [77])
        self.assertEqual(bridge.active_screens(), set(['tab']))

    def test_halloween_gets_no_child_and_no_writes(self):
        bridge, hooks = self.bridge(())
        view = View()
        hooks.get('TabView', '_onLoaded')(lambda view: None, view)
        self.assertEqual(view.children, {})
        self.assertEqual(bridge.active_screens(), set())
        # update() with no attached view writes nothing anywhere.
        bridge.update(True, [{'id': 1, 'ally': True, 'aliases': [], 'tab': {}}])
        bridge.dispose()
        self.assertEqual(self.refreshes, [])

    def test_only_the_classic_tab_is_hooked(self):
        bridge, hooks = self.bridge(('tab',))
        self.assertEqual(sorted(name for name, _ in hooks.overrides if name != 'TabView'), [])
        path = os.path.join(CLIENT, 'gameface', 'battle', 'panel_gameface.py')
        with io.open(path, encoding='utf-8') as stream:
            text = stream.read()
        for name in ('TabScreen', 'FullEventStatsWindow', 'halloween'):
            self.assertNotIn(name, text)
