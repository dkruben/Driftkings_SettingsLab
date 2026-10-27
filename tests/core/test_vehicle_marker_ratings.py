# -*- coding: utf-8 -*-
from support import RuntimeTest, module


class MarkerRatingsTests(RuntimeTest):
    def test_distance_refreshes_at_point_two_seconds_without_extra_stats_loads(self):
        api = self.load('flash.batalha.vehicle_markers.ratings')
        calls, delays, packets = [], [], []
        stats = module(enabled=lambda: True, loadStats=lambda: calls.append(True),
                       acquire=lambda owner: None, release=lambda owner: None,
                       getPlayersInfo=lambda ident: None)
        arena = module(vehicles={1: {'name': 'Player', 'accountDBID': 5}})
        class Manager(object):
            def _populate(self): pass
            def _dispose(self): pass
            def setMarkerSettings(self, value): pass
            def _isDAAPIInited(self): return True
            def as_setMarkerSettingsS(self, value): packets.append(value)
        bridge = api.Ratings(module(exception=lambda *args: None), stats,
                             {'customFields': {'format': '{{distance}}'}}, lambda: arena,
                             lambda delay, call: delays.append(delay) or len(delays), lambda ident: None,
                             lambda manager: True, lambda: 1,
                             lambda ident, vehicle, distance: {'distance': len(delays) if distance else None})
        manager = Manager()
        bridge.install(Manager)
        try:
            manager._populate()
            for tick in range(6):
                bridge.tick()
            self.assertEqual(len(calls), 2)
            self.assertEqual(delays[1:], [.2] * 6)
            self.assertEqual(len(packets), 6)
            self.assertEqual(packets[-1]['__vmRatings'][0]['values']['distance'], 6)
        finally:
            bridge.close()

    def test_macros_use_selected_rating_and_marker_palette(self):
        api = self.load('flash.batalha.vehicle_markers.ratings')
        colors = self.load('common.utils.colorratting')
        stats = {'battles': 1000, 'wn8': 2000, 'wnx': 1800, 'eff': 1400, 'xwn8': 75, 'xeff': 65}
        for scale in range(len(colors.color_tables)):
            for rating in ('wn8', 'wnx', 'eff'):
                result = api.values(stats, rating, scale)
                self.assertEqual(result['r'], stats[rating])
                self.assertEqual(result['c:xr'], colors.getStatisticColor(rating, stats[rating], scale))
                self.assertTrue(result['stat-available'])
                self.assertEqual(result['a:r'], 100)
        self.assertIsNone(api.values(stats, 'wnx')['xr'])

    def test_missing_anonymized_and_incomplete_stats_never_become_zero_ratings(self):
        api = self.load('flash.batalha.vehicle_markers.ratings')
        for stats, minimum, anonymous in ((None, 1, False), ({'battles': 9, 'wn8': 2000}, 10, False),
                                           ({'battles': 1000, 'wn8': 2000}, 1, True)):
            result = api.values(stats, 'wn8', 0, minimum, anonymous)
            self.assertIsNone(result['r'])
            self.assertFalse(result['stat-available'])
            self.assertEqual(result['a:r'], 0)
        self.assertEqual(api.values({'battles': 1000, 'wn8': 0})['r'], 0)
        self.assertIsNone(api.values({'battles': 1000, 'wn8': float('nan')})['r'])

    def test_bridge_reuses_shared_stats_sends_only_changes_and_releases_hooks(self):
        api = self.load('flash.batalha.vehicle_markers.ratings')
        stats = module(enabled=lambda: True, loadStats=lambda: None,
                       acquire=lambda owner: acquired.append(owner), release=lambda owner: released.append(owner),
                       getPlayersInfo=lambda ident: information.get(ident))
        acquired, released, callbacks, packets = [], [], [], []
        information = {5: {'battles': 1000, 'wn8': 2000}}
        arena = module(vehicles={1: {'name': 'Player', 'accountDBID': 5}})
        class Manager(object):
            ready = False
            def _populate(self): return 42
            def _dispose(self): pass
            def setMarkerSettings(self, value): pass
            def _isDAAPIInited(self): return self.ready
            def as_setMarkerSettingsS(self, value): packets.append(value)
        original = Manager.__dict__['_populate']
        bridge = api.Ratings(module(exception=lambda *args: None), stats, {}, lambda: arena,
                             lambda delay, call: callbacks.append(call) or len(callbacks),
                             lambda ident: None, lambda manager: True, lambda: 1)
        bridge.install(Manager)
        manager = Manager()
        self.assertEqual(manager._populate(), 42)
        bridge.tick()
        self.assertEqual(packets, [])
        manager.ready = True
        bridge.tick()
        self.assertEqual(packets[-1]['__vmRatings'][0]['values']['r'], 2000)
        bridge.tick()
        self.assertEqual(len(packets), 1)
        information[5]['wn8'] = 2500
        bridge.tick()
        self.assertEqual(len(packets), 2)
        manager.setMarkerSettings({})
        bridge.tick()
        self.assertEqual(len(packets), 3)
        manager._dispose()
        self.assertEqual(bridge.managers, {})
        bridge.close()
        self.assertEqual(acquired, released)
        self.assertIs(Manager.__dict__['_populate'], original)

    def test_account_wnx_requires_complete_assistance_and_expected_weights(self):
        api = self.load('core.wnx')
        api.set_reference({'data': {'1': {'damage': 100, 'frags': 1, 'spots': 1, 'assist': 50}}})
        stats = {'battles': 10, 'damage_dealt': 1000, 'frags': 10, 'spotted': 10,
                 'radio_assisted_damage': 200, 'track_assisted_damage': 200, 'stun_assisted_damage': 100}
        tanks = [{'tank_id': 1, 'statistics': stats}]
        self.assertEqual(api.account_from_tanks(tanks, 10), 1268)
        self.assertIsNone(api.account_from_tanks(tanks, 11))
        del stats['stun_assisted_damage']
        self.assertIsNone(api.account_from_tanks(tanks, 10))

    def test_rating_field_properties_and_opacity_are_validated(self):
        fields = self.load('core.vehicle_markers.fields')
        field = {'name': 'Rating', 'format': '{{r}}', 'alpha': '{{stat-available?100|0}}',
                 'textFormat': {'font': '$FieldFont', 'size': 17, 'color': '{{c:xr|#999999}}', 'bold': True}}
        normalized = fields.normalize({'enabled': True, 'ally': {'normal': [field]}})['ally']['normal'][0]
        self.assertTrue(normalized['textFormat']['bold'])
        self.assertEqual(normalized['alpha'], '{{stat-available?100|0}}')
        field['textFormat']['color'] = '{{c:unknown}}'
        with self.assertRaises(ValueError):
            fields.normalize({'enabled': True, 'ally': {'normal': [field]}})
