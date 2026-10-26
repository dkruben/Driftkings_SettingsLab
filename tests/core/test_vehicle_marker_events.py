# -*- coding: utf-8 -*-
import copy
import json
import os

from support import ROOT, RuntimeTest, module


class MarkerEventsTests(RuntimeTest):
    def test_author_styles_inherit_without_changing_each_other(self):
        normalize = self.load('core.vehicle_markers.damage').normalize
        options = {'enabled': True, 'x': 0, 'sources': {'player': {'x': -80, 'duration': 1},
                   'squad': {'format': '{{dmg-source}} {{dmg}}', 'rise': 100}, 'other': {'enabled': False}}}
        before = copy.deepcopy(options)
        result = normalize(options)
        self.assertEqual(result['sources']['player']['x'], -80)
        self.assertEqual(result['sources']['squad']['x'], 0)
        self.assertEqual(result['sources']['player']['duration'], 1)
        self.assertEqual(result['sources']['squad']['duration'], 2)
        self.assertEqual(result['sources']['squad']['rise'], 100)
        self.assertFalse(result['sources']['other']['enabled'])
        self.assertIn('{{i18n:blownUp}}', result['sources']['player']['blowupMessage'])
        self.assertEqual(options, before)
        # Legacy input accepts {{l10n:blownUp}}; copied configurations keep working.
        schema = normalize({'sources': {'player': {'blowupMessage': '{{l10n:blownUp}} {{dmg}}'}}})
        self.assertEqual(schema['sources']['player']['blowupMessage'], '{{l10n:blownUp}} {{dmg}}')
        with self.assertRaises(ValueError):
            normalize({'sources': {'player': {'blowupMessage': '{{unknown}}'}}})
        with self.assertRaises(ValueError):
            normalize({'sources': {'player': {'duration': 11}}})

    def test_conditions_and_validation_use_bounded_grammar(self):
        fields = self.load('core.vehicle_markers.fields')
        api = self.load('core.vehicle_markers.expressions')
        with open(os.path.join(ROOT, 'tests', 'fixtures', 'vehicle_marker_conditions.json'), 'rb') as stream:
            fixture = json.loads(stream.read().decode('utf-8'))
        for expression, expected in fixture['cases']:
            fields.template('{{' + expression + '?100|0}}')
            self.assertEqual(api.condition(expression, fields.MACROS, fixture['values']), expected, expression)
        for condition in ('distance<=500', 'distance!=0'):
            self.assertFalse(api.condition(condition, fields.MACROS, {'distance': None}))
        for value in ('{{unknown?{{hp}}|0}}', '{{hp.__class__}}', '{{hp/2<500?1|0}}', '{{hp', '{{hp%x}}'):
            with self.assertRaises(ValueError):
                fields.template(value)
        field = {'alpha': '{{enemy&&hp-ratio<25?100|0}}'}
        fields.normalize({'enabled': True, 'enemy': {'normal': [field]}})

    def test_distance_uses_only_current_entities_and_observer_origin(self):
        api = self.load('core.vehicle_markers.context')
        class Vector(object):
            def __init__(self, x): self.x = x
            def __sub__(self, other): return module(length=abs(self.x - other.x))
        attached = module(isAlive=lambda: True)
        player = module(team=1, playerVehicleID=1, position=Vector(0), getOwnVehiclePosition=lambda: Vector(100),
                        getVehicleAttached=lambda: attached,
                        arena=module(vehicles={1: {'prebattleID': 7}}))
        target = {'team': 1, 'prebattleID': 7}
        lookup = lambda ident: module(position=Vector(450)) if ident == 2 else None
        data = api.context(player, lookup, 2, target, True)
        self.assertEqual(data['distance'], 350)
        self.assertTrue(data['squad'])
        attached.isAlive = lambda: False
        self.assertEqual(api.context(player, lookup, 2, target, True)['distance'], 450)
        self.assertIsNone(api.context(player, lookup, 3, target, True)['distance'])
        self.assertIsNone(api.context(player, lookup, 2, target, False)['distance'])
        self.assertFalse(api.context(player, lookup, 2, {'team': 2, 'prebattleID': 7})['squad'])

    def test_position_and_battle_type_follow_marker_policy(self):
        api = self.load('core.vehicle_markers.context')
        vehicles = {5: {'team': 1}, 2: {'team': 1}, 9: {'team': 2}, 4: {'team': 2}}
        arena = module(vehicles=vehicles, bonusType=1)
        player = module(team=1, playerVehicleID=2, arena=arena, getVehicleAttached=lambda: None)
        data = dict((ident, api.context(player, lambda ident: None, ident, vehicle)) for ident, vehicle in vehicles.items())
        # Without the client's roster the team order falls back to vehicle ids, numbered per team.
        self.assertEqual([data[ident]['position'] for ident in (2, 5, 4, 9)], [1, 2, 1, 2])
        self.assertEqual(data[2]['battletype'], '')
        vehicles[1] = {'team': 1}
        self.assertEqual(api.context(player, lambda ident: None, 5, vehicles[5])['position'], 2)
        arena.bonusType = 2
        self.assertNotEqual(api.context(player, lambda ident: None, 5, vehicles[5])['battletype'], '')

