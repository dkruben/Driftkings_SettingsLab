# -*- coding: utf-8 -*-
import itertools

from support import RuntimeTest


def legacy_reload(reload_orig, clip_size, eq1=1, eq2=1, eq3=1, eq4=1):
    """Verbatim copy of the previous if/elif implementation, kept as a regression oracle."""
    rammer = 0.9 if clip_size == 1 and eq1 == 1 else 1
    if eq2 == 1 and eq3 == 1 and eq4 == 1:
        crew = 1.32
    elif eq2 == 1 and eq3 == 1 and eq4 == 0:
        crew = 1.27
    elif eq2 == 1 and eq3 == 0 and eq4 == 1:
        crew = 1.21
    elif eq2 == 1 and eq3 == 0 and eq4 == 0:
        crew = 1.16
    elif eq2 == 0 and eq3 == 1 and eq4 == 1:
        crew = 1.27
    elif eq2 == 0 and eq3 == 1 and eq4 == 0:
        crew = 1.21
    elif eq2 == 0 and eq3 == 0 and eq4 == 1:
        crew = 1.16
    else:
        crew = 1.1
    return round(reload_orig / (0.57 + 0.43 * crew) * rammer, 2)


class GunStatsTests(RuntimeTest):
    def setUp(self):
        super(GunStatsTests, self).setUp()
        self.stats = self.load('core.gun_stats')

    def test_crew_table_covers_every_combination(self):
        self.assertEqual(len(self.stats.CREW_RELOAD_BONUS), 8)
        self.assertEqual(self.stats.crew_bonus(1, 1, 1), 1.32)
        self.assertEqual(self.stats.crew_bonus(0, 0, 0), 1.10)

    def test_reload_matches_legacy_chain_for_all_equipment_flags(self):
        for reload_time, clip in itertools.product((0.5, 2.3, 3.9, 7.25, 12.0), (1, 2, 5)):
            for flags in itertools.product((0, 1), repeat=4):
                self.assertEqual(self.stats.reload_with_equipment(reload_time, clip, *flags),
                                 legacy_reload(reload_time, clip, *flags), (reload_time, clip, flags))

    def test_non_one_values_count_as_inactive_like_before(self):
        for value in (2, None, -1):
            self.assertEqual(self.stats.crew_bonus(value, 1, 1), 1.27)
            self.assertEqual(self.stats.reload_with_equipment(4.0, 1, value, 1, 1, 1),
                             legacy_reload(4.0, 1, value, 1, 1, 1))

    def test_rammer_only_applies_to_single_shot_guns(self):
        single = self.stats.reload_with_equipment(10.0, 1, 1, 0, 0, 0)
        clipped = self.stats.reload_with_equipment(10.0, 3, 1, 0, 0, 0)
        self.assertAlmostEqual(single, round(clipped * 0.9, 2), places=1)
        self.assertEqual(self.stats.reload_with_equipment(10.0, 1, 0, 0, 0, 0), clipped)

    def test_damage_per_minute_single_shot(self):
        # 400 damage every 8 seconds is 3000 damage per minute.
        self.assertEqual(self.stats.damage_per_minute(8.0, 1, 0.0, 400), 3000)

    def test_damage_per_minute_uses_full_clip_cycle(self):
        # 3 shells, 0.5 s apart, 10 s reload: cycle 11 s, 3 * 200 damage per cycle.
        expected = int(round(3 / 11.0 * 60 * 200, 0))
        self.assertEqual(self.stats.damage_per_minute(10.0, 3, 0.5, 200), expected)

    def test_damage_per_minute_rejects_non_positive_cycle(self):
        self.assertIsNone(self.stats.damage_per_minute(0, 1, 0, 100))
        self.assertIsNone(self.stats.damage_per_minute(-1.0, 1, 0, 100))

    def test_module_has_no_engine_imports(self):
        import inspect
        text = inspect.getsource(self.stats)
        for forbidden in ('BigWorld', 'import Avatar', 'gui.', 'helpers'):
            self.assertNotIn(forbidden, text)


if __name__ == '__main__':
    import unittest
    unittest.main()
