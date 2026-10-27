import json
from support import RuntimeTest, Settings, game_source, module


class AccountWN8Tests(RuntimeTest):
    def test_client_legacy_modes_are_removed_from_totals_and_vehicle_weights(self):
        api = self.load('core.profile_ratings')
        def stats(battles, wins, damage, frags, spots, defense, vehicles=None):
            return module(getBattlesCount=lambda: battles, getWinsCount=lambda: wins,
                          getDamageDealt=lambda: damage, getFragsCount=lambda: frags,
                          getSpottedEnemiesCount=lambda: spots, getCapturePoints=lambda: 0,
                          getDroppedCapturePoints=lambda: defense, getVehicles=lambda: vehicles)
        empty = stats(0, 0, 0, 0, 0, 0)
        historical = stats(10, 5, 500, 5, 5, 5)
        vehicle = module(getRandomStats=lambda: stats(110, 55, 100500, 105, 105, 105),
                         getClanStats=lambda: historical, getCompanyStats=lambda: empty)
        account = module(getRandomStats=lambda: stats(110, 55, 100500, 105, 105, 105, {1: (110, 55, 0)}),
                         getClanStats=lambda: historical, getCompanyStats=lambda: empty)
        clean = api.pure_random_stats(account, vehicle_dossier=lambda ident: vehicle)
        self.assertEqual(clean.getBattlesCount(), 100)
        self.assertEqual(clean.getVehicles(), {1: (100, 50, 0)})
        # Marker ratings read the client field names, as on VehiclesDossiersCut.
        self.assertEqual((clean.getVehicles()[1].battlesCount, clean.getVehicles()[1].wins), (100, 50))
        self.assertEqual(clean.getAvgDamage(), 1000)
        expected = lambda ident: dict(wn8expDamage=1000, wn8expFrag=1, wn8expSpot=1, wn8expDef=1, wn8expWinRate=50)
        self.assertEqual(api.account_wn8(clean, expected), 1565)
        self.assertIsNone(api.pure_random_stats(account, vehicle_dossier=lambda ident: None))
        self.assertIsNone(api.vehicle_wn8(None, 1, expected))

    def setUp(self):
        super(AccountWN8Tests, self).setUp()
        self.calculate = self.load('core.profile_ratings').account_wn8
        self.stats = module(getBattlesCount=lambda: 100, getVehicles=lambda: {1: (25, 12, 100), 2: (75, 37, 300)},
                            getAvgDamage=lambda: 1750, getAvgFrags=lambda: 1.75, getAvgEnemiesSpotted=lambda: 1.75,
                            getDroppedCapturePoints=lambda: 175, getWinsEfficiency=lambda: .5)
        self.expected = lambda key: dict(wn8expDamage=1000*key, wn8expFrag=key, wn8expSpot=key,
                                         wn8expDef=key, wn8expWinRate=50)

    def test_weights_expected_values_by_each_vehicles_battles(self):
        self.assertEqual(self.calculate(self.stats, self.expected), 1565)

    def test_vehicle_wn8_does_not_use_account_vehicle_list(self):
        del self.stats.getVehicles
        expected = lambda key: dict(wn8expDamage=1750, wn8expFrag=1.75, wn8expSpot=1.75,
                                     wn8expDef=1.75, wn8expWinRate=50)
        calculate = self.load('core.profile_ratings').vehicle_wn8
        self.assertEqual(calculate(self.stats, 99, expected), 1565)
        self.assertIsNone(calculate(self.stats, 99, lambda key: None))

    def test_incomplete_data_does_not_invent_a_rating(self):
        self.assertIsNone(self.calculate(self.stats, lambda key: None))
        self.stats.getVehicles = lambda: {1: (25, 12, 100)}
        self.assertIsNone(self.calculate(self.stats, self.expected))
        self.stats.getBattlesCount = lambda: 0
        self.assertIsNone(self.calculate(self.stats, self.expected))


