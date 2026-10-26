# -*- coding: utf-8 -*-
import json
import sys

from support import RuntimeTest, module


class ColorTests(RuntimeTest):
    def setUp(self):
        super(ColorTests, self).setUp()
        self.colors = self.load('common.utils.colorratting')

    def test_custom_noobmeter_limits_are_preserved(self):
        limits = [300, 600, 900, 1200, 1500, 1750, 2300, 2900, 9999]
        for palette in (0,):
            data = self.colors.getRatingColors(palette)
            self.assertEqual([band['value'] for band in data['wn8']], limits)

    def test_wotlife_replaces_third_palette_with_published_bands_and_colours(self):
        self.assertEqual(self.colors.color_tables[2]['ScaleColor'], 'WoT-Life')
        data = self.colors.getRatingColors(2)
        self.assertEqual([band['value'] for band in data['wn8']],
                         [300, 600, 900, 1250, 1600, 1900, 2350, 2900, 99999])
        self.assertEqual([band['value'] for band in data['winrate']], [45, 47, 49, 52, 54, 56, 60, 65, 101])
        self.assertEqual([band['color'] for band in data['wn8']],
                         ['#000000', '#CD3333', '#D77900', '#D7B600', '#6D9521',
                          '#4C762E', '#4A92B7', '#83579D', '#5A3175'])

    def test_rating_snapshot_and_shared_damage_efficiency_limits(self):
        tables = self.load('common.utils.color_rating_data').color_tables
        self.assertEqual([table['ScaleColor'] for table in tables],
                         ['NoobMeter', 'Driftkings', 'WoT-Life', 'Tomato.gg'])
        data = self.colors.getRatingColors(1)
        for metric, limits in (('wn8', [637, 1143, 1774, 2760, 3819, 99999]),
                               ('eff', [616, 892, 1191, 1554, 1890, 99999]),
                               ('wtr', [3197, 4763, 6725, 9219, 10979, 99999])):
            self.assertEqual([band['value'] for band in data[metric]], limits)
        self.assertEqual(data['winrate'][-2]['value'], 63.49)
        for palette in range(3):
            self.assertEqual([band['value'] for band in self.colors.getRatingColors(palette)['wn8effd']],
                             [0.5, 0.7, 0.9, 1.2, 1.9, 15])

    def test_relative_damage_uses_expected_damage_and_handles_missing_data(self):
        api = self.colors
        for palette in range(3):
            for ratio in (0, 0.49, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0):
                expected = api.getStatisticColor('relativePerformance', ratio, palette)
                self.assertEqual(api.getRelativePerformanceColor(ratio * 1000, 1000, palette), expected)
                self.assertEqual(api.getRelativePerformanceColor(ratio * 2000, 2000, palette), expected)
            for damage, reference in ((1, 0), (1, -1), (1, None), (None, 1000), (1, float('nan')),
                                      (1, float('inf')), (float('inf'), 1000), ('bad', 1000)):
                self.assertEqual(api.getRelativePerformanceColor(damage, reference, palette),
                                 api.getRatingPaletteColor('nocolor', palette))

    def test_json_resource_preserves_palette_names_and_moe_thresholds(self):
        data = self.load('common.utils.color_rating_data')
        document = data.load_tables()
        self.assertEqual(document['color_tables'], self.colors.color_tables)
        for table in document['color_tables']:
            self.assertEqual([band['value'] for band in table['colors']['mog']], list(data.MOE_LEVELS))
            self.assertEqual(table['colors']['system'], document['system_colors'])

    def resource_payloads(self):
        data = self.load('common.utils.color_rating_data')
        paths = [data.RESOURCE] + [data.RESOURCE_ROOT + item['file']
            for item in json.loads(data.read_resource().decode('utf-8'))['palettes']]
        return dict((path, data.read_resource(path)) for path in paths)

    def test_loader_rejects_invalid_json_and_duplicate_palettes(self):
        data = self.load('common.utils.color_rating_data')
        with self.assertRaises(ValueError):
            data.load_tables(lambda path: b'{')
        resources = self.resource_payloads()
        document = json.loads(resources[data.RESOURCE].decode('utf-8'))
        document['palettes'].append(document['palettes'][0])
        resources[data.RESOURCE] = json.dumps(document).encode('utf-8')
        with self.assertRaises(ValueError):
            data.load_tables(resources.__getitem__)

    def test_reference_definitions_control_the_palette_and_reject_broken_links(self):
        data = self.load('common.utils.color_rating_data')
        resources = self.resource_payloads()
        path = data.RESOURCE_ROOT + 'noobmeter.json'
        document = json.loads(resources[path].decode('utf-8'))
        document['def']['colorRating']['very_bad'] = '#123456'
        resources[path] = json.dumps(document).encode('utf-8')
        colors = data.load_tables(resources.__getitem__)['color_tables'][0]['colors']
        self.assertEqual(colors['wn8'][0]['color'], '#123456')
        for reference in ('${def.missing}', '${def.colorRating.very_bad}', '${bad.path}'):
            document['def']['colorRating']['very_bad'] = reference
            resources[path] = json.dumps(document).encode('utf-8')
            with self.assertRaises(ValueError):
                data.load_tables(resources.__getitem__)

    def test_registry_accepts_an_additional_palette_without_changing_existing_indices(self):
        data = self.load('common.utils.color_rating_data')
        resources = self.resource_payloads()
        document = json.loads(resources[data.RESOURCE].decode('utf-8'))
        document['palettes'].append({'name': 'Additional', 'file': 'additional.json'})
        resources[data.RESOURCE] = json.dumps(document).encode('utf-8')
        resources[data.RESOURCE_ROOT + 'additional.json'] = resources[data.RESOURCE_ROOT + 'driftkings.json']
        loaded = data.load_tables(resources.__getitem__)['color_tables']
        self.assertEqual(loaded[:-1], data.color_tables)
        self.assertEqual(loaded[-1]['ScaleColor'], 'Additional')

    def test_game_reads_the_bundled_resource_through_resmgr(self):
        data = self.load('common.utils.color_rating_data')
        resources = self.resource_payloads()
        previous = sys.modules.get('ResMgr')
        paths = []
        def open_section(path):
            paths.append(path)
            return module(asBinary=resources[path])
        sys.modules['ResMgr'] = module(openSection=open_section, isFile=lambda path: path in resources)
        try:
            self.assertEqual(data.load_tables()['color_tables'], data.color_tables)
            self.assertEqual(paths, [data.RESOURCE] + [data.RESOURCE_ROOT + filename
                for filename in ('noobmeter.json', 'driftkings.json', 'wotlife.json', 'tomato.json')])
        finally:
            if previous is None:
                del sys.modules['ResMgr']
            else:
                sys.modules['ResMgr'] = previous

    def test_extracted_tables_preserve_legacy_exports_and_shared_identity(self):
        data = self.load('common.utils.color_rating_data')
        self.assertEqual(self.colors.__all__, ('color_tables', 'getRatingColors', 'getColor', 'getStatisticColor',
                                               'getRatingPaletteColor', 'getComparisonColor', 'getMoeDamageColor',
                                               'getRelativePerformanceColor'))
        for name in ('MOE_LEVELS', 'color_tables'):
            self.assertIs(getattr(self.colors, name), getattr(data, name))

    def test_all_numeric_scales_at_below_and_above_every_boundary(self):
        api = self.colors
        checked = 0
        for table in api.color_tables:
            for metric, bands in table['colors'].items():
                if not isinstance(bands, (list, tuple)) or metric in ('diff', 'mog'):
                    continue
                if metric in table['colors'].get('gradient', {}).get('metrics', ()):
                    continue  # Tomato uses continuous interpolation; tested separately.
                for index, band in enumerate(bands):
                    limit = band['value']
                    # Source scales use exclusive upper bounds, not <=.
                    lower = band['color']
                    upper = bands[min(index + 1, len(bands) - 1)]['color']
                    self.assertEqual(api.getColor(table['colors'], metric, limit - 0.00001), lower)
                    self.assertEqual(api.getColor(table['colors'], metric, limit), upper)
                    self.assertEqual(api.getColor(table['colors'], metric, limit + 0.00001), upper)
                    checked += 1
                self.assertEqual(api.getColor(table['colors'], metric, -1e40), bands[0]['color'])
                self.assertEqual(api.getColor(table['colors'], metric, 1e40), bands[-1]['color'])
        self.assertGreater(checked, 100)

    def test_moe_inclusive_lower_bounds_and_outside_range(self):
        api = self.colors
        for index in range(len(api.color_tables)):
            bands = api.getRatingColors(index)['mog']
            for position, band in enumerate(bands):
                self.assertEqual(api.getStatisticColor('mog', band['value'], index), band['color'])
                self.assertEqual(api.getStatisticColor('mog', band['value'] - 0.001, index),
                                 bands[max(0, position - 1)]['color'])
            self.assertEqual(api.getStatisticColor('mog', -10, index), bands[0]['color'])
            self.assertEqual(api.getStatisticColor('mog', 101, index), bands[-1]['color'])

    def test_invalid_palette_and_metric_fallbacks(self):
        api = self.colors
        first = api.getRatingColors(0)
        for value in (-1, len(api.color_tables), 100, None, 'unknown', float('nan'), float('inf')):
            self.assertIs(api.getRatingColors(value), first)
        self.assertIs(api.getRatingColors('1'), api.getRatingColors(1))
        for index in range(3):
            data = api.getRatingColors(index)
            self.assertIsNone(api.getColor(data, 'missing', 100))
            for value in (None, 'invalid', float('nan'), float('inf'), -float('inf')):
                self.assertIsNone(api.getColor(data, 'wn8', value))
                self.assertEqual(api.getStatisticColor('wn8', value, index), api.getRatingPaletteColor('nocolor', index))
            self.assertEqual(api.getStatisticColor('missing', 100, index), api.getRatingPaletteColor('nocolor', index))

    def test_aliases_and_battle_units(self):
        api = self.colors
        for index in range(3):
            data = api.getRatingColors(index)
            for alias, metric in (('xwn8', 'x'), ('xeff', 'x'), ('marks', 'mog'), ('winRate', 'winrate'),
                                  ('avgDamage', 'tdb'), ('hitRate', 'hitsRatio')):
                for value in (0, 50, 100, 1000):
                    self.assertEqual(api.getColor(data, alias, value), api.getColor(data, metric, value))
            self.assertEqual(api.getColor(data, 'battles', 10000), api.getColor(data, 'kb', 10))
            self.assertEqual(api.getColor(data, 'unused', kwargs=50), api.getColor(data, 'x', 50))

    def test_comparisons_negative_zero_positive_and_invalid(self):
        api = self.colors
        for index in range(3):
            palette = api.getRatingColors(index)['colorRating']
            for value, name in ((9, 'very_bad'), (10, 'normal'), (11, 'good')):
                self.assertEqual(api.getComparisonColor(value, 10, index), palette[name])
            for value in (None, 'bad', float('nan'), float('inf')):
                self.assertEqual(api.getComparisonColor(value, 10, index), api.getRatingPaletteColor('nocolor', index))

    def test_moe_damage_target_boundaries(self):
        api = self.colors
        targets = (100, 200, 300, 400, 500, 600, 700)
        for index in range(3):
            for position, target in enumerate(targets):
                for value in (target - 0.01, target):
                    self.assertEqual(api.getMoeDamageColor(value, targets, index),
                                     api.getStatisticColor('mog', api.MOE_LEVELS[position + 1], index))
                self.assertEqual(api.getMoeDamageColor(target + 0.01, targets, index),
                                 api.getStatisticColor('mog', api.MOE_LEVELS[min(position + 2, 7)], index))
            for value in (None, 'bad', float('nan'), float('inf')):
                self.assertEqual(api.getMoeDamageColor(value, targets, index), api.getRatingPaletteColor('nocolor', index))
            self.assertEqual(api.getMoeDamageColor(1, (), index), api.getRatingPaletteColor('nocolor', index))
