# -*- coding: utf-8 -*-
"""Halloween roster: allies only, sorted by the mod, mode entities without statistics."""
from support import RuntimeTest
from rosters import Harness, halloween

# Alive first, then heavy, medium, TD, light; vehicle name, then player name.
# Dora (E100) < anna (Maus), Zed (Leopard), Ally Bot (Pumpkin), carl (Bat); Bob is dead.
EXPECTED = [5, 2, 1, 6, 4, 3]


class HalloweenOrderTests(RuntimeTest):
    def setUp(self):
        super(HalloweenOrderTests, self).setUp()
        self.adapters = self.load('core.mode_adapters')

    def test_native_sort_key_order(self):
        allies = dict((ident, vehicle) for ident, vehicle in halloween().items() if vehicle['team'] == 1)
        self.assertEqual(self.adapters.roster_order(allies), EXPECTED)

    def test_names_compare_without_case_and_missing_data_sorts_last(self):
        vehicles = halloween()
        order = self.adapters.roster_order({2: vehicles[2], 3: dict(vehicles[2], name='ANNA2'),
                                            7: {'team': 1, 'name': 'odd'}})
        self.assertEqual(order, [2, 3, 7])


class HalloweenRowsTests(RuntimeTest):
    def setUp(self):
        super(HalloweenRowsTests, self).setUp()
        self.harness = Harness(self, halloween(), 'halloween')
        self.views = self.harness.views

    def rows(self):
        return dict((row['id'], row) for row in self.views.rows(None, ('panel', 'loading', 'tab')))

    def test_only_allies_are_resolved(self):
        rows = self.rows()
        self.assertEqual(sorted(rows), [1, 2, 3, 4, 5, 6])
        self.assertTrue(all(row['ally'] for row in rows.values()))
        self.assertEqual(self.views.model.order, {'left': EXPECTED, 'right': []})

    def test_rows_follow_the_mod_order_not_the_exchange(self):
        # HWStatisticsDataController sends its own allies order and an empty enemy side.
        data = {'leftItemsIDs': [1, 2, 3, 4, 5], 'rightItemsIDs': [],
                'leftVehiclesData': [{'vehicleID': 2, 'playerStatus': 4}]}
        self.views.captureOrder(lambda controller, data: None, None, data)
        rows = self.rows()
        self.assertEqual([rows[ident]['index'] for ident in EXPECTED], list(range(6)))
        # Exchange metadata (squad, badges, user tags) is still used.
        self.assertEqual(self.views.model.metadata[2]['playerStatus'], 4)

    def test_a_death_moves_the_player_down(self):
        self.rows()
        self.harness.arena.vehicles[5]['isAlive'] = False
        rows = self.rows()
        order = sorted(rows, key=lambda ident: rows[ident]['index'])
        self.assertEqual(order, [2, 1, 6, 4, 5, 3])

    def test_mode_entities_have_no_statistics_and_no_error(self):
        rows = self.rows()
        bot = self.views.contextCache[6][1]
        player = self.views.contextCache[2][1]
        self.assertEqual((bot['stat-available'], bot['stat-color'], bot['r']), ('', '', None))
        self.assertEqual((player['stat-available'], player['stat-color'], player['r']), ('', 'stat', None))
        self.assertEqual(rows[6]['name'], 'Ally Bot')
        self.assertEqual(self.views.failures, {})

    def test_classic_panel_profiles_are_not_resolved(self):
        rows = self.rows()
        self.assertTrue(all(row['panels'] == {} for row in rows.values()))
        self.assertEqual(self.views.model.mode, 'large')

    def test_nothing_is_drawn_over_the_native_panel(self):
        payload = self.harness.tick()
        self.assertEqual((payload['enabled'], payload['rows']), (False, []))
        self.assertEqual(self.harness.gameface[-1], (False, []))
