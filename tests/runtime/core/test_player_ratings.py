# -*- coding: utf-8 -*-
try:
    import Queue as queue
except ImportError:
    import queue

from support import RuntimeTest, module, source


class PlayerRatingsTests(RuntimeTest):
    def test_marker_consumer_uses_stats_even_with_roster_hidden_but_respects_stats_switch(self):
        self.api['GLOBAL'] = module(ENABLED='enabled')
        self.api['TEAM_PANELS'] = module(STATS_ENABLED='statsEnabled')
        settings = {'enabled': False, 'statsEnabled': True}
        self.api['settings_service'] = module(getComponentDict=lambda config: settings)
        stats = self.api['Statistics']()
        self.assertFalse(stats.enabled())
        stats._consumers.add(object())
        self.assertTrue(stats.enabled())
        settings['statsEnabled'] = False
        self.assertFalse(stats.enabled())

    def setUp(self):
        super(PlayerRatingsTests, self).setUp()
        colors = self.load('common.utils.colorratting')
        self.api = source('core/player_ratings.py', {
            'urllib2': module(), 'Queue': queue,
            'gui.battle_control.arena_info.interfaces': module(IArenaVehiclesController=object),
            'gui.battle_control.arena_info.settings': module(ARENA_LISTENER_SCOPE=module(VEHICLES=2)),
            'gui.battle_control.battle_constants': module(BATTLE_CTRL_ID=module(MOD=19)),
            'gui.shared.gui_items.Vehicle': module(getVehicleClassTag=lambda value: None),
            'gui.shared.personality': module(ServicesLocator=object()),
            'helpers': module(dependency=module(descriptor=lambda value: None)),
            'messenger': module(g_settings=object()),
            'skeletons.gui.battle_session': module(IBattleSessionProvider=object),
            'driftkings._constants': self.load('_constants'),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: None, logWarning=lambda *args: None,
                                       getStatisticColor=colors.getStatisticColor,
                                       callback=lambda *args: None, cancelCallback=lambda *args: None),
            'driftkings.common.utils.colorratting': module(getPlayer=lambda: None, logWarning=lambda *args: None,
                                       getStatisticColor=colors.getStatisticColor,
                                       callback=lambda *args: None, cancelCallback=lambda *args: None),
            'driftkings.core.callbacks': module(getPlayer=lambda: None, logWarning=lambda *args: None,
                                       getStatisticColor=colors.getStatisticColor,
                                       callback=lambda *args: None, cancelCallback=lambda *args: None),
            'driftkings.core.hooks': module(override=lambda *args: None),
            'driftkings.settings.service': module(settings_service=object()),
            'driftkings.stats.vehinfo': module(calculateRatingScale=lambda metric, value: value,
                                      getVehicleInfoData=lambda value: None, scaleValuesInstance=object())})

    def test_unavailable_ratings_have_missing_marker_and_neutral_color(self):
        result = self.api['format_rating']('{{wn8}} {{c:wn8}} {{r}}', {}, {}, False)
        self.assertEqual(result, u'\u2014 #AAAAAA \u2014')

    def test_available_ratings_use_the_configured_palette(self):
        colors = self.load('common.utils.colorratting')
        for index in range(3):
            result = self.api['format_rating']('{{wn8}} {{c:wn8}}', {'wn8': 2000}, {}, True, index)
            self.assertEqual(result, '2000 ' + colors.getStatisticColor('wn8', 2000, index))

    def test_battles_below_a_thousand_are_shown_instead_of_0k(self):
        template = '{{kb%2d~k|--k}}'
        for battles, expected in ((99, '99'), (850, '850'), (999, '999'), (1000, ' 1k'), (23400, '23k')):
            self.assertEqual(self.api['format_rating'](template, {'battles': battles}, {}, True), expected)
        self.assertEqual(self.api['format_rating'](template, {}, {}, False), '--k')

    def test_names_are_escaped_and_macros_do_not_traverse_objects(self):
        result = self.api['format_rating']('{{name}} {{clan}}', {}, {'name': '<Admin>', 'clanAbbrev': 'A&B'}, True)
        self.assertEqual(result, '&lt;Admin&gt; [A&amp;B]')
        formatter = self.api['RatingFormatter']()
        self.assertEqual(formatter.vformat('{name.__class__}', (), {'name': 'unsafe'}), u'\u2014')

    def test_damage_ratio_missing_denominators_and_valid_value(self):
        ratio = self.api['tank_damage_ratio']
        for battles, hp, damage in ((0, 100, 100), (-1, 100, 100), (2, 0, 100), (2, -1, 100), (2, 100, None)):
            self.assertEqual(ratio({'battles': battles, 'damage_dealt': damage}, hp), u'\u2014')
        self.assertEqual(ratio({'battles': 4, 'damage_dealt': 6000}, 1000), 1.5)

    def test_expected_values_recover_when_download_arrives(self):
        api = self.api
        calculator = api['CalculatorRating']
        vehicle = {'level': 8, 'vClass': 'heavyTank'}
        scales = module(wn8_revision=0, getVehicleInfoDataArray=lambda: [vehicle])
        api['scaleValuesInstance'] = scales
        api['getVehicleInfoData'] = lambda ident: vehicle
        self.assertIsNone(calculator.getExpectedWn8(1))
        vehicle.update(wn8expDamage=1000, wn8expFrag=1, wn8expSpot=1, wn8expDef=1, wn8expWinRate=50)
        scales.wn8_revision += 1
        self.assertEqual(calculator.getExpectedWn8(1)['expDamage'], 1000)
        vehicle['wn8expDamage'] = 1200
        scales.wn8_revision += 1
        self.assertEqual(calculator.getExpectedWn8(1)['expDamage'], 1200)

    def test_fallback_counts_only_valid_samples_and_refreshes(self):
        api = self.api
        vehicle = {'level': 8, 'vClass': 'heavyTank'}
        sample = dict(vehicle, wn8expDamage=1000, wn8expFrag=1, wn8expSpot=1, wn8expDef=1, wn8expWinRate=50)
        scales = module(wn8_revision=0, getVehicleInfoDataArray=lambda: [vehicle, sample])
        api['scaleValuesInstance'] = scales
        api['getVehicleInfoData'] = lambda ident: vehicle
        calculator = api['CalculatorRating']
        self.assertEqual(calculator.getExpectedWn8(1)['expDamage'], 1000)
        sample['wn8expDamage'] = 1200
        scales.wn8_revision += 1
        self.assertEqual(calculator.getExpectedWn8(1)['expDamage'], 1200)
        sample['vClass'] = 'mediumTank'
        scales.wn8_revision += 1
        self.assertEqual(calculator.getExpectedWn8(1)['expDamage'], 1200)

    def test_statistics_download_is_bounded_and_closes_response(self):
        api = self.api
        closed, pending = [], [b'1234', b'5678']
        api['urllib2'] = module(urlopen=lambda *args, **kwargs: module(
            read=lambda amount: pending.pop(0) if pending else b'', close=lambda: closed.append(True)))
        api['MAX_STATS_RESPONSE'] = 5
        self.assertRaises(IOError, api['Events'].read_response, 'test', 1)
        self.assertEqual(closed, [True])
        api['MAX_STATS_RESPONSE'] = 100
        pending[:] = [b'{}']
        self.assertEqual(api['Events'].read_response('test', 1), b'{}')
        self.assertEqual(closed, [True, True])

    def test_api_statistics_pair_random_account_and_vehicle_counts(self):
        api = self.api
        requests = []
        def request(region, endpoint, **kwargs):
            requests.append((endpoint, kwargs))
            if endpoint == 'wot/account/info':
                return {'511': {'statistics': {'random': {'battles': 10}, 'all': {'battles': 90}}}}
            return {'511': [{'tank_id': 1, 'mark_of_mastery': 3,
                             'random': {'battles': 10, 'wins': 6, 'damage_dealt': 10000},
                             'all': {'battles': 90, 'wins': 80, 'damage_dealt': 900000}}]}
        api['g_event'] = module(userRegion=lambda account: 'eu', request=request)
        stats = api['Statistics']()
        info, tanks = stats.fetchPlayerStats(['511'])
        self.assertEqual(info['511']['statistics']['random']['battles'], 10)
        self.assertEqual(tanks['511'][0]['statistics']['battles'], 10)
        self.assertEqual(tanks['511'][0]['damageStats']['damage_dealt'], 10000)
        self.assertEqual(tanks['511'][0]['mark_of_mastery'], 3)
        self.assertEqual(requests[0][1]['extra'], 'statistics.random')
        self.assertEqual(requests[1][0], 'wot/tanks/stats')
        self.assertEqual(requests[1][1]['extra'], 'random')
        self.assertEqual(requests[1][1]['account_id'], '511')
        self.assertNotIn('statistics.all', requests[0][1]['fields'])

    def test_api_vehicle_failure_is_not_cached_as_empty_statistics(self):
        api = self.api
        api['g_event'] = module(userRegion=lambda account: 'eu', request=lambda *args, **kwargs: None)
        info, tanks = api['Statistics']().fetchPlayerStats(['511'])
        self.assertEqual(info, {})
        self.assertEqual(tanks, {})

    def test_statistics_download_checks_deadline_after_read_and_closes(self):
        api = self.api
        closed, clock = [], iter([0, 0, 31])
        api['time'] = module(time=lambda: next(clock))
        api['urllib2'] = module(urlopen=lambda *args, **kwargs: module(
            read=lambda amount: b'{}', close=lambda: closed.append(True)))
        self.assertRaises(IOError, api['Events'].read_response, 'test', 1)
        self.assertEqual(closed, [True])
