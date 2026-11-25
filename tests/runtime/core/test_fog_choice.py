# -*- coding: utf-8 -*-
"""Optional Remove Fog: OFF by default, enabled and disabled only by an explicit user choice that persists."""
import json
import os
import shutil
import tempfile
import zipfile

from support import RuntimeTest, module, source

REMOVE = 'removeFog'


class _Changes(dict):
    """What the settings service passes to listeners: the changed keys and their origin."""
    def __init__(self, data, origin='user'):
        dict.__init__(self, data)
        self.origin = origin


class _Config(object):
    def __init__(self, data):
        self.data = dict(data)


class _JsonStore(object):
    def __init__(self, path):
        self.path = path

    def write(self, document):
        with open(self.path, 'wb') as stream:
            stream.write(json.dumps(document).encode('utf-8'))


def _read_object(path):
    with open(path, 'rb') as stream:
        value = json.loads(stream.read().decode('utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object: ' + path)
    return value


class OptionalRemoveFogTests(RuntimeTest):
    def setUp(self):
        super(OptionalRemoveFogTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.profile = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'default', 'battle_preferences.json')
        self.cache = os.path.join(self.root, 'mods', 'configs', 'driftkings', 'cache', 'fog')
        self.client_mods = os.path.join(self.root, 'mods', '2.4.2.0')
        self.package = os.path.join(self.client_mods, 'Driftkings.RemoveFog.wotmod')
        os.makedirs(os.path.dirname(self.profile))
        os.makedirs(self.client_mods)
        self.api = source('core/fog_package.py', {
            'driftkings.core.updater.installer': module(read_resource=None),
            'driftkings.settings.service': module(settings_service=None),
            'driftkings.settings.store': module(read_object=_read_object, SettingsStore=_JsonStore)})
        self.api['package_current'] = lambda path, stamp: os.path.isfile(path)
        self.api['source_stamp'] = lambda root: 'test-stamp'

    def write_package(self):
        with zipfile.ZipFile(self.package, 'w') as archive:
            archive.writestr('meta.xml', '<root><id>driftkings.removefog</id></root>')

    def controller(self, value=False):
        controller = self.api['FogPackageController'](_Config({REMOVE: value, 'enabled': True}))
        controller.active = True
        controller.root = self.root
        controller.version = '2.4.2.0'
        controller.target = self.package
        controller.cache = self.cache
        controller.scheduled = []
        controller.schedule = lambda desired: controller.scheduled.append(desired)
        return controller

    def launch(self, value=False):
        controller = self.controller(value)
        controller.prepare(self.profile)
        controller.startup()
        return controller

    def read_choice(self):
        return self.api['read_choice'](self.cache)

    # OFF by default and no automatic activation
    def test_fresh_profile_is_off_and_schedules_nothing(self):
        controller = self.launch()
        self.assertIs(controller.config.data[REMOVE], False)
        self.assertEqual(controller.scheduled, [])
        self.assertIsNone(self.read_choice())

    def test_installation_with_package_present_does_not_enable_it(self):
        self.write_package()
        controller = self.launch()
        self.assertEqual(controller.scheduled, [False])  # convergence removal only; never an install
        self.assertNotIn(True, controller.scheduled)

    # Explicit activation and deactivation, persisted across sessions
    def test_explicit_activation_is_recorded_and_installs(self):
        controller = self.launch()
        controller.config.data[REMOVE] = True
        controller.changed(object(), _Changes({REMOVE: controller.config.data[REMOVE]}))
        self.assertIs(self.read_choice(), True)
        self.assertEqual(controller.scheduled, [True])

    def test_explicit_deactivation_is_recorded_and_removes_through_helper(self):
        self.write_package()
        self.api['write_choice'](self.cache, True)
        controller = self.launch(True)
        controller.config.data[REMOVE] = False
        controller.changed(object(), _Changes({REMOVE: controller.config.data[REMOVE]}))
        self.assertIs(self.read_choice(), False)
        self.assertEqual(controller.scheduled, [False])

    def test_choice_persists_across_sessions_without_profile_value(self):
        self.api['write_choice'](self.cache, True)
        self.assertIs(self.launch().config.data[REMOVE], True)
        self.write_package()
        self.assertEqual(self.launch(True).scheduled, [])  # package already current: nothing to do

    def test_repeated_activation_and_deactivation_keep_one_consistent_choice(self):
        controller = self.launch()
        for value in (True, False, True, False, True):
            controller.config.data[REMOVE] = value
            controller.changed(object(), _Changes({REMOVE: controller.config.data[REMOVE]}))
        self.assertIs(self.read_choice(), True)
        # No package exists: each ON schedules an install, each OFF finds nothing to remove.
        self.assertEqual(controller.scheduled, [True, True, True])

    # Legacy profiles
    def test_legacy_true_without_choice_never_enables(self):
        with open(self.profile, 'wb') as stream:
            stream.write(json.dumps({REMOVE: True, 'enabled': True}).encode('utf-8'))
        controller = self.launch()
        self.assertIs(controller.config.data[REMOVE], False)
        self.assertEqual(controller.scheduled, [])
        self.assertIsNone(self.read_choice())

    def test_legacy_profile_is_not_rewritten_by_migration(self):
        with open(self.profile, 'wb') as stream:
            stream.write(json.dumps({REMOVE: True, 'enabled': True}).encode('utf-8'))
        before = open(self.profile, 'rb').read()
        self.launch()
        self.assertEqual(open(self.profile, 'rb').read(), before)

    def test_legacy_owned_package_converges_to_off_and_is_never_reinstalled(self):
        # Known limitation (see the readiness report): a legacy owned package stays in place until the user changes
        # the option; the launch path never removes or installs it automatically.
        self.write_package()
        with open(self.profile, 'wb') as stream:
            stream.write(json.dumps({'enabled': True}).encode('utf-8'))
        self.assertEqual(self.launch().scheduled, [False])  # converge to OFF
        self.assertEqual(self.launch().scheduled, [False])  # helper not run in this test: still converging
        os.remove(self.package)  # what the helper does after the game closes
        self.assertEqual(self.launch().scheduled, [])  # nothing reinstalled

    # Failure handling
    def test_unreadable_choice_is_treated_as_not_chosen(self):
        if not os.path.isdir(self.cache):
            os.makedirs(self.cache)
        with open(os.path.join(self.cache, 'choice.json'), 'wb') as stream:
            stream.write(b'{broken')
        controller = self.launch()
        self.assertIs(controller.config.data[REMOVE], False)
        self.assertEqual(controller.scheduled, [])

    def test_choice_with_non_boolean_value_is_ignored(self):
        if not os.path.isdir(self.cache):
            os.makedirs(self.cache)
        with open(os.path.join(self.cache, 'choice.json'), 'wb') as stream:
            stream.write(b'{"removeFog": "yes"}')
        self.assertIsNone(self.read_choice())

    def test_choice_write_is_atomic_and_replaces_the_previous_choice(self):
        self.api['write_choice'](self.cache, True)
        self.api['write_choice'](self.cache, False)
        self.assertIs(self.read_choice(), False)
        self.assertFalse(os.path.exists(os.path.join(self.cache, 'choice.json.tmp')))

    # Third-party files are never part of the choice
    def test_foreign_package_at_the_target_is_not_removed_or_claimed(self):
        with zipfile.ZipFile(self.package, 'w') as archive:
            archive.writestr('meta.xml', '<root><id>someone.else</id></root>')
        with open(self.profile, 'wb') as stream:
            stream.write(json.dumps({'enabled': True}).encode('utf-8'))
        controller = self.launch()
        self.assertEqual(controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))


    # Effective state agrees with the displayed setting
    def test_effective_state_matches_the_setting_on_fresh_install(self):
        controller = self.launch()
        self.assertEqual(controller.effective_state(), 'off')

    def test_effective_state_reports_a_legacy_package_still_loaded_until_restart(self):
        self.write_package()
        controller = self.controller()
        controller.prepare(self.profile)
        self.assertIs(controller.config.data[REMOVE], False)
        self.assertEqual(controller.effective_state(), 'off-package-loaded')

    def test_effective_state_on_requires_the_package(self):
        self.api['write_choice'](self.cache, True)
        controller = self.controller(True)
        controller.prepare(self.profile)
        self.assertEqual(controller.effective_state(), 'on-package-missing')
        self.write_package()
        self.assertEqual(controller.effective_state(), 'on')


if __name__ == '__main__':
    import unittest
    unittest.main()
