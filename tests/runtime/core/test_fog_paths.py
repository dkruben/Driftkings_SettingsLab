# -*- coding: utf-8 -*-
"""Fog runtime follows the installed mod path without allowing arbitrary paths."""
import json
import os
import shutil
import tempfile
import zipfile

from support import RuntimeTest, module, source


class FogPathTests(RuntimeTest):
    def setUp(self):
        super(FogPathTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.api = source('core/fog_package.py', {
            'driftkings.core.updater.installer': module(read_resource=None),
            'driftkings.settings.service': module(settings_service=None)})
        for name in ('2.4.2.0', '2.4.2.0 Common Test'):
            os.makedirs(os.path.join(self.root, 'mods', name))

    def paths(self, values):
        with open(os.path.join(self.root, 'paths.xml'), 'w') as stream:
            stream.write('<root><Paths>' + ''.join('<Path>' + value + '</Path>' for value in values) + '</Paths></root>')

    def test_ct_declared_folder_wins_even_when_numeric_folder_exists(self):
        self.paths(['./res_mods/2.4.2.0 Common Test', './mods/2.4.2.0 Common Test'])
        self.assertEqual(self.api['mod_directory'](self.root, '2.4.2.0'),
                         os.path.join(self.root, 'mods', '2.4.2.0 Common Test'))

    def test_production_and_missing_paths_file_use_numeric_folder(self):
        self.assertEqual(self.api['mod_directory'](self.root, '2.4.2.0'), os.path.join(self.root, 'mods', '2.4.2.0'))
        self.paths(['./mods/2.4.2.0'])
        self.assertEqual(self.api['mod_directory'](self.root, '2.4.2.0'), os.path.join(self.root, 'mods', '2.4.2.0'))

    def test_unsafe_unknown_or_ambiguous_paths_are_rejected(self):
        for values in (['./mods/../other'], ['./mods/2.4.1.1'],
                       ['./mods/2.4.2.0', './mods/2.4.2.0 Common Test']):
            self.paths(values)
            self.assertRaises(ValueError, self.api['mod_directory'], self.root, '2.4.2.0')
        self.assertRaises(ValueError, self.api['mod_directory'], self.root, '../2.4.2.0')

    def test_declared_folder_must_exist(self):
        self.paths(['./mods/2.4.2.0 Common Test'])
        os.rmdir(os.path.join(self.root, 'mods', '2.4.2.0 Common Test'))
        self.assertRaises(ValueError, self.api['mod_directory'], self.root, '2.4.2.0')


class _Config(object):
    """Stand-in for the battle preferences section: only the data and i18n attributes are used."""
    def __init__(self, data):
        self.data = data
        self.i18n = {}


class FogPreferenceTests(RuntimeTest):
    """Legacy resolution of removeFog, the scheduling guards and idempotent migration, on temporary folders."""

    REMOVE = 'removeFog'

    def setUp(self):
        super(FogPreferenceTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.store = module(read_object=self._read_object, SettingsStore=_JsonStore)
        self.api = source('core/fog_package.py', {
            'driftkings.core.updater.installer': module(read_resource=None),
            'driftkings.settings.service': module(settings_service=None),
            'driftkings.settings.store': self.store})
        self.profile = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'default', 'battle_preferences.json')
        self.client_mods = os.path.join(self.root, 'mods', '2.4.2.0 Common Test')
        os.makedirs(os.path.dirname(self.profile))
        os.makedirs(self.client_mods)
        self.package = os.path.join(self.client_mods, 'Driftkings.RemoveFog.wotmod')
        # The native stamp needs a client res/packages tree; tests only need "a package is present or not".
        self.api['package_current'] = lambda path, stamp: os.path.isfile(path)
        self.api['source_stamp'] = lambda root: 'test-stamp'

    @staticmethod
    def _read_object(path):
        with open(path, 'rb') as stream:
            value = json.loads(stream.read().decode('utf-8-sig'))
        if not isinstance(value, dict):
            raise ValueError('Expected a JSON object: ' + path)
        return value

    def write_profile(self, values):
        with open(self.profile, 'wb') as stream:
            stream.write(json.dumps(values).encode('utf-8'))

    def read_profile(self):
        return self._read_object(self.profile)

    def write_package(self, mod_id='driftkings.removefog'):
        with zipfile.ZipFile(self.package, 'w') as archive:
            archive.writestr('meta.xml', '<root><id>%s</id><version>1.0.0</version></root>' % mod_id)

    def controller(self, data, package=None):
        controller = self.api['FogPackageController'](_Config(data))
        controller.active = True
        controller.root = self.root
        controller.version = '2.4.2.0'
        controller.target = package or self.package
        controller.scheduled = []
        controller.schedule = lambda desired: controller.scheduled.append(desired)
        return controller

    def classify(self, package=None):
        return self.api['classify_preference'](self.profile, package or self.package)

    # Default off and the fresh installation
    def test_default_value_in_distribution_source_is_off(self):
        source_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'res', 'configs', 'driftkings',
                                   'default', 'battle_preferences.json')
        self.assertIs(self._read_object(os.path.normpath(source_file))[self.REMOVE], False)

    def test_fresh_installation_without_package_schedules_nothing(self):
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        self.assertEqual(self.classify(), self.api['DEFAULT_OFF'])
        self.assertEqual(controller.prepare(self.profile), self.api['DEFAULT_OFF'])
        controller.changed(None, {})
        self.assertEqual(controller.scheduled, [])
        self.assertFalse(os.path.exists(self.package))

    # Explicit preferences
    def test_explicit_true_is_preserved_and_not_rewritten(self):
        self.write_profile({self.REMOVE: True, 'enabled': True})
        self.write_package()
        before = open(self.profile, 'rb').read()
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.prepare(self.profile), self.api['EXPLICIT'])
        self.assertIs(controller.config.data[self.REMOVE], True)
        self.assertEqual(open(self.profile, 'rb').read(), before)

    def test_explicit_false_with_package_is_not_removed_at_startup(self):
        self.write_profile({self.REMOVE: False, 'enabled': True})
        self.write_package()
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.prepare(self.profile), self.api['EXPLICIT'])
        controller.startup()
        self.assertEqual(controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    # Legacy profiles
    def test_legacy_profile_without_key_and_owned_package_is_migrated_to_true(self):
        self.write_profile({'enabled': True, 'color': '#F930F8'})
        self.write_package()
        controller = self.controller({self.REMOVE: False, 'enabled': True, 'color': '#F930F8'})
        self.assertEqual(controller.prepare(self.profile), self.api['LEGACY_MIGRATE'])
        self.assertIs(controller.config.data[self.REMOVE], True)
        self.assertEqual(self.read_profile(), {'enabled': True, 'color': '#F930F8', self.REMOVE: True})
        controller.changed(None, {})
        self.assertEqual(controller.scheduled, [])

    def test_legacy_profile_without_key_and_without_package_stays_off(self):
        self.write_profile({'enabled': True})
        before = open(self.profile, 'rb').read()
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.prepare(self.profile), self.api['DEFAULT_OFF'])
        self.assertEqual(open(self.profile, 'rb').read(), before)
        controller.changed(None, {})
        self.assertEqual(controller.scheduled, [])

    def test_inherited_default_is_not_taken_for_explicit_false(self):
        # A missing key with an owned package must migrate, never fall back to a destructive False.
        self.write_profile({'enabled': True})
        self.write_package()
        self.assertEqual(self.classify(), self.api['LEGACY_MIGRATE'])
        controller = self.controller({'enabled': True})
        controller.prepare(self.profile)
        controller.changed(None, {})
        self.assertEqual(controller.scheduled, [])

    def test_missing_key_in_live_data_never_schedules(self):
        controller = self.controller({'enabled': True})
        self.write_package()
        controller.changed(None, {})
        self.assertEqual(controller.scheduled, [])

    def test_package_of_another_client_folder_is_not_proof(self):
        # The same package in the numeric folder belongs to another realm and must not migrate this profile.
        other = os.path.join(self.root, 'mods', '2.4.2.0', 'Driftkings.RemoveFog.wotmod')
        os.makedirs(os.path.dirname(other))
        with zipfile.ZipFile(other, 'w') as archive:
            archive.writestr('meta.xml', '<root><id>driftkings.removefog</id></root>')
        self.write_profile({'enabled': True})
        self.assertEqual(self.classify(), self.api['DEFAULT_OFF'])
        self.assertEqual(self.read_profile(), {'enabled': True})

    # Migration safety
    def test_migration_is_idempotent_without_marker_file(self):
        self.write_profile({'enabled': True})
        self.write_package()
        self.api['migrate_preference'](self.profile, self.package)
        first = open(self.profile, 'rb').read()
        self.assertEqual(self.api['migrate_preference'](self.profile, self.package), self.api['EXPLICIT'])
        self.assertEqual(open(self.profile, 'rb').read(), first)
        siblings = sorted(os.listdir(os.path.dirname(self.profile)))
        self.assertEqual(siblings, ['battle_preferences.json'])

    def test_unrelated_profile_files_are_not_touched(self):
        self.write_profile({'enabled': True})
        self.write_package()
        other = os.path.join(os.path.dirname(self.profile), 'vehicle_health.json')
        with open(other, 'wb') as stream:
            stream.write(b'{"enabled": false}')
        self.api['migrate_preference'](self.profile, self.package)
        self.assertEqual(open(other, 'rb').read(), b'{"enabled": false}')

    def test_ambiguous_unreadable_profile_holds_and_does_not_write(self):
        with open(self.profile, 'wb') as stream:
            stream.write(b'{not json')
        self.write_package()
        before = open(self.profile, 'rb').read()
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.prepare(self.profile), self.api['AMBIGUOUS'])
        self.assertTrue(controller.hold)
        controller.changed(None, {})
        self.assertEqual(controller.scheduled, [])
        self.assertEqual(open(self.profile, 'rb').read(), before)

    def test_ambiguous_foreign_package_without_key_is_not_migrated_or_removed(self):
        self.write_profile({'enabled': True})
        self.write_package(mod_id='someone.else')
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.prepare(self.profile), self.api['AMBIGUOUS'])
        self.assertEqual(self.read_profile(), {'enabled': True})
        controller.changed(None, {'enabled': True})
        self.assertEqual(controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    def test_held_state_only_acts_on_explicit_user_change_of_the_option(self):
        self.write_profile({'enabled': True})
        self.write_package(mod_id='someone.else')
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        controller.prepare(self.profile)
        controller.changed('battle_preferences', {'enabled': False})
        self.assertEqual(controller.scheduled, [])
        controller.changed('battle_preferences', {self.REMOVE: False})
        self.assertEqual(controller.scheduled, [False])
        self.assertFalse(controller.hold)

    def test_unexpected_failure_while_resolving_holds_every_automatic_action(self):
        self.write_package()
        controller = self.controller({self.REMOVE: False, 'enabled': True})

        def failing(profile_file, package):
            raise IOError('simulated write failure')
        self.api['migrate_preference'] = failing
        self.assertEqual(controller.prepare(self.profile), self.api['AMBIGUOUS'])
        self.assertTrue(controller.hold)
        controller.changed(None, {})
        self.assertEqual(controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    def test_non_boolean_explicit_value_is_ambiguous(self):
        self.write_profile({self.REMOVE: 'yes'})
        self.write_package()
        self.assertEqual(self.classify(), self.api['AMBIGUOUS'])

    # Manual activation and deactivation
    def test_manual_activation_schedules_install(self):
        controller = self.controller({self.REMOVE: True, 'enabled': True}, package=self.package)
        self.assertFalse(os.path.exists(self.package))
        controller.changed('battle_preferences', {self.REMOVE: True})
        self.assertEqual(controller.scheduled, [True])

    def test_manual_deactivation_schedules_removal_only_through_helper(self):
        self.write_package()
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        controller.changed('battle_preferences', {self.REMOVE: False})
        self.assertEqual(controller.scheduled, [False])
        self.assertTrue(os.path.isfile(self.package))

    def test_master_switch_off_schedules_removal_path(self):
        self.write_package()
        controller = self.controller({self.REMOVE: True, 'enabled': False})
        controller.changed('battle_preferences', {'enabled': False})
        self.assertEqual(controller.scheduled, [False])

    def test_profile_isolation_is_per_profile_file(self):
        # Two profiles: only the active profile file is read and migrated.
        other_profile = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'other', 'battle_preferences.json')
        os.makedirs(os.path.dirname(other_profile))
        with open(other_profile, 'wb') as stream:
            stream.write(b'{"enabled": true}')
        self.write_profile({'enabled': True})
        self.write_package()
        self.api['migrate_preference'](self.profile, self.package)
        self.assertEqual(open(other_profile, 'rb').read(), b'{"enabled": true}')


class FogStartupTests(RuntimeTest):
    """Startup order, loader materialization, profile switching and manual changes, with mocks only."""

    REMOVE = 'removeFog'

    def setUp(self):
        super(FogStartupTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.profile_dir = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'default')
        self.profile = os.path.join(self.profile_dir, 'battle_preferences.json')
        self.client_mods = os.path.join(self.root, 'mods', '2.4.2.0')
        os.makedirs(self.profile_dir)
        os.makedirs(self.client_mods)
        self.package = os.path.join(self.client_mods, 'Driftkings.RemoveFog.wotmod')
        self.api = source('core/fog_package.py', {
            'driftkings.core.updater.installer': module(read_resource=None),
            'driftkings.settings.service': module(settings_service=None),
            'driftkings.settings.store': module(read_object=FogPreferenceTests._read_object,
                                                SettingsStore=_JsonStore)})
        self.api['package_current'] = lambda path, stamp: os.path.isfile(path)
        self.api['source_stamp'] = lambda root: 'test-stamp'

    def materialize(self, defaults):
        """Mirror settings/loader.py: a missing profile file receives the defaults before fog code runs."""
        if not os.path.isfile(self.profile):
            _JsonStore(self.profile).write(defaults)

    def write_package(self, mod_id='driftkings.removefog', path=None):
        target = path or self.package
        if not os.path.isdir(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        with zipfile.ZipFile(target, 'w') as archive:
            archive.writestr('meta.xml', '<root><id>%s</id></root>' % mod_id)

    def controller(self, data):
        controller = self.api['FogPackageController'](_Config(data))
        controller.active = True
        controller.root = self.root
        controller.version = '2.4.2.0'
        controller.target = self.package
        controller.scheduled = []
        controller.schedule = lambda desired: controller.scheduled.append(desired)
        return controller

    def launch(self, data):
        """Preference resolution followed by the automatic startup decision, as in production order."""
        controller = self.controller(data)
        controller.prepare(self.profile)
        controller.startup()
        return controller

    def test_preparation_runs_before_the_settings_signal_is_connected(self):
        order = []

        class Signal(object):
            def connect(self, callback, component=None, keys=None):
                order.append('connect')

            def disconnect(self, callback):
                pass

        class Event(object):
            def __iadd__(self, other):
                return self

            def __isub__(self, other):
                return self

        self.write_package()
        # start() takes the client root from the working directory; point it at the temporary client.
        previous_directory = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous_directory)
        api = source('core/fog_package.py', {
            'helpers': module(getClientVersion=lambda: '2.4.2.0'),
            'driftkings.common.utils': module(events=module(LobbyView=module(
                populate=module(after=module(event=Event()))))),
            'driftkings.core.callbacks': module(callbacks=None),
            'driftkings.core.updater.installer': module(read_resource=None),
            'driftkings.settings.service': module(settings_service=module(onModSettingsChanged=Signal())),
            'driftkings.settings.loader': module(settings_loader=module(path=lambda component: self.profile)),
            'driftkings.settings.store': module(read_object=FogPreferenceTests._read_object,
                                                SettingsStore=_JsonStore)})
        _JsonStore(self.profile).write({self.REMOVE: True, 'enabled': True})
        controller = api['FogPackageController'](_Config({self.REMOVE: False, 'enabled': True}))
        original_prepare = controller.prepare
        original_startup = controller.startup

        def recorded_prepare(profile_file):
            order.append('prepare')
            return original_prepare(profile_file)

        def recorded_startup():
            order.append('startup')
            return original_startup()
        controller.prepare = recorded_prepare
        controller.startup = recorded_startup
        controller.schedule = lambda desired: order.append(('schedule', desired))
        controller.start()
        self.assertLess(order.index('prepare'), order.index('connect'))
        self.assertIs(controller.config.data[self.REMOVE], True)
        self.assertNotIn(('schedule', False), order)

    def test_loader_materialized_false_with_package_from_another_profile_removes_nothing(self):
        # Case E: a new profile, no stored file; the loader materializes false; another profile's package exists.
        self.write_package()
        self.materialize({self.REMOVE: False, 'enabled': True})
        controller = self.launch({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))
        self.assertEqual(FogPreferenceTests._read_object(self.profile), {self.REMOVE: False, 'enabled': True})

    def test_new_profile_with_absent_file_and_package_is_not_migrated(self):
        self.write_package()
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.prepare(self.profile), self.api['DEFAULT_OFF'])
        self.assertFalse(os.path.exists(self.profile))
        controller.startup()
        self.assertEqual(controller.scheduled, [])

    def test_alternating_profiles_never_remove_the_shared_package(self):
        # Profile "default" has a materialized false; profile "other" has an explicit true. The package is shared.
        other_dir = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'other')
        os.makedirs(other_dir)
        other_profile = os.path.join(other_dir, 'battle_preferences.json')
        _JsonStore(other_profile).write({self.REMOVE: True, 'enabled': True})
        self.write_package()
        self.materialize({self.REMOVE: False, 'enabled': True})
        first = self.launch({self.REMOVE: False, 'enabled': True})
        self.assertEqual(first.scheduled, [])
        second = self.controller({self.REMOVE: True, 'enabled': True})
        second.prepare(other_profile)
        second.startup()
        self.assertEqual(second.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))
        self.assertIs(FogPreferenceTests._read_object(other_profile)[self.REMOVE], True)

    def test_explicit_true_is_preserved_and_installs_when_missing(self):
        _JsonStore(self.profile).write({self.REMOVE: True, 'enabled': True})
        controller = self.launch({self.REMOVE: True, 'enabled': True})
        self.assertEqual(controller.scheduled, [True])
        self.assertIs(FogPreferenceTests._read_object(self.profile)[self.REMOVE], True)

    def test_explicit_true_with_package_present_schedules_nothing(self):
        _JsonStore(self.profile).write({self.REMOVE: True, 'enabled': True})
        self.write_package()
        controller = self.launch({self.REMOVE: True, 'enabled': True})
        self.assertEqual(controller.scheduled, [])

    def test_explicit_false_is_preserved_without_removal(self):
        _JsonStore(self.profile).write({self.REMOVE: False, 'enabled': True})
        self.write_package()
        controller = self.launch({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    def test_manual_true_to_false_schedules_removal_after_close(self):
        _JsonStore(self.profile).write({self.REMOVE: True, 'enabled': True})
        self.write_package()
        controller = self.launch({self.REMOVE: True, 'enabled': True})
        controller.config.data[self.REMOVE] = False
        controller.changed('battle_preferences', {self.REMOVE: False})
        self.assertEqual(controller.scheduled, [False])
        self.assertTrue(os.path.isfile(self.package))

    def test_materialized_default_is_not_taken_as_a_manual_disable(self):
        self.materialize({self.REMOVE: False, 'enabled': True})
        self.write_package()
        controller = self.launch({self.REMOVE: False, 'enabled': True})
        self.assertEqual(controller.scheduled, [])

    def test_automatic_calls_with_a_false_result_never_schedule(self):
        self.write_package()
        controller = self.controller({self.REMOVE: False, 'enabled': True})
        controller.changed(None, {})
        controller.changed(None, {self.REMOVE: False})
        self.assertEqual(controller.scheduled, [])

    def test_realm_and_client_isolation_at_startup(self):
        other_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, other_root)
        other_package = os.path.join(other_root, 'mods', '2.4.2.0', 'Driftkings.RemoveFog.wotmod')
        self.write_package(path=other_package)
        _JsonStore(self.profile).write({self.REMOVE: True, 'enabled': True})
        controller = self.launch({self.REMOVE: True, 'enabled': True})
        self.assertEqual(controller.scheduled, [True])
        self.assertTrue(os.path.isfile(other_package))

    def test_ambiguous_startup_writes_nothing_and_schedules_nothing(self):
        with open(self.profile, 'wb') as stream:
            stream.write(b'{broken')
        self.write_package(mod_id='someone.else')
        before = open(self.profile, 'rb').read()
        controller = self.launch({self.REMOVE: False, 'enabled': True})
        self.assertTrue(controller.hold)
        self.assertEqual(controller.scheduled, [])
        self.assertEqual(open(self.profile, 'rb').read(), before)


class _JsonStore(object):
    """Atomic-enough test writer used in place of driftkings.settings.store.SettingsStore."""
    def __init__(self, path):
        self.path = path

    def write(self, document):
        with open(self.path, 'wb') as stream:
            stream.write(json.dumps(document, sort_keys=True).encode('utf-8'))
