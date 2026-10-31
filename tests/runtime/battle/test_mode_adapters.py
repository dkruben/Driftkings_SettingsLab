# -*- coding: utf-8 -*-
"""Mode adapters: random keeps the current panels, other modes leave the native views intact."""
from support import RuntimeTest
from support.rosters import Harness, battle, halloween, vehicle_type


class AdapterTableTests(RuntimeTest):
    def setUp(self):
        super(AdapterTableTests, self).setUp()
        self.adapters = self.load('core.mode_adapters')

    def test_random_supports_every_screen_with_the_classic_panel(self):
        random = self.adapters.adapter_for('random')
        self.assertEqual((random.loading, random.panel, random.tab, random.enemies, random.order),
                         (True, True, 'classic', True, 'native'))
        self.assertFalse(random.event_numbers)
        self.assertEqual(random.team_size, 30)
        self.assertEqual(random.panel_modes, self.load('settings.settings_data').PROFILES)

    def test_halloween_is_allies_only_with_numbers_in_its_own_tab_only(self):
        adapter = self.adapters.adapter_for('halloween')
        self.assertEqual((adapter.enemies, adapter.team_size, adapter.panel_modes, adapter.order),
                         (False, 5, (), 'mod'))
        self.assertEqual((adapter.loading, adapter.panel, adapter.tab), (False, False, 'halloween'))
        self.assertTrue(adapter.event_numbers)

    def test_modes_without_adapter_are_disabled(self):
        for mode in ('comp7', 'event', 'white_tiger', 'special', 'unknown', 'hangar', None):
            self.assertIsNone(self.adapters.adapter_for(mode), mode)

    def test_frontline_uses_its_native_tables_without_classic_panel_modes(self):
        adapter = self.adapters.adapter_for('frontline')
        self.assertEqual((adapter.loading, adapter.panel, adapter.tab, adapter.team_size), (True, False, 'frontline', 30))
        self.assertEqual((adapter.panel_modes, adapter.order, adapter.enemies), ((), 'native', True))

    def test_black_signal_and_stronghold_use_explicit_native_adapters(self):
        for mode, tab, maximum in (('fort_rush', 'classic', 7), ('stronghold', 'flash', 15)):
            adapter = self.adapters.adapter_for(mode)
            self.assertEqual((adapter.loading, adapter.panel, adapter.tab, adapter.team_size), (True, True, tab, maximum))
            self.assertEqual(adapter.panel_modes, self.adapters.CLASSIC_PANEL_MODES)
            self.assertEqual(adapter.order, 'native')
        self.assertTrue(self.adapters.adapter_for('fort_rush').event_numbers)


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
        for mode in ('halloween', 'comp7', 'frontline'):
            views = self.harness(mode).views
            panel, calls = self.panel()
            views.nativeMode(lambda panel, mode: None, panel, 3)
            self.assertEqual((views.model.mode, views.baseMode, views.panel), ('large', 4, None), mode)
            views.initialMode(lambda panel: None, panel)
            self.assertEqual(calls, [], mode)
            self.assertEqual(views.nativeHover(lambda panel, mode: 'native', panel, 4), 'native', mode)


