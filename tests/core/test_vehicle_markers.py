# -*- coding: utf-8 -*-
import copy
import json
import os
import shutil
import tempfile

from support import ROOT, RuntimeTest


class VehicleMarkersTests(RuntimeTest):
    def legacy(self):
        data = self.defaults()
        data.pop('schemaVersion')
        for key in ('markers', 'customFields'):
            source = data[key]
            data[key] = {'enabled': source['enabled'], 'ally': source['ally']['alive'],
                         'enemy': source['enemy']['alive'], 'dead': source['enemy']['dead']}
        for key in ('healthBar', 'damageText', 'icons'):
            for team in ('ally', 'enemy'):
                data[key].pop(team)
        return data

    def test_eight_contexts_have_independent_fields_native_flags_and_styles(self):
        data = self.defaults()
        count = 0
        for team in ('ally', 'enemy'):
            for state in ('alive', 'dead'):
                for mode in ('normal', 'extended'):
                    count += 1
                    data['customFields'][team][state][mode] = [{'format': str(count), 'x': count}]
                    data['markers'][team][state][mode]['playerName'] = count % 2 == 0
                    data['healthBar'][team][state][mode] = {'x': count, 'border': {'color': '#123456'}}
                    data['icons'][team][state][mode] = {'level': {'x': count}}
                    data['damageText'][team][state][mode] = {'rise': count}
        before = copy.deepcopy(data)
        result = self.load('core.vehicle_markers.config').prepare(data)
        count = 0
        for team in ('ally', 'enemy'):
            for state in ('alive', 'dead'):
                for mode in ('normal', 'extended'):
                    count += 1
                    profile = result['customFields']['profiles'][team][state][mode]
                    self.assertEqual(profile['fields'][0]['x'], count)
                    self.assertEqual(profile['native']['playerName'], count % 2 == 0)
                    self.assertEqual(profile['healthBar']['x'], count)
                    self.assertEqual(profile['healthBar']['border']['color'], '#123456')
                    self.assertEqual(profile['healthBar']['border']['width'], 1)
                    self.assertEqual(profile['icons']['level']['x'], count)
                    self.assertEqual(profile['damageText']['rise'], count)
        self.assertEqual(data, before)
        result['customFields']['profiles']['enemy']['dead']['normal']['healthBar']['x'] = 99
        self.assertEqual(result['customFields']['profiles']['ally']['dead']['normal']['healthBar']['x'], 3)

    def test_legacy_layout_migration_keeps_values_and_copies_dead_layout_to_each_team(self):
        old = self.legacy()
        old['customFields']['enemy']['normal'][0]['x'] = 123
        old['healthBar']['width'] = 120
        before = copy.deepcopy(old)
        layouts = self.load('core.vehicle_markers.layouts')
        converted = layouts.migrate(old)
        self.assertEqual(old, before)
        self.assertEqual(converted['customFields']['enemy']['alive']['normal'][0]['x'], 123)
        self.assertEqual(converted['customFields']['ally']['dead'], old['customFields']['dead'])
        converted['customFields']['enemy']['dead']['extended'][0]['x'] = 555
        self.assertNotEqual(converted['customFields']['ally']['dead']['extended'][0]['x'], 555)
        self.assertEqual(layouts.migrate(converted), converted)
        prepared = self.load('core.vehicle_markers.config').prepare(converted)
        self.assertEqual(prepared['customFields']['profiles']['enemy']['alive']['normal']['healthBar']['width'], 120)

    def test_store_converts_the_seven_file_layout_once_and_keeps_backups(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        api = self.load('settings.vehicle_markers_store')
        old = {'general.json': {'enabled': False, 'debug': True, 'colorRating': 1, 'ratingType': 'eff',
                                'turretMarkers': {'highVulnerability': '#', 'lowVulnerability': '~', 'unknown': '?'}},
               'markers.json': {'markers': {'enabled': True}}, 'colors.json': {'colors': {'colorBlind': {'enabled': False}}},
               'healthbar.json': {'healthBar': {'width': 80}}, 'fields.json': {'customFields': {'enabled': True}},
               'damage.json': {'damageText': {}}, 'icons.json': {'icons': {}}}
        originals = {}
        for name, document in old.items():
            originals[name] = json.dumps(document).encode('utf-8')
            with open(os.path.join(directory, name), 'wb') as stream:
                stream.write(originals[name])
        result = api.VehicleMarkersStore(directory).load()
        self.assertFalse(result['enabled'])
        self.assertTrue(result['markers']['debug'])
        self.assertEqual((result['markers']['colorRating'], result['markers']['ratingType']), (1, 'eff'))
        self.assertEqual(result['markers']['turretMarkers'], {'highVulnerability': '#', 'lowVulnerability': '~'})
        self.assertFalse(result['markers']['colors']['colorBlind']['enabled'])
        # Layouts come from the XVM defaults, not from the old health bar.
        self.assertEqual(result['markersAliveNormal'], self.xvm_defaults()['markersAliveNormal'])
        for name, content in originals.items():
            with open(os.path.join(directory, name + '.v2.bak'), 'rb') as stream:
                self.assertEqual(stream.read(), content)
        self.assertEqual(sorted(name for name in os.listdir(directory) if name.endswith('.json')),
                         sorted(api.FILES))
        self.assertEqual(api.VehicleMarkersStore(directory).load(), result)

    def test_bad_scope_or_style_is_rejected(self):
        prepare = self.load('core.vehicle_markers.config').prepare
        for block in ('markers', 'customFields', 'healthBar', 'damageText', 'icons'):
            data = self.defaults()
            data[block]['enemy']['dead']['invalid'] = {}
            with self.assertRaises(ValueError):
                prepare(data)
        data = self.defaults()
        data['icons']['enemy']['dead']['extended'] = {'level': {'scale': 99}}
        with self.assertRaises(ValueError):
            prepare(data)

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
        data['markersAliveNormal']['def']['tankName']['y'] = -40
        store.save(data)
        loaded = store.load()
        self.assertEqual(loaded['markersAliveNormal']['def']['tankName']['y'], -40)
        # Templates stay references in the file.
        self.assertEqual(loaded['markersAliveNormal']['ally']['textFields'][0], '${def.tankName}')
        broken = copy.deepcopy(data)
        broken['markersAliveNormal']['ally']['healthBar']['height'] = 0
        with self.assertRaises(ValueError):
            store.save(broken)
        self.assertEqual(store.load(), data)
        self.assertEqual(sorted(os.listdir(root)), sorted(store.filenames))

    def xvm_defaults(self):
        documents = {}
        directory = os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'vehicle_markers')
        xvm = self.load('core.vehicle_markers.xvm')
        for name in xvm.FILES:
            with open(os.path.join(directory, name), 'rb') as stream:
                documents[name] = json.loads(stream.read().decode('utf-8'))
        return xvm.join(documents)

    def defaults(self):
        # The internal schema produced from the XVM files; validation and Flash consume it.
        return self.load('core.vehicle_markers.xvm').adapt(self.xvm_defaults())

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
        self.assertEqual(data['colors']['colorBlind']['team']['enemyDead'], '#C48CFF')

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
        data['customFields']['enemy']['alive']['normal'][0]['format'] = '{{unsupported}}'
        with self.assertRaises(ValueError):
            prepare(data)
        data = self.defaults()
        data['colors']['hp'] = [{'value': 50, 'color': '#FFFFFF'}]
        with self.assertRaises(ValueError):
            prepare(data)

    def test_custom_bar_and_contour_preserve_account_preferences(self):
        data = self.load('core.vehicle_markers.config').prepare(self.defaults())
        apply = self.load('core.vehicle_markers.presentation').apply
        native = dict((team, {'markerBaseHpIndicator': True, 'markerAltHpIndicator': True,
                             'markerBaseIcon': True, 'markerAltIcon': True})
                      for team in ('ally', 'enemy', 'dead'))
        changed = apply(native, data['markers'], data['customFields'])
        for team in native:
            self.assertEqual(changed[team], native[team])
        profile = changed['__vmTest']['profiles']['enemy']['alive']['normal']
        self.assertTrue(profile['healthBar']['enabled'])
        self.assertTrue(profile['icons']['vehicle']['enabled'])
        for team in native:
            self.assertTrue(native[team]['markerBaseHpIndicator'])

    def test_referenced_field_survives_store_defaults_and_compiles_overrides(self):
        data = self.xvm_defaults()
        data['markersAliveNormal']['def']['custom'] = {'format': '{{r}}', 'x': -30, 'align': 'left'}
        data['markersAliveNormal']['enemy']['textFields'] = [{'$ref': {'path': 'def.custom'}, 'y': -90}]
        result = self.load('core.vehicle_markers.config').prepare(data)
        field = result['customFields']['profiles']['enemy']['alive']['normal']['fields'][0]
        self.assertEqual((field['x'], field['y']), (-30, -90))
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        store = self.load('settings.vehicle_markers_store').VehicleMarkersStore(root)
        store.save(data)
        loaded = store.load()
        self.assertEqual(loaded['markersAliveNormal']['enemy']['textFields'], data['markersAliveNormal']['enemy']['textFields'])
