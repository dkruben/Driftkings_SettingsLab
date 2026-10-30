# -*- coding: utf-8 -*-
"""Hangar marks of excellence: progress history, trend, WN8 and the achievement tooltip."""
from support import RuntimeTest, Settings, game_source, module

REAL = ('driftkings._constants', 'driftkings.common.utils.numbers', 'driftkings.core.marks_calculator',
        'driftkings.common.utils.colorratting')


class Stats(object):
    def __init__(self, battles=100, damage=1500.0, spot=1.2, frags=0.9, defence=0.6):
        self.values = dict(battles=battles, damage=damage, spot=spot, frags=frags, defence=defence)

    def getBattlesCount(self):
        return self.values['battles']

    def getAvgDamage(self):
        return self.values['damage']

    def getAvgEnemiesSpotted(self):
        return self.values['spot']

    def getAvgFrags(self):
        return self.values['frags']

    def getDroppedCapturePoints(self):
        return None

    def _getAvgValue(self, total, part):
        return self.values['defence']


class HangarMarksTests(RuntimeTest):
    def setUp(self):
        super(HangarMarksTests, self).setUp()
        self.data = {'enabled': True, 'showInStatistic': True, 'historyBattles': 10, 'colorRating': 0}
        self.saved, self.account = {}, 77
        self.expected = {'wn8expDamage': 1500.0, 'wn8expSpot': 1.2, 'wn8expFrag': 0.9, 'wn8expDef': 0.6, 'wn8expWinRate': 52.0}

        def load_json(component, name, default, path, save=False, quiet=False):
            if save:
                self.saved[name] = default
                return default
            return self.saved.get(name, default)

        self.api, self.hooks = game_source('lobby/hangar_marks_of_excellence.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'driftkings.common.config.json_reader': module(loadJson=load_json),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: module(databaseID=self.account)),
            'driftkings.common.utils.exceptions': module(log_exceptions=lambda function: function),
            'driftkings.stats.vehinfo': module(getVehicleInfoData=lambda cd: self.expected if cd == 1 else None),
            'gui.Scaleform.daapi.view.lobby.profile.ProfileUtils': module(ProfileUtils=module(getValueOrUnavailable=lambda value: value)),
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: {'resource': 'resource'}),
            'driftkings.core.cache': module(cache_directory=lambda name: 'cache'),
        }, real=REAL)

    def test_one_snapshot_per_battle_counter(self):
        record = self.api['record_snapshot']
        history = {}
        self.assertTrue(record(history, 5, 10, 50.0, 1200))
        self.assertFalse(record(history, 5, 10, 50.0, 1200))
        self.assertTrue(record(history, 5, 10, 51.0, 1210))
        self.assertTrue(record(history, 5, 11, 52.0, 1220))
        self.assertEqual([p['battles'] for p in history['vehicles']['5']], [10, 11])
        # Out-of-range and missing values are clamped rather than stored.
        record(history, 5, 12, 140.0, float('nan'))
        self.assertEqual(history['vehicles']['5'][-1], {'battles': 12, 'percent': 100.0, 'average': 0.0})

    def test_a_lower_counter_starts_a_new_history_and_only_21_points_are_kept(self):
        record = self.api['record_snapshot']
        history = {}
        for battles in range(30):
            record(history, 'tank', battles, battles, 1000)
        self.assertEqual(len(history['vehicles']['tank']), 21)
        record(history, 'tank', 3, 1.0, 1000)
        self.assertEqual(history['vehicles']['tank'], [{'battles': 3, 'percent': 1.0, 'average': 1000.0}])

    def test_trend_covers_the_requested_battles(self):
        record, trend = self.api['record_snapshot'], self.api['trend']
        history = {}
        self.assertEqual(trend(history, 1)['delta'], None)
        for battles, percent in ((0, 60.0), (4, 62.0), (8, 63.5), (12, 65.0), (14, 64.0)):
            record(history, 1, battles, percent, 2000)
        result = trend(history, 1, last_battles=10)
        self.assertEqual((result['battles'], result['delta']), (10, 2.0))
        self.assertEqual(result['points'], [62.0, 63.5, 65.0, 64.0])
        self.assertEqual(trend(history, 1, last_battles=0)['battles'], 2)

    def test_wn8_matches_the_reference_formula(self):
        data = self.api['g_data']
        vehicle = module(intCD=1)
        # Every ratio at 1.0 gives 980 + 210 + 155 + 75 + 145.
        self.assertEqual(data._calculate_wn8(vehicle, Stats(), 52.0), 1565)
        # Damage below 22% of the expected value leaves only the win rate: 145 * (40/52 - 0.71) / 0.29.
        self.assertEqual(data._calculate_wn8(vehicle, Stats(damage=300.0, spot=0, frags=0, defence=0), 40.0), 29)
        self.assertEqual(data._calculate_wn8(vehicle, Stats(battles=0), 52.0), 0)
        self.assertEqual(data._calculate_wn8(module(intCD=2), Stats(), 52.0), 0)
        self.expected['wn8expDef'] = 0
        self.assertEqual(data._calculate_wn8(vehicle, Stats(), 52.0), 0)

    def test_mastery_labels_and_safe_numbers(self):
        data = self.api['g_data']
        self.assertEqual([data._mastery_label(value) for value in (4, 1, 0, None)], ['Ace Tanker', '3rd class', '--', '--'])
        self.assertEqual((data._safe(float('nan'), 3.0), data._safe(None, 2), data._safe(5)), (3.0, 2, 5))
        mastery = module(isInDossier=lambda: True, getValue=lambda: 4, getSmallIcon=lambda: '../maps/ace.png')
        dossier = module(getTotalStats=lambda: module(getAchievement=lambda record: mastery))
        self.assertEqual(data._get_mastery_info(dossier), {'value': 4, 'icon': 'img://maps/ace.png'})
        self.assertEqual(data._get_mastery_info(None), {'value': 0, 'icon': ''})

    def test_history_is_loaded_per_account_and_saved_on_change(self):
        self.saved['progress_77'] = {'vehicles': {'9': [{'battles': 1, 'percent': 40.0, 'average': 900}, 'broken']}}
        history = self.api['ProgressHistory']()
        sample = {'vehicleID': 9, 'randomBattles': 12, 'damageRating': 45.0, 'movingAvgDamage': 950}
        result = history.observe(sample)
        self.assertEqual((result['battles'], result['delta']), (11, 5.0))
        self.assertEqual(len(self.saved['progress_77']['vehicles']['9']), 2)
        self.account = None
        self.assertEqual(history.observe(sample), {'delta': None, 'battles': 0})

    def test_achievement_tooltip_only_when_enabled(self):
        condition = self.hooks.get('MarkOnGunAchievement', 'getUserCondition')
        self.api['getAchievementDossier'] = lambda achievement: 'dossier'
        self.api['g_data'].build_tooltip = lambda dossier: 'tooltip'
        self.assertEqual(condition(lambda *args: 'native', 'achievement'), 'tooltip')
        self.data['showInStatistic'] = False
        self.assertEqual(condition(lambda *args: 'native', 'achievement'), 'native')