class ScreenGateTests(RuntimeTest):
    def test_black_signal_and_stronghold_keep_both_teams_ratings_and_tier_eleven(self):
        for mode, tab in (('fort_rush', 'classic'), ('stronghold', 'flash')):
            vehicles = battle(7, 7)
            vehicles[1]['vehicleType'] = vehicle_type('Tier XI', 'heavyTank', level=11)
            harness = Harness(self, vehicles, mode)
            left = sorted(ident for ident, vehicle in vehicles.items() if vehicle['team'] == 1)
            right = sorted(ident for ident, vehicle in vehicles.items() if vehicle['team'] == 2)
            harness.views.captureOrder(lambda controller, data: None, None,
                                       {'leftItemsIDs': left, 'rightItemsIDs': right})
            harness.tick()
            payload = harness.views.lastPayload
            self.assertTrue(payload['enabled'])
            self.assertEqual(len(payload['rows']), 14)
            self.assertEqual(sum(row['ally'] for row in payload['rows']), 7)
            self.assertEqual(harness.watched[-1], tab)
            self.assertFalse(harness.views.model.restricted)
            self.assertTrue(all(row['panels'] and row['loading']['enabled'] and row['tab']['enabled'] for row in payload['rows']))
            values = harness.views.contextCache[1][1]
            self.assertEqual((values['rlevel'], values['r']), ('XI', 1800))
            self.assertEqual(harness.views.failures, {})

    def test_seasonal_adapters_are_cleared_at_battle_end_and_not_reused_in_other_modes(self):
        for mode in ('frontline', 'fort_rush', 'stronghold'):
            harness = Harness(self, battle(7, 7), mode)
            harness.tick()
            views = harness.views
            pending = views.callback
            cleared = []
            views.gameface.clear = lambda: cleared.append(True)
            views.end()
            self.assertIn(pending, harness.cancelled)
            self.assertEqual(harness.sent[-1], {'enabled': False, 'rows': []})
            self.assertEqual(cleared, [True])
            self.assertIsNone(views.callback)
            self.assertIsNone(views.adapter)
            self.assertIsNone(views.lastPayload)
            self.assertFalse(views.rowCache or views.contextCache or views.screenCache or views.model.vehicles)
            views.end()  # Cleanup is idempotent; no callback is cancelled twice.
            self.assertEqual(harness.cancelled.count(pending), 1)
            harness.player.arena = harness.arena = type(harness.arena)('next')
            harness.arena.vehicles, harness.arena.statistics, harness.arena.guiType = battle(7, 7), {}, 1
            harness.mode = 'unknown'
            views.view = harness.view
            harness.tick()
            self.assertEqual((views.lastPayload['enabled'], views.lastPayload['rows']), (False, []))

    def test_black_signal_respawn_updates_the_classic_panels_without_old_health(self):
        harness = Harness(self, battle(7, 7), 'fort_rush')
        harness.tick()
        harness.views.killed(1)
        harness.arena.vehicles[1]['isAlive'] = False
        harness.tick()
        self.assertEqual(harness.views.contextCache[1][1]['hp'], 0)
        harness.arena.vehicles[1].update(isAlive=True, vehicleType=vehicle_type('Respawn', 'mediumTank', health=1900, descr=321))
        harness.tick()
        values = harness.views.contextCache[1][1]
        self.assertEqual((values['vehicle-short'], values['hp'], values['r']), ('Respawn', 1900, 1800))
        self.assertEqual(values['alive'], 'alive')
        self.assertNotEqual(harness.views.model.spotted.get(1), 'dead')
        harness.arena.vehicles[901] = harness.arena.vehicles.pop(1)
        harness.player.playerVehicleID = 901
        harness.tick()
        self.assertEqual(set(row['id'] for row in harness.views.lastPayload['rows']), set(harness.arena.vehicles))
        self.assertEqual(harness.views.contextCache[901][1]['player'], 'pl')

    def test_frontline_tables_contain_both_teams_and_keep_account_identity(self):
        harness = Harness(self, battle(30, 30), 'frontline')
        payload = harness.tick()
        self.assertTrue(payload['enabled'])
        self.assertEqual(payload['tableMode'], 'frontline')
        self.assertEqual(len(payload['rows']), 60)
        self.assertEqual(sum(row['ally'] for row in payload['rows']), 30)
        self.assertFalse(harness.views.model.restricted)
        for row in payload['rows']:
            self.assertEqual(row['panels'], {})
            self.assertEqual(row['accountDBID'], harness.arena.vehicles[row['id']]['accountDBID'])
            self.assertTrue(row['loading']['enabled'])
            self.assertTrue(row['tab']['enabled'])
        harness.data['enabled'] = False
        self.assertFalse(harness.tick()['enabled'])

    def test_frontline_respawn_replaces_vehicle_and_clears_previous_life_health(self):
        harness = Harness(self, battle(30, 30), 'frontline')
        harness.data['tab']['formatLeftVehicle'] = '{{vehicle}} {{hp}} {{r}}'
        harness.tick()
        harness.views.killed(1)
        harness.arena.vehicles[1]['isAlive'] = False
        harness.tick()
        harness.arena.vehicles[1].update(isAlive=True, vehicleType=vehicle_type('Replacement', 'heavyTank', health=2400, descr=999))
        harness.tick()
        row = next(row for row in harness.views.lastPayload['rows'] if row['id'] == 1)
        self.assertIn('Replacement 2400 1800', row['tab']['formatLeftVehicle'])
        self.assertNotIn(1, harness.views.model.health)
        self.assertNotIn(1, harness.views.model.spotted)
        # A new entity ID still belongs to the same account, with no stale old row.
        harness.arena.vehicles[901] = harness.arena.vehicles.pop(1)
        harness.player.playerVehicleID = 901
        harness.tick()
        rows = harness.views.lastPayload['rows']
        self.assertEqual(len(rows), 60)
        self.assertNotIn(1, [row['id'] for row in rows])
        self.assertEqual(next(row for row in rows if row['id'] == 901)['accountDBID'], 10001)

    def test_random_payload_is_unchanged(self):
        harness = Harness(self, battle(15, 15), 'random')
        payload = harness.tick()
        self.assertTrue(payload['enabled'])
        self.assertEqual(len(payload['rows']), 30)
        self.assertEqual(harness.gameface[-1][0], True)
        self.assertEqual(harness.watched[-1], 'classic')
        self.assertNotIn('summary', payload['rows'][0])

    def test_halloween_sends_the_tab_but_no_flash_rows(self):
        harness = Harness(self, halloween(), 'halloween')
        payload = harness.tick()
        self.assertEqual((payload['enabled'], payload['rows']), (False, []))
        enabled, rows = harness.gameface[-1]
        self.assertTrue(enabled)
        self.assertEqual(sorted(row['id'] for row in rows), [1, 2, 3, 4, 5, 6])
        self.assertEqual(harness.watched[-1], 'halloween')

    def test_unsupported_modes_send_nothing_to_draw(self):
        for mode, vehicles in (('comp7', battle(7, 7)), ('unknown', battle(15, 15))):
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

    def test_random_keeps_the_exchange_order_and_enemies(self):
        harness = Harness(self, battle(15, 15), 'random')
        left = sorted((ident for ident, vehicle in harness.arena.vehicles.items() if vehicle['team'] == 1),
                      reverse=True)
        right = sorted(ident for ident, vehicle in harness.arena.vehicles.items() if vehicle['team'] == 2)
        harness.views.captureOrder(lambda controller, data: None, None,
                                   {'leftItemsIDs': left, 'rightItemsIDs': right})
        rows = dict((row['id'], row) for row in harness.views.rows(None, ('panel',)))
        self.assertEqual([rows[ident]['index'] for ident in left], list(range(15)))
        self.assertEqual([rows[ident]['index'] for ident in right], list(range(15)))
        self.assertEqual(set(rows[1]['panels']), set(harness.data['profiles']))
