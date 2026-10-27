import hashlib
from support import RuntimeTest, game_source, module


class CarouselPreviewTests(RuntimeTest):
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
