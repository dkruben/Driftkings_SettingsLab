# -*- coding: utf-8 -*-
import itertools

from support import RuntimeTest

DATA = {'ad': 1000.0, 'td': 2500.0, 'af': 1.0, 'tf': 3.0, 'x': [100 * i for i in range(1, 101)]}


def legacy_xte(data, dmg, frg):
    """Verbatim copy of the previous ScaleValues.calculateXTE body (data lookup excluded)."""
    if data is None:
        return -1
    if data['td'] == data['ad'] or data['tf'] == data['af']:
        return -1
    avgD, topD, avgF, topF = float(data['ad']), float(data['td']), float(data['af']), float(data['tf'])
    minD, minF = avgD * 0.4, avgF * 0.4
    d = 1 + (dmg - avgD) / (topD - avgD) if dmg >= avgD else 1 + (dmg - avgD) / (avgD - minD)
    f = 1 + (frg - avgF) / (topF - avgF) if frg >= avgF else 1 + (frg - avgF) / (avgF - minF)
    d, f = max(0, d), max(0, f)
    t = (d * 3.0 + f * 1.0) / 4.0 * 1000.0
    for i, v in enumerate(data['x']):
        if v > t:
            return i
    return 100


class XvmScalesTests(RuntimeTest):
    def setUp(self):
        super(XvmScalesTests, self).setUp()
        self.scales = self.load('core.xvm_scales')

    def test_rank_boundaries(self):
        thresholds = [10, 20, 30]
        self.assertEqual(self.scales.rank(thresholds, 5), 0)
        self.assertEqual(self.scales.rank(thresholds, 10), 1)
        self.assertEqual(self.scales.rank(thresholds, 29.9), 2)
        self.assertEqual(self.scales.rank(thresholds, 30), 100)

    def test_rank_without_usable_thresholds(self):
        for bad in (None, {}, 'x', 5, ['a', None]):
            self.assertEqual(self.scales.rank(bad, 1), -1)

    def test_xte_matches_legacy_implementation(self):
        for dmg, frg in itertools.product((0, 100, 500, 999, 1000, 1500, 2500, 4000), (0, 0.3, 1, 2, 3, 5)):
            self.assertEqual(self.scales.xte(DATA, dmg, frg), legacy_xte(DATA, dmg, frg), (dmg, frg))

    def test_xte_is_monotonic_and_bounded(self):
        ranks = [self.scales.xte(DATA, dmg, 1.0) for dmg in range(0, 6000, 250)]
        self.assertEqual(ranks, sorted(ranks))
        self.assertTrue(all(0 <= value <= 100 for value in ranks))

    def test_xte_rejects_missing_or_degenerate_reference_data(self):
        self.assertEqual(self.scales.xte(None, 1, 1), -1)
        self.assertEqual(self.scales.xte({'ad': 1}, 1, 1), -1)
        self.assertEqual(self.scales.xte(dict(DATA, td=DATA['ad']), 1, 1), -1)
        self.assertEqual(self.scales.xte(dict(DATA, ad='x'), 1, 1), -1)
        self.assertEqual(self.scales.xte(dict(DATA, ad=0, td=0), 1, 1), -1)

    def test_xtdb(self):
        self.assertEqual(self.scales.xtdb({'x': [100, 200]}, 150), 1)
        self.assertEqual(self.scales.xtdb({'x': [100, 200]}, 500), 100)
        self.assertEqual(self.scales.xtdb(None, 1), -1)
        self.assertEqual(self.scales.xtdb({}, 1), -1)


if __name__ == '__main__':
    import unittest
    unittest.main()
