# -*- coding: utf-8 -*-
import copy
import json
import os
import shutil
import tempfile

from support import ROOT, RuntimeTest


class VehicleMarkersTests(RuntimeTest):
    def test_each_color_rating_uses_shared_team_hp_and_damage_without_copying_them_to_json(self):
        prepare = self.load('core.vehicle_markers.config').prepare
        rating = self.load('common.utils.colorratting')
        for index in range(len(rating.color_tables)):
            raw = self.defaults()
            raw['colorRating'] = index
            data = prepare(raw)
            shared = rating.getRatingColors(index)
            self.assertEqual(data['colors']['team']['enemy'], shared['system']['enemy_alive'])
            self.assertEqual(data['colors']['hp'], shared['hp_ratio'])
            self.assertEqual(data['damageText']['colors']['player'], shared['damage']['player_enemy_hit'])
            self.assertNotIn('hp', raw['colors'])
            self.assertNotIn('colors', raw['damageText'])
            for hp in (0, 10, 10.4, 25, 25.4, 50, 50.4, 100):
                actual = next((band['color'] for band in data['colors']['hp'] if hp < band['value']),
                              data['colors']['hp'][-1]['color'])
                self.assertEqual(actual, rating.getColor(shared, 'hp_ratio', hp))

    def test_explicit_color_overrides_take_priority_without_mutating_shared_tables(self):
        prepare = self.load('core.vehicle_markers.config').prepare
        rating = self.load('common.utils.colorratting')
        before = copy.deepcopy(rating.color_tables)
        raw = self.defaults()
        raw['colors']['team'] = {'enemy': '#123456'}
        raw['damageText']['colors'] = {'player': '#654321'}
        data = prepare(raw)
        self.assertEqual(data['colors']['team']['enemy'], '#123456')
        self.assertEqual(data['damageText']['colors']['player'], '#654321')
        self.assertEqual(rating.color_tables, before)

    def test_split_store_preserves_personal_values_and_rejects_invalid_save(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        store = self.load('settings.vehicle_markers_store').VehicleMarkersStore(root)
        data = store.load()
        data['customFields']['enemy']['normal'][0]['x'] = 123
        store.save(data)
        self.assertEqual(store.load()['customFields']['enemy']['normal'][0]['x'], 123)
        broken = copy.deepcopy(data)
        broken['healthBar']['height'] = 0
        with self.assertRaises(ValueError):
            store.save(broken)
        self.assertEqual(store.load(), data)
        self.assertEqual(sorted(os.listdir(root)), sorted(store.filenames))

    def defaults(self):
        result = {}
        directory = os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'vehicle_markers')
        for name in ('general', 'markers', 'fields', 'colors', 'healthbar', 'damage', 'icons'):
            with open(os.path.join(directory, name + '.json'), 'rb') as stream:
                result.update(json.loads(stream.read().decode('utf-8')))
        return result

    def test_canonical_split_defaults_prepare_without_mutating_editable_documents(self):
        raw = self.defaults()
        before = copy.deepcopy(raw)
        prepared = self.load('core.vehicle_markers.config').prepare(raw)
        self.assertEqual(raw, before)
        self.assertEqual(prepared['customFields']['healthBar'], prepared['healthBar'])
        prepared['customFields']['colors']['team']['enemy'] = '#123456'
        self.assertEqual(raw, before)

    def test_enemy_bar_uses_team_macro_and_colorblind_override(self):
        data = self.load('core.vehicle_markers.config').prepare(self.defaults())
        self.assertEqual(data['healthBar']['color'], '{{c:team}}')
        self.assertNotEqual(data['colors']['team']['enemy'], data['colors']['team']['ally'])
        self.assertEqual(data['colors']['colorBlind']['team']['enemy'], '#C48CFF')

    def test_native_settings_are_copied_and_special_modes_keep_original_markers(self):
        policy = self.load('core.vehicle_markers.presentation')
        calls = []
        class Logger(object):
            def info(self, *args): pass
            def exception(self, *args): pass
        class Manager(object):
            def setMarkerSettings(self, settings):
                calls.append(settings)
                return settings
        original = Manager.__dict__['setMarkerSettings']
        native = {'enemy': {'markerBaseHp': 1, 'markerBaseHpIndicator': True}}
        snapshot = copy.deepcopy(native)
        data = self.load('core.vehicle_markers.config').prepare(self.defaults())
        controller = policy.Presentation(Logger(), data['markers'], data['customFields'], supported=lambda manager: False)
        controller.install(Manager)
        try:
            changed = Manager().setMarkerSettings(native)
            self.assertEqual(changed['enemy'], native['enemy'])
            self.assertIsNone(changed['__vmTest'])
            self.assertEqual(native, snapshot)
        finally:
            controller.close()
        self.assertIs(Manager.__dict__['setMarkerSettings'], original)

    def test_regular_modes_and_killcam_policy(self):
        supported = self.load('core.vehicle_markers.compatibility').supported
        self.assertTrue(supported('MarkersManager', 1))
        self.assertTrue(supported('MarkersManager', 2))
        self.assertFalse(supported('KillCamMarkersManager', 1))
        self.assertFalse(supported('MarkersManager', None))
        self.assertFalse(supported('MarkersManager', 32))

    def test_invalid_macros_and_hp_bands_fail_before_installing_hooks(self):
        prepare = self.load('core.vehicle_markers.config').prepare
        data = self.defaults()
        data['customFields']['enemy']['normal'][0]['format'] = '{{unsupported}}'
        with self.assertRaises(ValueError):
            prepare(data)
        data = self.defaults()
        data['colors']['hp'] = [{'value': 50, 'color': '#FFFFFF'}]
        with self.assertRaises(ValueError):
            prepare(data)

    def test_custom_bar_suppresses_native_bar_and_contour_without_touching_account(self):
        data = self.load('core.vehicle_markers.config').prepare(self.defaults())
        apply = self.load('core.vehicle_markers.presentation').apply
        native = dict((team, {'markerBaseHpIndicator': True, 'markerAltHpIndicator': True,
                             'markerBaseIcon': True, 'markerAltIcon': True})
                      for team in ('ally', 'enemy', 'dead'))
        changed = apply(native, data['markers'], data['customFields'])
        for team in native:
            self.assertFalse(changed[team]['markerBaseHpIndicator'])
            self.assertFalse(changed[team]['markerAltIcon'])
            self.assertTrue(native[team]['markerBaseHpIndicator'])
