# -*- coding: utf-8 -*-
"""Legacy JSON compatibility contracts; all writes stay in a temporary profile.

Characterization, not migration: unknown keys and duplicate JSON keys retain
their current semantics. No production normalization is replaced by a mock.
"""
import copy
import json
import os
import shutil
import sys
import tempfile

from support import ROOT, RuntimeTest, module, source
from support.settings import load_source


class LegacySettingsRegressionTests(RuntimeTest):
    def setUp(self):
        super(LegacySettingsRegressionTests, self).setUp()
        self.root = tempfile.mkdtemp(prefix='dk-legacy-settings-')
        self.addCleanup(shutil.rmtree, self.root)
        self.defaults = self.load('settings.default_values').DEFAULTS
        self.loader_api = self.load('settings.loader')
        self.settings = self.load('settings.settings_data').SettingsData()
        self.loader = self.loader_api.SettingsLoader(self.root, self.settings)
        self.store = self.load('settings.store')
        self.service = self.load('settings.service').SettingsService(self.settings, self.loader)
        # These engine APIs are consulted during real SectionDefinition setup.
        for name, stub in [('Keys', module()), ('helpers', module(getClientLanguage=lambda: 'en')),
                           ('driftkings.core.hooks', module(hooks=module(current=None)))]:
            previous = sys.modules.get(name)
            self.addCleanup(self.restore_module, name, previous)
            sys.modules[name] = stub
        with open(os.path.join(ROOT, 'mod/res/mods/driftkings/text/en.yml'), 'rb') as stream:
            self.text = self.load('core.locale_catalog').parse_catalog(stream.read())['TEXT']
        self.legacy_autoaim = {'enabled': False, 'angle': 9.0, 'catchHiddenTarget': True,
                               'disableArtyMode': False, 'personalNote': {'keep': [1, 2]}}
        self.legacy_clock = {'clock': False, 'clockStyle': 4, 'clockSeconds': False,
                             'clock24Hour': False, 'customClockFormat': True,
                             'text': 'legacy', 'panel': {'x': 999}, 'clockX': 999,
                             'customClockText': 'old format'}

    @staticmethod
    def restore_module(name, previous):
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous

    def path(self, name, profile='default'):
        return os.path.join(self.root, profile, name + '.json')

    def write(self, name, values, raw=None):
        path = self.path(name)
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as stream:
            stream.write(json.dumps(values).encode('utf-8') if raw is None else raw)
        return path

    def bytes(self, path):
        with open(path, 'rb') as stream:
            return stream.read()

    def section(self, name):
        locations = {'autoaim_target_indicator': 'battle', 'hangar_preferences': 'lobby', 'main': 'components'}
        classes = {'autoaim_target_indicator': 'AutoaimTargetIndicatorSettings',
                   'hangar_preferences': 'HangarPreferencesSettings', 'main': 'MainSettings'}
        base = self.load('settings.definitions.base')
        definition = source('settings/definitions/%s/%s.py' % (locations[name], name),
                            {'driftkings.settings.definitions.base': base})[classes[name]]
        config = definition.__new__(definition)
        config.loadLang = lambda: config.i18n.update(dict(self.text['common'], **self.text[name]))
        self.service.initialize(config)
        return config

    def panel(self, config):
        registry = self.load('settings.registry').SettingsRegistry()
        registry.register(config)
        # The registry deliberately delegates to the singleton; bind that seam
        # to a real service whose loader is confined to this test's directory.
        api = self.load('settings.service')
        previous = api.settings_service
        api.settings_service = self.service
        self.addCleanup(setattr, api, 'settings_service', previous)
        return registry

    def test_autoaim_legacy_load_defaults_and_no_read_rewrite(self):
        path = self.write('autoaim_target_indicator', self.legacy_autoaim)
        before = self.bytes(path)
        config = self.section('autoaim_target_indicator')
        self.assertFalse(config.data['enabled'])
        self.assertEqual(config.data['color'], self.defaults[config.NAME]['color'])
        for key, value in self.legacy_autoaim.items():
            self.assertEqual(config.data[key], value)
        self.assertEqual(self.bytes(path), before)

    def test_autoaim_panel_excludes_retired_keys(self):
        self.write('autoaim_target_indicator', self.legacy_autoaim)
        config = self.section('autoaim_target_indicator')
        description = self.panel(config).describe(config.NAME)
        self.assertEqual(set(description['values']), set(('enabled', 'color')))

    def test_autoaim_valid_color_persists_unknown_keys_and_restarts(self):
        self.write('autoaim_target_indicator', self.legacy_autoaim)
        config = self.section('autoaim_target_indicator')
        registry = self.panel(config)
        values = registry.describe(config.NAME)['values']
        values['color'] = '#123456'
        registry.apply(config.NAME, values)
        restarted = self.loader_api.SettingsLoader(self.root, self.settings)
        result = restarted.load(config.NAME, self.defaults[config.NAME])
        self.assertEqual(result['color'], '#123456')
        for key, value in self.legacy_autoaim.items():
            self.assertEqual(result[key], value)
        self.assertEqual(self.store.read_object(self.path(config.NAME)), result)

    def test_autoaim_invalid_color_rejected_without_file_or_live_changes(self):
        path = self.write('autoaim_target_indicator', self.legacy_autoaim)
        config = self.section('autoaim_target_indicator')
        registry = self.panel(config)
        before, live = self.bytes(path), copy.deepcopy(config.data)
        values = registry.describe(config.NAME)['values']
        values['color'] = 'not-a-color'
        self.assertRaises(ValueError, registry.apply, config.NAME, values)
        self.assertEqual(self.bytes(path), before)
        self.assertEqual(config.data, live)

    def test_old_hangar_clock_does_not_replace_missing_main_defaults(self):
        path = self.write('hangar_preferences', self.legacy_clock)
        before = self.bytes(path)
        config = self.section('main')
        self.assertEqual(config.data['clock']['enabled'], self.defaults['main']['clock']['enabled'])
        self.assertEqual([x['format'] for x in config.data['clock']['formats']],
                         [x['format'] for x in self.defaults['main']['clock']['formats']])
        self.assertEqual(self.bytes(path), before)

    def test_missing_clock_in_existing_main_is_defaulted_without_rewrite(self):
        path = self.write('main', {'enabled': False, 'personalNote': 'keep'})
        before = self.bytes(path)
        result = self.loader.load('main', self.defaults['main'])
        self.assertEqual(result['clock'], self.defaults['main']['clock'])
        self.assertFalse(result['enabled'])
        self.assertEqual(self.bytes(path), before)

    def test_current_clock_wins_and_survives_save_and_restart(self):
        old = self.write('hangar_preferences', self.legacy_clock)
        before = self.bytes(old)
        formats = [{'format': '%H:%M custom', 'x': 37, 'textFormat': {'color': '#abcdef'}}]
        self.write('main', {'clock': {'enabled': False, 'formats': formats}, 'personalNote': 42})
        config = self.section('main')
        self.service.apply(config, {'enabled': False})
        self.service.apply(config, {'clock': {'enabled': True}})
        result = self.loader_api.SettingsLoader(self.root, self.settings).load('main', self.defaults['main'])
        self.assertTrue(result['clock']['enabled'])
        self.assertFalse(result['enabled'])
        self.assertEqual(result['clock']['formats'][0]['format'], formats[0]['format'])
        self.assertEqual(result['clock']['formats'][0]['x'], 37)
        self.assertEqual(result['clock']['formats'][0]['textFormat']['color'], '#abcdef')
        self.assertEqual(result['personalNote'], 42)
        self.assertEqual(self.bytes(old), before)

    def assert_rejected_original(self, raw):
        path = self.write('autoaim_target_indicator', None, raw)
        self.assertRaises(ValueError, self.loader.load, 'autoaim_target_indicator',
                          self.defaults['autoaim_target_indicator'])
        self.assertEqual(self.bytes(path), raw)

    def test_malformed_json_is_rejected_without_rewrite(self):
        self.assert_rejected_original(b'{"enabled":')

    def test_utf8_bom_is_loaded_without_rewrite(self):
        raw = b'\xef\xbb\xbf{"enabled":false,"note":"caf\xc3\xa9"}'
        path = self.write('autoaim_target_indicator', None, raw)
        result = self.loader.load('autoaim_target_indicator', self.defaults['autoaim_target_indicator'])
        self.assertEqual(result['note'], u'caf\xe9')
        self.assertFalse(result['enabled'])
        self.assertEqual(self.bytes(path), raw)

    def test_non_object_json_roots_are_rejected_without_rewrite(self):
        for raw in (b'[]', b'null', b'42', b'"text"'):
            self.assert_rejected_original(raw)

    def test_known_invalid_types_are_rejected_without_rewrite(self):
        for raw in (b'{"enabled":1}', b'{"enabled":"false"}', b'{"color":42}'):
            self.assert_rejected_original(raw)

    def test_invalid_section_is_not_registered_or_rewritten(self):
        raw = b'{"enabled":"invalid"}'
        path = self.write('autoaim_target_indicator', None, raw)
        self.assertRaises(ValueError, self.section, 'autoaim_target_indicator')
        self.assertNotIn('autoaim_target_indicator', self.settings.configs)
        self.assertEqual(self.bytes(path), raw)

    def test_clock_non_list_formats_rejected_without_rewrite(self):
        raw = b'{"clock":{"formats":"invalid"}}'
        path = self.write('main', None, raw)
        self.assertRaises(ValueError, self.section, 'main')
        self.assertEqual(self.bytes(path), raw)

    def test_interrupted_write_recovers_previous_document_in_temporary_profile(self):
        path = self.write('autoaim_target_indicator', self.legacy_autoaim)
        original = self.bytes(path)
        os.rename(path, path + '.previous')
        result = self.loader.load('autoaim_target_indicator', self.defaults['autoaim_target_indicator'])
        self.assertEqual(self.bytes(path), original)
        self.assertFalse(os.path.exists(path + '.previous'))
        self.assertFalse(result['enabled'])
        self.assertEqual(result['personalNote'], self.legacy_autoaim['personalNote'])

    def test_duplicate_keys_characterize_last_value_wins(self):
        # KNOWN LIMITATION: duplicates are accepted by json.loads, not rejected.
        raw = b'{"enabled":true,"enabled":false}'
        path = self.write('autoaim_target_indicator', None, raw)
        result = self.loader.load('autoaim_target_indicator', self.defaults['autoaim_target_indicator'])
        self.assertFalse(result['enabled'])
        self.assertEqual(self.bytes(path), raw)

    def test_unknown_nested_keys_survive_save_and_reload(self):
        self.write('autoaim_target_indicator', self.legacy_autoaim)
        defaults = self.defaults['autoaim_target_indicator']
        result = self.loader.load('autoaim_target_indicator', defaults)
        self.loader.save('autoaim_target_indicator', {'enabled': True})
        reloaded = self.loader.load('autoaim_target_indicator', defaults)
        self.assertEqual(reloaded['personalNote'], result['personalNote'])
        self.assertTrue(reloaded['enabled'])

    def test_clock_list_elements_characterize_generic_and_specific_limits(self):
        # KNOWN LIMITATION: generic validation checks the list, not its elements;
        # MainSettings skips non-dictionaries and preserves them in the document.
        raw = b'{"clock":{"formats":[7,"unexpected",null]}}'
        path = self.write('main', None, raw)
        self.loader_api.validate_types(self.defaults['main'], json.loads(raw.decode('utf-8')))
        config = self.section('main')
        self.assertEqual(config.data['clock']['formats'], [7, 'unexpected', None])
        self.assertEqual(self.bytes(path), raw)
        self.assertEqual(set(self.panel(config).describe('main')['values']),
                         set(('enabled', 'clock.enabled')))

    def test_component_specific_list_validation_rejects_bad_panel_entries(self):
        resolver = self.load('settings.team_panel_store').resolve_fields
        for entries in ([7], [None], ['missing-template']):
            if entries == ['missing-template']:
                # Strings are valid literal formats, not implicit references.
                self.assertEqual(resolver(entries, {}), [{'format': 'missing-template'}])
            else:
                self.assertRaises(ValueError, resolver, entries, {})
        self.assertRaises(ValueError, resolver, [{'ref': 'missing'}], {})

    def test_profile_clone_selection_is_next_start_and_preserves_source(self):
        self.write('autoaim_target_indicator', self.legacy_autoaim)
        defaults = self.defaults['autoaim_target_indicator']
        self.loader.load('autoaim_target_indicator', defaults)
        before = self.bytes(self.path('autoaim_target_indicator'))
        self.loader.clone('personal')
        self.assertTrue(self.loader.select('personal'))
        self.assertEqual(self.loader.active, 'default')
        restarted = self.loader_api.SettingsLoader(self.root, self.settings)
        self.assertEqual(restarted.active, 'personal')
        self.assertEqual(restarted.load('autoaim_target_indicator', defaults)['personalNote'],
                         self.legacy_autoaim['personalNote'])
        restarted.save('autoaim_target_indicator', {'color': '#654321'})
        self.assertEqual(self.bytes(self.path('autoaim_target_indicator')), before)
        self.assertEqual(restarted.load('autoaim_target_indicator', defaults)['color'], '#654321')

    def test_new_profile_creates_current_defaults_and_valid_selector(self):
        result = self.loader.load('autoaim_target_indicator', self.defaults['autoaim_target_indicator'])
        self.assertEqual(result, self.defaults['autoaim_target_indicator'])
        self.assertEqual(self.store.read_object(self.path('autoaim_target_indicator')), result)
        self.assertEqual(self.store.read_object(os.path.join(self.root, 'load.json')),
                         {'loadConfig': 'default'})

    def test_reset_current_controls_preserves_unknown_persisted_values(self):
        self.write('autoaim_target_indicator', dict(self.legacy_autoaim, color='#123456'))
        config = self.section('autoaim_target_indicator')
        registry = self.panel(config)
        controls_api = self.load('settings.panel.controls')
        session_api = load_source('settings/panel/session.py',
                                  {'driftkings.settings.panel': module(logger=module())})
        description = registry.describe(config.NAME)
        controls = [controls_api.Control('checkbox', 'enabled', default=True).finalize(),
                    controls_api.Control('color', 'color', default=self.defaults[config.NAME]['color']).finalize()]
        mod = module(controls=controls, index=dict((c.id, c) for c in controls),
                     values=copy.deepcopy(description['values']), saved=copy.deepcopy(description['values']),
                     value_controls=lambda: controls)
        def apply_values(name, values):
            candidate = dict(mod.values, **values)
            registry.apply(config.NAME, candidate)
            mod.values.update(registry.describe(config.NAME)['values'])
            return values
        def save(name):
            mod.saved = copy.deepcopy(mod.values)
        bridge = module(mods={'autoaim': mod}, dependency_status=lambda mod: [],
                        apply_values=apply_values, save=save)
        session = session_api['EditSession'](bridge)
        session.reset('autoaim')
        session.save()
        persisted = self.store.read_object(self.path(config.NAME))
        self.assertTrue(persisted['enabled'])
        self.assertEqual(persisted['color'], self.defaults[config.NAME]['color'])
        for key in ('angle', 'catchHiddenTarget', 'disableArtyMode', 'personalNote'):
            self.assertEqual(persisted[key], self.legacy_autoaim[key])
