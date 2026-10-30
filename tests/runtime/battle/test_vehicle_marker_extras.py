# -*- coding: utf-8 -*-
import copy

from support import module, RuntimeTest


class MarkerExtrasTests(RuntimeTest):
    def test_references_expand_overrides_without_mutating_templates(self):
        api = self.load('core.vehicle_markers.references')
        data = {'def': {'style': {'x': 1, 'shadow': {'alpha': 50, 'blur': 2}}},
                'fields': [{'$ref': {'path': 'def.style'}, 'shadow': {'blur': 4}}, '${def.style}']}
        before = copy.deepcopy(data)
        result = api.resolve(data)
        self.assertEqual(result['fields'][0]['shadow'], {'alpha': 50, 'blur': 4})
        result['fields'][0]['x'] = 99
        self.assertEqual(result['fields'][1]['x'], 1)
        self.assertEqual(data, before)
        for document in ({'def': {'a': '${def.a}'}}, {'x': '${def.missing}'},
                         {'def': {'a': 2}, 'x': {'$ref': 'def.a', 'x': 3}}):
            with self.assertRaises(ValueError): api.resolve(document)
        self.assertEqual(api.defaults({'x': 4}, {'$ref': 'def.style'}), {'$ref': 'def.style'})

    def test_healthbar_gradient_fill_and_event_trail_validation(self):
        normalize = self.load('core.vehicle_markers.healthbar').normalize
        result = normalize({'fill': {'alpha': 45}, 'gradient': {'enabled': True, 'angle': 90},
                            'damage': {'color': '{{c:dmg}}'}})
        self.assertEqual(result['fill']['alpha'], 45)
        self.assertEqual(result['gradient']['color'], '{{c:hp}}')
        self.assertEqual(normalize({})['fill']['alpha'], 100)
        self.assertFalse(normalize({})['gradient']['enabled'])
        for options in ({'fill': {'alpha': 101}}, {'gradient': {'angle': 361}}, {'gradient': {'enabled': 1}}):
            with self.assertRaises(ValueError): normalize(options)

    def test_indicators_preserve_native_opacity_by_default(self):
        api = self.load('core.vehicle_markers.icons')
        result = api.normalize({'enabled': True, 'damageIndicator': {'enabled': False, 'x': 80}})
        for key in api.INDICATORS:
            self.assertEqual(result[key]['deadAlpha'], 100)
            self.assertIsNone(result[key]['y'])
        self.assertFalse(result['damageIndicator']['enabled'])
        self.assertEqual(result['damageIndicator']['x'], 80)

    def test_visible_stock_turret_classification_and_missing_data(self):
        classify = self.load('core.vehicle_markers.turrets').classify
        stock = module(compactDescr=1, maxHealth=100, guns=[module(name='a')])
        top = module(compactDescr=2, maxHealth=150, guns=[module(name='b')], unlocks=[1])
        descriptor = module(type=module(turrets=[[stock, top]]), turret=stock)
        self.assertEqual(classify(descriptor, lambda vehicle, gun: {'a': 1, 'b': 2}[gun.name])['turret-vulnerability'], 'high')
        self.assertEqual(classify(descriptor, lambda *args: None)['turret-vulnerability'], 'unknown')
        descriptor.turret = top
        self.assertFalse(classify(descriptor, lambda *args: None)['stock-turret'])
        self.assertIsNone(classify(None, lambda *args: None)['stock-turret'])
