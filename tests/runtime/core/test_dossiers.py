# -*- coding: utf-8 -*-
"""Shared vehicle dossier reads used by the marks modules and the carousel."""
from support import RuntimeTest, dossiers, module


def dossier(records=None, mastery=None):
    return module(getRecordValue=lambda block, name: (records or {}).get(name),
                  getTotalStats=lambda: module(getAchievement=lambda record: mastery))


def badge(rank, earned=True):
    return module(getValue=lambda: rank, isInDossier=lambda: earned)


class DossierTests(RuntimeTest):
    def setUp(self):
        super(DossierTests, self).setUp()
        self.api = dossiers()

    def test_total_records_and_damage_rating(self):
        item = dossier({'damageRating': 8550, 'marksOnGun': 2})
        self.assertEqual(self.api.damage_rating(item), 85.5)
        self.assertEqual(self.api.total_record(item, 'marksOnGun'), 2)

    def test_mastery_rank_only_counts_earned_badges(self):
        self.assertEqual(self.api.mastery_rank(dossier(mastery=badge(4))), 4)
        self.assertEqual(self.api.mastery_rank(dossier(mastery=badge(3, earned=False))), 0)
        self.assertEqual(self.api.mastery_rank(dossier()), 0)
        # NO_LVL (5) is not Ace Tanker.
        self.assertEqual(self.api.mastery_rank(dossier(mastery=badge(5))), 0)
        self.assertIsNone(self.api.mastery_achievement(dossier(mastery=badge(2, earned=False))))

    def test_assistance_averages_and_wnx_total(self):
        calls = []
        stats = module(getBattlesCountVer2=lambda: 10, getDamageAssistedTrack=lambda: 1000,
                       getDamageAssistedRadio=lambda: 2000, getDamageAssistedStun=lambda: 500,
                       getAvgDamageAssistedStun=lambda: 50.0,
                       _getAvgValue=lambda total, part: calls.append(part) or part() / float(total()))
        self.assertEqual(self.api.average_assists(stats), (100.0, 200.0, 50.0))
        self.assertEqual(self.api.wnx_assistance(stats), 350.0)
        stats.getDamageAssistedStun = lambda: None
        self.assertIsNone(self.api.wnx_assistance(stats))
