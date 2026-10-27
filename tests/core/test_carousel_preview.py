import hashlib
from support import RuntimeTest, game_source, module


class CarouselPreviewTests(RuntimeTest):
    def test_settings_preview_uses_the_draft_palette_only_for_the_carousel(self):
        requested = []
        api, _ = game_source('settings/panel/presenter.py', {
            'driftkings.lobby.vehicle_carousel': module(g_data=module(
                preview_cards=lambda palette: requested.append(palette) or {'source': 'inventory'}))
        })
        values = {'legacy.CarouselStats': {
            'field_' + hashlib.sha1(b'colorRating').hexdigest()[:16]: 2}}
        self.assertIsNone(api['carousel_preview']('dk.settings', values))
        self.assertEqual(requested, [])
        self.assertEqual(api['carousel_preview']('legacy.CarouselStats', values), {'source': 'inventory'})
        self.assertEqual(requested, [2])

    def test_inventory_snapshot_is_bounded_selected_first_and_account_scoped(self):
        inventory = dict((cd, module(shortUserName='Tank %s' % cd, nationName='usa',
            name='usa:A%s_Test' % cd, icon='img://gui/maps/icons/vehicle/test.png', level=8,
            type='heavyTank', isPremium=False, isFavorite=cd == 3, isInBattle=False,
            dailyXPFactor=2)) for cd in range(1, 7))
        account = module(databaseID=7)
        api, _ = game_source('lobby/vehicle_carousel.py', {
            'CurrentVehicle': module(g_currentVehicle=module(isPresent=lambda: True, intCD=3)),
            'gui.shared.personality': module(ServicesLocator=module(itemsCache=module(
                items=module(getVehicles=lambda criteria: inventory))))
        })
        reads, palettes = [], []
        api['getPlayer'] = lambda: account
        api['collect'] = lambda vehicle: reads.append(vehicle.name) or {'battles': 42, 'winRate': 55.5}
        api['getStatisticColor'] = lambda metric, value, palette: palettes.append(palette) or '#123456'
        data = api['CarouselData']()
        result = data.preview_cards(2)
        self.assertEqual(result['source'], 'inventory')
        self.assertEqual([card['id'] for card in result['vehicles']], [3, 1, 2, 4])
        self.assertTrue(result['vehicles'][0]['selected'])
        self.assertTrue(result['vehicles'][0]['favorite'])
        self.assertEqual(result['vehicles'][0]['stats']['winRate'], 55.5)
        self.assertEqual(set(palettes), set([2]))
        data.preview_cards(1)
        self.assertEqual(len(reads), 4, 'slider edits reuse dossier statistics')
        account.databaseID = 8
        data.preview_cards()
        self.assertEqual(len(reads), 8, 'switching accounts cannot reuse another account dossier')

