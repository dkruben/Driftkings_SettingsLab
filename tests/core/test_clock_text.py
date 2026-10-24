import json
import os
import shutil
import tempfile
from support import RuntimeTest


class MainClockSettingsTests(RuntimeTest):
    FORMATS = [{'x': 4, 'y': 93, 'screenHAlign': 'right',
                'format': "<img src='gui/maps/driftkings/clock/clockbg.png'>"},
               {'x': -10, 'y': 80, 'textFormat': {'align': 'right', 'valign': 'bottom'},
                'format': "<font size='36'>%H:%M</font>"}]
    HANGAR_CLOCK = {'clock': False, 'clockBackground': True, 'clockScale': 125, 'clockX': -456, 'clockY': 123,
                    'customClockText': '%H:%M', 'lowAmmoPercentage': 30}

    def setUp(self):
        super(MainClockSettingsTests, self).setUp()
        path = os.path.join(os.path.dirname(__file__), '../../res/configs/driftkings/default/main.json')
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
                         "<img src='gui/maps/driftkings/clock/clockbg.png'>")
        self.assertEqual(self.main(), self.defaults['clock'])

    def test_clock_object_is_kept_and_saving_other_options_keeps_it(self):
        self.write({'clock': {'enabled': True, 'formats': self.FORMATS}})
        self.assertEqual(self.main()['formats'], self.FORMATS)
        self.loader.save('main', {'enabled': False})
        stored = self.read()
        self.assertEqual(stored['clock']['formats'], self.FORMATS)
        self.assertFalse(stored['enabled'])

    def test_plain_hangar_clock_text_becomes_one_field_at_its_position(self):
        self.write(self.HANGAR_CLOCK, self.hangar)
        clock = self.main()
        self.assertFalse(clock['enabled'])
        self.assertEqual(clock['formats'], [{'x': -456, 'y': 123, 'screenHAlign': 'right', 'width': 240, 'height': 100,
                                             'textFormat': {'align': 'right'}, 'format': '%H:%M'}])
        stored = self.read()
        self.assertNotIn('clockScale', stored)
        self.assertNotIn('lowAmmoPercentage', stored)
        # The previous file is left as it was.
        self.assertEqual(self.read(self.hangar), self.HANGAR_CLOCK)

    def test_hangar_clock_definitions_keep_their_fields(self):
        text = '// personal clock\n' + json.dumps({'formats': self.FORMATS})
        for value in (text, {'formats': self.FORMATS}, self.FORMATS):
            self.write(dict(self.HANGAR_CLOCK, customClockText=value), self.hangar)
            if os.path.isfile(self.path):
                os.remove(self.path)
            self.assertEqual(self.main()['formats'], self.FORMATS)

    def test_untouched_shipped_clock_takes_the_new_default_fields(self):
        self.write({'clock': True, 'clockX': -100, 'clockY': 80, 'customClockText': self.api.OLD_CLOCK_TEXT}, self.hangar)
        self.assertEqual(self.main(), self.defaults['clock'])

    def test_installer_created_main_file_still_receives_the_previous_clock(self):
        self.write(self.HANGAR_CLOCK, self.hangar)
        self.write({'enabled': True})
        self.assertEqual(self.main()['formats'][0]['x'], -456)

    def test_flat_clock_options_in_main_are_converted_before_hangar_ones(self):
        self.write(self.HANGAR_CLOCK, self.hangar)
        self.write({'clock': True, 'clockX': 10, 'customClockText': {'formats': self.FORMATS}})
        clock = self.main()
        self.assertTrue(clock['enabled'])
        self.assertEqual(clock['formats'], self.FORMATS)

    def test_unreadable_clock_json_falls_back_to_the_default_fields(self):
        self.write(dict(self.HANGAR_CLOCK, customClockText='{"formats": ['), self.hangar)
        self.assertEqual(self.main()['formats'], self.defaults['clock']['formats'])

    def test_clock_must_stay_an_object_with_a_list_of_fields(self):
        self.api.validate_types(self.defaults, {'clock': {'enabled': False, 'formats': []}})
        for values in ({'clock': {'formats': 'text'}}, {'clock': {'enabled': 1}}):
            self.assertRaises(ValueError, self.api.validate_types, self.defaults, values)
