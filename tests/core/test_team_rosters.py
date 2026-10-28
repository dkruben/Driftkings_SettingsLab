# -*- coding: utf-8 -*-
"""Team panels over fake rosters: 15 vs 15, 30 vs 30 and Halloween with bots (accountDBID 0)."""
from support import RuntimeTest
from rosters import Harness, battle, halloween


def by_id(rows):
    return dict((row['id'], row) for row in rows)


class RandomRosterTests(RuntimeTest):
    def exchange(self, harness):
        teams = {}
        for ident, vehicle in harness.arena.vehicles.items():
            teams.setdefault(vehicle['team'], []).append(ident)
        left, right = sorted(teams[1], reverse=True), sorted(teams[2])
        harness.views.captureOrder(lambda controller, data: None, None,
                                   {'leftItemsIDs': left, 'rightItemsIDs': right})
        return left, right

    def check(self, allies, enemies):
        harness = Harness(self, battle(allies, enemies), 'random')
        left, right = self.exchange(harness)
        payload = harness.tick()
        rows = by_id(payload['rows'])
        self.assertTrue(payload['enabled'])
        self.assertEqual(len(rows), allies + enemies)
        self.assertEqual(sum(1 for row in rows.values() if row['ally']), allies)
        self.assertEqual([rows[ident]['index'] for ident in left], list(range(allies)))
        self.assertEqual([rows[ident]['index'] for ident in right], list(range(enemies)))
        # Every player has statistics; a tick resolves the current classic profile.
        self.assertTrue(all(harness.views.contextCache[ident][1]['stat-available'] == 'stat' for ident in rows))
        self.assertTrue(all(list(row['panels']) == ['large'] for row in rows.values()))
        self.assertEqual(payload['mode'], 'large')
        self.assertEqual(harness.views.failures, {})
        return harness

    def test_15_vs_15(self):
        self.check(15, 15)

    def test_30_vs_30_is_not_truncated(self):
        harness = self.check(30, 30)
        self.assertLessEqual(30, harness.views.adapter.team_size)

    def test_30_vs_30_frontline_stays_native(self):
        harness = Harness(self, battle(30, 30), 'frontline')
        payload = harness.tick()
        self.assertEqual((payload['enabled'], payload['rows']), (False, []))


class HalloweenRosterTests(RuntimeTest):
    def test_five_allies_and_bots(self):
        for bots in (0, 8, 30):
            harness = Harness(self, halloween(bots), 'halloween')
            rows = by_id(harness.views.rows(None, ('panel', 'loading', 'tab')))
            # 5 players and the allied bot; enemy bots and the boss are left out.
            self.assertEqual(sorted(rows), [1, 2, 3, 4, 5, 6], bots)
            context = harness.views.contextCache
            self.assertEqual([ident for ident in rows if context[ident][1]['stat-color'] == 'stat'],
                             [1, 2, 3, 4, 5], bots)
            self.assertEqual(harness.views.failures, {})

    def test_statistics_lookup_of_mode_entities_returns_nothing(self):
        harness = Harness(self, halloween(), 'halloween')
        self.assertIsNone(harness.stats.getPlayersInfo(0))
        harness.views.rows(None, ('panel',))
        self.assertEqual(harness.views.contextCache[6][1]['stat-available'], '')

    def test_halloween_ticks_never_draw_the_flash_panel(self):
        harness = Harness(self, halloween(), 'halloween')
        for _ in range(3):
            payload = harness.tick()
            self.assertEqual((payload['enabled'], payload['rows']), (False, []))
        self.assertEqual(len(harness.sent), 1)
        # Only the TAB table receives the allies.
        self.assertEqual([len(rows) for enabled, rows in harness.gameface], [6, 6, 6])
        self.assertNotIn('medium2', [payload['mode'] for payload in harness.sent])
