import json
import math
import os

from support import RuntimeTest, Settings, game_source, module


class WnxTests(RuntimeTest):
    def setUp(self):
        super(WnxTests, self).setUp()
        self.api = self.load('core.wnx')
        with open(os.path.join(os.path.dirname(__file__), 'fixtures/wnx_reference.json'), 'rb') as stream:
            self.reference = json.loads(stream.read().decode('utf-8'))
        self.expected = dict(damage=1000, frags=.8, spots=.9, assist=250)

    def test_matches_published_javascript_calculator(self):
        for record in self.reference['ratings']:
            self.assertAlmostEqual(self.api.calculate(*(record['input'] + [self.expected])), record['result'])

    def test_assistance_increases_rating_without_changing_direct_damage(self):
        self.assertGreater(self.api.calculate(1000, 1, 1, 500, self.expected),
                           self.api.calculate(1000, 1, 1, 0, self.expected))

    def test_missing_and_invalid_data_are_not_reported_as_zero(self):
        for value in (None, -1, float('inf'), float('nan'), True, 'bad'):
            self.assertIsNone(self.api.calculate(1000, 1, 1, value, self.expected))
        self.assertIsNone(self.api.calculate(1000, 1, 1, 0, None))
        self.assertIsNone(self.api.calculate(1000, 1, 1, 0, dict(self.expected, damage=0)))
        self.assertEqual(self.api.calculate(0, 0, 0, 0, self.expected), 0)

    def test_overall_weights_expected_values_by_battles_and_skips_unmatched_tanks(self):
        records = [dict(damage=2000, frags=2, spots=2, assistance=1000, battles=2, expected=self.expected),
                   dict(damage=999999, frags=50, spots=50, assistance=99999, battles=20, expected=None)]
        result = self.api.calculate_overall(records)
        exp = dict((key, value * 2) for key, value in self.expected.items())
        self.assertEqual(result, self.api.calculate(2000, 2, 2, 1000, exp, overall=True))
        self.assertIsNone(self.api.calculate_overall([]))

    def test_expected_values_are_unavailable_until_stats_applies_reference(self):
        self.assertIsNone(self.api.get_expected(1))
        self.api.set_reference({'data': {'1': self.expected}})
        self.assertEqual(self.api.get_expected(1), self.expected)
        self.assertIsNone(self.api.get_expected(0))
        with self.assertRaises(ValueError):
            self.api.set_reference({'data': {}})
        self.assertEqual(self.api.get_expected(1), self.expected)

    def test_public_page_parser_rejects_partial_or_changed_pages(self):
        row = b'{tank_id:1,name:"Example",expected_damage:1000,expected_frags:0.8,expected_spots:0.9,expected_assistance:250}'
        document = self.api.parse_reference_page(row, minimum=1)
        self.assertEqual(document['data']['1'], self.expected)
        for body in (b'<html>offline</html>', row.replace(b'1000', b'-1')):
            with self.assertRaises(ValueError):
                self.api.parse_reference_page(body, minimum=1)
        with self.assertRaises(ValueError):
            self.api.parse_reference_page(row)  # A partial page must not replace the full cache.

    def test_tomato_gradient_matches_published_javascript(self):
        colors = self.load('common.utils.colorratting')
        self.assertEqual(colors.color_tables[3]['ScaleColor'], 'Tomato.gg')
        for record in self.reference['colors']:
            for metric in ('wn8', 'wnx'):
                self.assertEqual(colors.getStatisticColor(metric, record['value'], 3), record[metric])
        self.assertEqual(colors.getStatisticColor('wnx', None, 3), '#CCCCCC')

    def test_existing_palettes_can_color_a_real_wnx_value(self):
        colors = self.load('common.utils.colorratting')
        for palette in range(3):
            self.assertEqual(colors.getStatisticColor('wnx', 1500, palette),
                             colors.getStatisticColor('wn8', 1500, palette))

    def test_carousel_calculates_wnx_from_native_vehicle_dossier(self):
        stats = module(**dict((name, lambda value=value: value) for name, value in {
            'getBattlesCount': 10, 'getBattlesCountVer2': 10, 'getAvgDamage': 1000,
            'getAvgDamageReceived': 500, 'getDamageAssistedEfficiency': 300,
            'getAvgDamageBlocked': 0, 'getAvgDamageAssistedStun': 50, 'getAvgFrags': 1,
            'getAvgEnemiesSpotted': 1, 'getWinsEfficiency': .5, 'getHitsCount': 10,
            'getShotsCount': 20, 'getCapturePoints': 0, 'getDroppedCapturePoints': 0,
            'getDamageAssistedRadio': 2000, 'getDamageAssistedTrack': 1000,
            'getDamageAssistedStun': 500}.items()))
        dossier = module(getRandomStats=lambda: stats, getRecordValue=lambda *args: 0,
                         getTotalStats=lambda: module(getAchievement=lambda *args: None))
        api, _ = game_source('lobby/vehicle_carousel.py', {
            'driftkings.interface_catalog': module(gameface_spec=lambda name: {'resource': 'test'}),
            'driftkings.core.wnx': module(calculate=self.api.calculate, get_expected=lambda ident: self.expected),
            'driftkings.core.carousel_tiers': module(battle_tiers=lambda *args: (8, 10)),
            'driftkings.stats.vehinfo': module(getVehicleInfoData=lambda ident: {}, calculateRatingScale=lambda *args: 0),
            'gui.shared.personality': module(ServicesLocator=module(itemsCache=module(
                items=module(getVehicleDossier=lambda ident: dossier)))),
            'driftkings.settings.service': Settings({'colorRating': 3}).service(),
        }, real=('driftkings._constants', 'driftkings.common.utils.numbers',
                 'driftkings.common.utils.colorratting', 'driftkings.core.carousel'))
        vehicle = module(intCD=1, level=8, type='heavyTank', name='tank', shortUserName='Tank',
                         isPremium=False, nationName='germany', descriptor=module(maxHealth=1500))
        values = api['collect'](vehicle)
        self.assertEqual(values['wnx'], int(math.floor(self.api.calculate(1000, 1, 1, 350, self.expected) + .5)))
