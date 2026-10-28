# -*- coding: utf-8 -*-
"""Mode adapters: random keeps the current panels, other modes leave the native views intact."""
from support import RuntimeTest
from rosters import Harness, battle, halloween


class AdapterTableTests(RuntimeTest):
    def setUp(self):
        super(AdapterTableTests, self).setUp()
        self.adapters = self.load('core.mode_adapters')

    def test_random_supports_every_screen_with_the_classic_panel(self):
        random = self.adapters.adapter_for('random')
        self.assertEqual((random.loading, random.panel, random.tab, random.enemies, random.order),
                         (True, True, True, True, 'native'))
        self.assertEqual(random.team_size, 15)
        self.assertEqual(random.panel_modes, self.load('settings.settings_data').PROFILES)

    def test_halloween_is_allies_only_without_classic_modes_or_drawn_screens(self):
        adapter = self.adapters.adapter_for('halloween')
        self.assertEqual((adapter.enemies, adapter.team_size, adapter.panel_modes, adapter.order),
                         (False, 5, (), 'mod'))
        self.assertEqual((adapter.loading, adapter.panel, adapter.tab), (False, False, False))

    def test_modes_without_adapter_are_disabled(self):
        for mode in ('comp7', 'frontline', 'event', 'white_tiger', 'special', 'unknown', 'hangar', None):
            self.assertIsNone(self.adapters.adapter_for(mode), mode)


class PanelModeHookTests(RuntimeTest):
    """HWPlayersPanel inherits the classic PlayersPanel hooks; they must only pass through."""
    def panel(self):
        calls = []
        panel = type('Panel', (object,), {})()
        panel.as_setPanelModeS = calls.append
        return panel, calls

    def harness(self, mode):
        harness = Harness(self, battle(15, 15) if mode != 'halloween' else halloween(), mode)
        harness.data['playersPanel']['startMode'] = 'short'
        return harness

    def test_random_follows_and_forces_classic_modes(self):
        views = self.harness('random').views
        panel, calls = self.panel()
        views.nativeMode(lambda panel, mode: None, panel, 3)
        self.assertEqual((views.model.mode, views.baseMode), ('medium2', 3))
        views.initialMode(lambda panel: None, panel)
        self.assertEqual(calls, [1])
        self.assertIsNone(views.nativeHover(lambda panel, mode: 'native', panel, 4))

    def test_halloween_and_unsupported_modes_keep_native_modes(self):
        for mode in ('halloween', 'comp7'):
            views = self.harness(mode).views
            panel, calls = self.panel()
            views.nativeMode(lambda panel, mode: None, panel, 3)
            self.assertEqual((views.model.mode, views.baseMode, views.panel), ('large', 4, None), mode)
            views.initialMode(lambda panel: None, panel)
            self.assertEqual(calls, [], mode)
            self.assertEqual(views.nativeHover(lambda panel, mode: 'native', panel, 4), 'native', mode)


class ScreenGateTests(RuntimeTest):
    def test_random_payload_is_unchanged(self):
        harness = Harness(self, battle(15, 15), 'random')
        payload = harness.tick()
        self.assertTrue(payload['enabled'])
        self.assertEqual(len(payload['rows']), 30)
        self.assertEqual(harness.gameface[-1][0], True)

    def test_unsupported_modes_send_nothing_to_draw(self):
        for mode, vehicles in (('halloween', halloween()), ('comp7', battle(7, 7)), ('unknown', battle(15, 15))):
            harness = Harness(self, vehicles, mode)
            payload = harness.tick()
            self.assertEqual((payload['enabled'], payload['rows']), (False, []), mode)
            self.assertEqual(harness.gameface[-1], (False, []), mode)
            # Statistics still load for the markers.
            self.assertEqual(harness.stats.loads, 1, mode)

    def test_the_adapter_follows_the_arena(self):
        harness = Harness(self, battle(15, 15), 'random')
        self.assertTrue(harness.views.supports('panel'))
        harness.mode = 'halloween'
        self.assertTrue(harness.views.supports('panel'))
        harness.player.arena = harness.arena = type(harness.arena)('next')
        harness.arena.vehicles, harness.arena.statistics, harness.arena.guiType = halloween(), {}, 1
        self.assertFalse(harness.views.supports('panel'))
        harness.views.end()
        self.assertIsNone(harness.views.adapter)