class NativeProfileTests(RuntimeTest):
    def test_native_header_fields_vehicle_sorting_and_switches(self):
        settings = {'enabled': True, 'vehicleColors': True, 'statisticsColors': True, 'showPlayerWN8': True, 'showVehicleWN8': True}
        names = ['_BattlesCountField', '_DamageCoefficientField', '_HitsField', '_AvgDmgField',
                 '_WinsEfficiencyField', '_AvgEnemiesSpottedField', '_AvgDestroyedField', '_SurvivalField', '_AvgReceivedDmgField']
        fields = module(**dict((name, type(name, (object,), {})) for name in names))
        fields.DetailedStatisticsUtils = type('DetailedStatisticsUtils', (object,), {})
        fields.ProfileUtils = module(packLditItemData=lambda text, desc, tip, icon: dict(text=text, description=desc, iconPath=icon))
        api, hooks = game_source('flash/lobby/profile_statistics.py', {
            'driftkings.settings.service': Settings(settings).service(),
            'gui.Scaleform.genConsts.PROFILE_DROPDOWN_KEYS': module(PROFILE_DROPDOWN_KEYS=module(ALL='all', FALLOUT='fallout')),
            'gui.Scaleform.daapi.view.lobby.profile': module(ProfileUtils=fields),
            'gui.Scaleform.daapi.view.lobby.profile.profile_statistics_vos': module(ProfileAllStatisticsVO=type('ProfileAllStatisticsVO', (object,), {})),
            'gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique': module(ProfileTechnique=type('ProfileTechnique', (object,), {})),
            'gui.Scaleform.daapi.view.lobby.profile.ProfileStatistics': module(ProfileStatistics=type('ProfileStatistics', (object,), {})),
        }, real=('driftkings.common.utils.colorratting', 'driftkings.core.profile_ratings'))
        api['vehicle_wn8'] = lambda *args: 2300
        api['account_wn8'] = lambda *args: 2200
        api['install']()
        native = [{'text': str(i)} for i in range(6)]
        stats = module(getBattlesCount=lambda: 19, getWinsEfficiency=lambda: .7895, getAvgDamage=lambda: 1357)
        data = [stats, module(getRandomStats=lambda: stats)]
        header = hooks.get('ProfileAllStatisticsVO', '_getHeaderData')
        result = header(lambda *args: native, None, data)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[-1]['description'], 'WN8')
        self.assertIn('2200', result[-1]['text'])
        self.assertEqual(native, [{'text': str(i)} for i in range(6)])
        rows = [{'id': 1, 'shortUserName': 'Tank', 'winsEfficiency': 78.95, 'battlesCount': 19, 'avgExperience': 1022}]
        vehicles = hooks.get('ProfileTechnique', '_getTechniqueListVehicles')
        technique = module(_battlesType='all', _userID=None, itemsCache=module(items=module(
            getVehicleDossier=lambda *args: module(getRandomStats=lambda: stats))))
        # Native rows stay unchanged; the list renderer paints the stored colors.
        self.assertIs(vehicles(lambda *args: rows, technique, None), rows)
        self.assertEqual(rows[0]['shortUserName'], 'Tank')
        self.assertEqual(set(technique._dkVehicleColors[1]), set(('battlesTF', 'winsTF', 'vehicleTF')))
        settings['vehicleColors'] = False
        settings['statisticsColors'] = False
        self.assertEqual(vehicles(lambda *args: rows, technique, None), rows)
        self.assertEqual(technique._dkVehicleColors, {})
        settings['showVehicleWN8'] = False
        settings['showPlayerWN8'] = False
        self.assertEqual(header(lambda *args: native, None, data), tuple(native))
        settings['vehicleColors'] = True
        settings['statisticsColors'] = True
        field = hooks.get('_WinsEfficiencyField', '_buildData')
        self.assertIn('<font', field(lambda *args: '78.95%', None, stats, True))

        settings['showVehicleWN8'] = True
        settings['showPlayerWN8'] = True
        native_details = [{'label': 'General', 'data': [{'label': 'Battles', 'data': '19'}]}]
        receive = hooks.get('ProfileTechnique', '_receiveVehicleDossier')
        detailed = hooks.get('DetailedStatisticsUtils', 'getStatistics')
        received = hooks.get('_AvgReceivedDmgField', '_buildData')
        view = module(_battlesType='all', _dkVehicleColors={}, itemsCache=module(items=module(
            getItemByCD=lambda key: module(descriptor=module(maxHealth=1000)),
            getVehicleDossier=lambda *args: module(getRandomStats=lambda: stats))))
        stats.getAvgDamageReceived = lambda: 455
        def native_render(*args):
            return (detailed(lambda *args: native_details, stats, True, None),
                    received(lambda *args: '455', None, stats, True))
        rendered, received_text = receive(native_render, view, 1, None)
        self.assertEqual(rendered[0]['data'][-1]['label'], 'WN8')
        self.assertIn('2300', rendered[0]['data'][-1]['data'])
        self.assertIn('<font', received_text)
        self.assertIn('vehicleTF', view._dkVehicleColors[1])
        self.assertEqual(len(native_details[0]['data']), 1)
        self.assertEqual(received(lambda *args: '455', None, stats, True), '455')
        view._battlesType = 'epic'
        self.assertEqual(receive(native_render, view, 1, None)[0], native_details)
        view._battlesType = 'all'
        settings['showVehicleWN8'] = False
        settings['showPlayerWN8'] = False
        self.assertEqual(receive(native_render, view, 1, None)[0], native_details)
