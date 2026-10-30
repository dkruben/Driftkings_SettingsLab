import hashlib
from support import RuntimeTest, game_source, module


class CarouselPreviewTests(RuntimeTest):
    def test_absolute_damage_colours_evaluate_each_value_independently(self):
        api, _ = game_source('lobby/vehicle_carousel.py')
        api['layout'] = self.load('core.carousel')
        api['normalize_icon_paths'] = lambda value: value
        api['settings_service'] = module(getComponentDict=lambda config: {})
        calls = []
        def color(metric, value, palette):
            calls.append((metric, value))
            return '#123456' if value == 2380 else '#654321'
        api['getStatisticColor'] = color
        result = api['render_macro']('{{v.c_tdb}} / {{v.c_wn8expd}}', {'avgDamage': 2380, 'wn8expd': 1950})
        self.assertEqual(result, '#123456 / #654321')
        self.assertEqual(calls, [('tdb', 2380), ('tdb', 1950)])

    def test_zero_marks_icon_does_not_replace_earned_marks(self):
        api, _ = game_source('lobby/vehicle_carousel.py')
        api['layout'] = self.load('core.carousel')
        api['normalize_icon_paths'] = lambda value: value
        api['bounded'] = lambda value, low, high, default: default if value is None else value
        self.assertEqual(api['render_macro']('{{icon:marksOnGun}}', {'marksOnGun': 0}),
                         'coui://gui/maps/driftkings/carroucel/mark_0.png')
        for rank in (1, 2, 3):
            suffix = 'mark' if rank == 1 else 'marks'
            self.assertEqual(api['render_macro']('{{icon:marksOnGun}}', {'marksOnGun': rank, 'nation': 'usa'}),
                             'coui://gui/maps/icons/marksOnGun/95x85/usa_%d_%s.png' % (rank, suffix))

    def test_settings_preview_uses_the_draft_palette_only_for_the_carousel(self):
        requested = []
        api, _ = game_source('settings/panel/presenter.py', {
            'driftkings.lobby.vehicle_carousel': module(g_data=module(
                preview_cards=lambda palette: requested.append(palette) or {'source': 'examples'}))
        })
        values = {'legacy.CarouselStats': {
            'field_' + hashlib.sha1(b'colorRating').hexdigest()[:16]: 2}}
        self.assertIsNone(api['carousel_preview']('dk.settings', values))
        self.assertEqual(requested, [])
        self.assertEqual(api['carousel_preview']('legacy.CarouselStats', values), {'source': 'examples'})
        self.assertEqual(requested, [2])

    def test_two_fictional_cards_use_live_colour_rules_without_reading_inventory(self):
        api, _ = game_source('lobby/vehicle_carousel.py')
        calls = []
        api['collect'] = lambda vehicle: self.fail('Preview must not read a player dossier')
        api['getPlayer'] = lambda: self.fail('Preview must not access the account')
        api['getStatisticColor'] = lambda metric, value, palette: calls.append((metric, value, palette)) or '#123456'
        data = api['CarouselData']()
        result = data.preview_cards(2)
        self.assertEqual(result['source'], 'examples')
        self.assertEqual([card['name'] for card in result['vehicles']], ['T32', 'Obj. 140'])
        self.assertEqual(len(result['vehicles']), 2)
        self.assertEqual(result['vehicles'][0]['stats']['winRate'], 54.3)
        self.assertIn(('winrate', 54.3, 2), calls)
        self.assertTrue(all(card['colors']['winRate'] == '#123456' for card in result['vehicles']))
