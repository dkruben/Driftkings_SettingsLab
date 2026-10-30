import json
import os
import shutil
import tempfile
import copy
from support import RuntimeTest, source, module


class MainClockSettingsTests(RuntimeTest):
    FORMATS = [{'x': 4, 'y': 93, 'screenHAlign': 'right',
                'format': "<img src='gui/maps/custom/clock.png'>"},
               {'x': -10, 'y': 80, 'textFormat': {'align': 'right', 'valign': 'bottom'},
                'format': "<font size='36'>%H:%M</font>"}]
    HANGAR_CLOCK = {'clock': False, 'clockBackground': True, 'clockScale': 125, 'clockX': -456, 'clockY': 123,
                    'customClockText': '%H:%M', 'lowAmmoPercentage': 30}

    def setUp(self):
        super(MainClockSettingsTests, self).setUp()
        path = os.path.join(os.path.dirname(__file__), '../../../res/configs/driftkings/default/main.json')
        with open(path, 'rb') as stream:
            self.defaults = json.loads(stream.read().decode('utf-8-sig'))
        self.api = self.load('settings.loader')
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)
        os.makedirs(os.path.join(self.folder, 'default'))
        self.path = os.path.join(self.folder, 'default', 'main.json')
        self.hangar = os.path.join(self.folder, 'default', 'hangar_preferences.json')
        self.loader = self.api.SettingsLoader(self.folder, settings=object())
        self.loader._active = 'default'

    def write(self, values, path=None):
        with open(path or self.path, 'w') as stream:
            json.dump(values, stream)

    def read(self, path=None):
        with open(path or self.path, 'rb') as stream:
            return json.loads(stream.read().decode('utf-8'))

    def main(self):
        return self.loader.load('main', self.defaults)['clock']

    def test_defaults_hold_the_clock_switch_and_fields(self):
        self.assertTrue(self.defaults['enabled'])
        self.assertTrue(self.defaults['clock']['enabled'])
        self.assertEqual(self.defaults['clock']['formats'][0]['format'],
                         "<img src='gui/maps/driftkings/clock/clockbg.svg'>")
        self.assertEqual(self.main(), self.defaults['clock'])

    def test_clock_object_is_kept_and_saving_other_options_keeps_it(self):
        self.write({'clock': {'enabled': True, 'formats': self.FORMATS}})
        self.assertEqual(self.main()['formats'], self.FORMATS)
        self.loader.save('main', {'enabled': False})
        stored = self.read()
        self.assertEqual(stored['clock']['formats'], self.FORMATS)
        self.assertFalse(stored['enabled'])


    def test_disabled_hangar_does_not_override_explicit_main_clock(self):
        self.write(dict(self.HANGAR_CLOCK, enabled=False), self.hangar)
        self.write({'enabled': True, 'clock': {'enabled': True, 'formats': self.FORMATS}})
        self.assertTrue(self.main()['enabled'])


    def test_clock_must_stay_an_object_with_a_list_of_fields(self):
        self.api.validate_types(self.defaults, {'clock': {'enabled': False, 'formats': []}})
        for values in ({'clock': {'formats': 'text'}}, {'clock': {'enabled': 1}}):
            self.assertRaises(ValueError, self.api.validate_types, self.defaults, values)

    def test_panel_edits_sparse_clock_fields_and_persists_nested_values(self):
        api = source('settings/definitions/components/main.py', {
            'driftkings.settings.definitions.base': module(SectionDefinition=object)})
        config = api['MainSettings']()
        config.data = config.normalize_loaded(copy.deepcopy(self.defaults))
        parser = self.load('core.locale_catalog').parse_catalog
        path = os.path.join(os.path.dirname(__file__), '../../../mod/res/mods/driftkings/text/pt.yml')
        with open(path, 'rb') as stream:
            catalog = parser(stream.read())['TEXT']
        config.i18n = dict(catalog['common'], **catalog['main'])
        config.getSettingsDefaults = lambda: config.normalize_loaded(copy.deepcopy(self.defaults))
        service = self.load('settings.service').settings_service
        original = service.apply
        self.addCleanup(setattr, service, 'apply', original)
        def apply(section, values):
            candidate = section.normalize_changes(values, values)
            section.data = self.loader.save('main', candidate)
        service.apply = apply
        registry = self.load('settings.registry').SettingsRegistry()
        registry.register(config)
        description = registry.describe('main')
        values = description['values']
        prefix = 'clock.formats.'
        self.assertEqual(len(values), 34)  # two switches and 16 properties per field
        values[prefix + '0.x'] = 42
        values[prefix + '0.shadow.enabled'] = True
        values[prefix + '0.shadow.alpha'] = 55
        values[prefix + '1.format'] = '<font size="28">%H:%M:%S</font>'
        values[prefix + '1.textFormat.color'] = '#aabbcc'
        values[prefix + '1.screenHAlign'] = 1
        registry.apply('main', values)
        stored = self.main()['formats']
        self.assertEqual(stored[0]['x'], 42)
        self.assertTrue(stored[0]['shadow']['enabled'])
        self.assertEqual(stored[0]['shadow']['alpha'], 55)
        self.assertEqual(stored[1]['format'], values[prefix + '1.format'])
        self.assertEqual(stored[1]['textFormat']['color'], '#aabbcc')
        self.assertEqual(stored[1]['screenHAlign'], 'center')
        self.assertEqual(stored[0]['format'], self.defaults['clock']['formats'][0]['format'])
