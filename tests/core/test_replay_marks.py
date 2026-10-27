# -*- coding: utf-8 -*-
"""Replays carry no dossier: owner cache first, then any account, then the configured base."""
from support import RuntimeTest

TODAY = 739000


class ReplayMarksTests(RuntimeTest):
    def setUp(self):
        super(ReplayMarksTests, self).setUp()
        self.marks = self.load('core.marks_calculator')
        self.model = self.load('views.marks_model')

    def calibrate(self, cache, owner='1'):
        return self.marks.replay_calibration(cache, owner, 'T-34', 94.0, 3500, TODAY)

    def test_owner_cache_is_exact_and_returned_as_is(self):
        owned = [80.0, 2000.0, 81.0, 2050.0, 1, 2]
        values, approximate = self.calibrate({'1': {'T-34': owned}, '2': {'T-34': [1, 1, 2, 2, 3, 3]}})
        self.assertIs(values, owned)
        self.assertFalse(approximate)

    def test_other_account_is_copied_and_most_recent_wins(self):
        older, newer = [60.0, 1500.0, 61.0, 1520.0, 5, 6], [70.0, 1700.0, 71.0, 1720.0, 8, 9]
        cache = {'1': {}, '2': {'T-34': older}, '3': {'T-34': newer}, '4': {'T-34': [50.0, 900.0, 50.0, 900.0, 9, 99]}}
        values, approximate = self.calibrate(cache)
        self.assertEqual(values, newer)
        self.assertIsNot(values, newer)
        self.assertTrue(approximate)
        self.assertEqual(cache['1'], {})

    def test_four_value_entries_are_padded_with_today(self):
        values, approximate = self.calibrate({'2': {'T-34': [60.0, 1500.0, 61.0, 1520.0]}})
        self.assertEqual(values, [60.0, 1500.0, 61.0, 1520.0, TODAY, TODAY])
        self.assertTrue(approximate)

    def test_configured_base_when_no_cache_has_the_vehicle(self):
        values, approximate = self.calibrate({'1': {'IS-7': [1, 1, 2, 2]}})
        self.assertEqual(values, [0, 0, 94.0, 3500.0, TODAY, TODAY])
        self.assertTrue(approximate)
        # The base reproduces the configured mark when the battle matches the average damage.
        self.assertAlmostEqual(self.marks.battle_estimate(3500, 3500, values), 94.0, places=2)

    def test_degenerate_owner_curve_uses_borrowed_data_without_mutating_cache(self):
        borrowed = [80.0, 2000.0, 81.0, 2050.0, 1, 2]
        for owned in ([81.6, 1002, 81.6, 1012, 1, 2],
                      [80.0, 2000, 81.0, 2000, 1, 2],
                      [80.0, 2100, 81.0, 2000, 1, 2]):
            cache = {'1': {'T-34': owned}, '2': {'T-34': borrowed}}
            values, approximate = self.calibrate(cache)
            self.assertEqual(values, borrowed)
            self.assertTrue(approximate)
            self.assertIs(cache['1']['T-34'], owned)
            self.assertIsNot(values, borrowed)

    def test_flat_borrowed_curve_uses_the_existing_configured_base(self):
        values, approximate = self.calibrate({'2': {'T-34': [58.28, 1200, 58.28, 1210, 1, 2]}})
        self.assertEqual(values, [0, 0, 94.0, 3500.0, TODAY, TODAY])
        self.assertTrue(approximate)

    def test_decreasing_samples_with_a_positive_slope_remain_exact(self):
        owned = [81.0, 2050.0, 80.0, 2000.0, 1, 2]
        values, approximate = self.calibrate({'1': {'T-34': owned}})
        self.assertIs(values, owned)
        self.assertFalse(approximate)

    def test_invalid_base_leaves_the_panel_unavailable(self):
        for percent, damage in ((0, 3500), (94.0, 0), ('bad', 3500), (101, 3500)):
            self.assertEqual(self.marks.replay_calibration({}, '1', 'T-34', percent, damage, TODAY), (None, False))

    def test_model_flags_approximate_only_for_valid_data(self):
        self.assertTrue(self.model.compact_model(1, 94.0, 94.1, 0, (0,), {}, 2, True, True)['approximate'])
        self.assertFalse(self.model.compact_model(1, 94.0, 94.1, 0, (0,), {}, 2, True)['approximate'])
        self.assertFalse(self.model.compact_model(1, None, None, 0, (0,), {}, 2, True, True)['approximate'])
