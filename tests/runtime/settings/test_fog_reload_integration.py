# -*- coding: utf-8 -*-
"""Remove Fog through the real settings path: loader -> service -> signal -> fog controller.

Only the game boundaries are stubbed (client version, resource loading, callbacks). Storage, the loader, the
settings service and its change notifications are the production modules, running on a temporary client folder.
"""
import copy
import json
import os
import shutil
import sys
import tempfile
import types
import zipfile

from support import CLIENT, RuntimeTest, module, source

FOG = 'removeFog'
MASTER = 'enabled'
SECTION = 'battle_preferences'


class _Section(object):
    """What SectionDefinition exposes to the service: a name, live data and the normalization hooks."""
    STORAGE_CLASS = None

    def __init__(self, name, data):
        from driftkings.settings.settings_data import default_keys
        self.NAME = name
        self.data = data
        self.defaultKeys = default_keys(name)
        self.i18n = {}

    def normalize_loaded(self, values):
        return values

    def normalize_changes(self, values, changes):
        return values


class _Listener(object):
    def __init__(self):
        self.calls = []

    def __call__(self, component, changes):
        self.calls.append((component, getattr(changes, 'origin', None), dict(changes)))


class RemoveFogIntegrationTests(RuntimeTest):
    def setUp(self):
        super(RemoveFogIntegrationTests, self).setUp()
        # driftkings.settings is not registered by the base fixture; expose the real package folder.
        package = types.ModuleType('driftkings.settings')
        package.__path__ = [os.path.join(CLIENT, 'settings')]
        sys.modules['driftkings.settings'] = package
        # hotkeys.processHotKeys imports the game's Keys module on every read; no bindings are needed here.
        sys.modules['Keys'] = module()
        self.addCleanup(sys.modules.pop, 'Keys', None)
        self.client = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.client)
        os.makedirs(os.path.join(self.client, 'mods', '2.4.2.0'))
        self.configs = os.path.join(self.client, 'mods', 'configs', 'driftkings')
        os.makedirs(os.path.join(self.configs, 'default'))
        self.package = os.path.join(self.client, 'mods', '2.4.2.0', 'Driftkings.RemoveFog.wotmod')
        self.new_runtime()

    def new_runtime(self):
        """A fresh loader and service: the equivalent of one client session."""
        from driftkings.settings.loader import SettingsLoader
        from driftkings.settings.service import SettingsService
        self.loader = SettingsLoader(self.configs)
        self.service = SettingsService(loader=self.loader)
        self.fog = source('core/fog_package.py', {
            'driftkings.core.updater.installer': module(read_resource=None),
            'driftkings.settings.service': module(settings_service=self.service)})
        self.fog['package_current'] = lambda path, stamp: os.path.isfile(path)
        self.fog['source_stamp'] = lambda root: 'test-stamp'

    # Files and packages
    def profile_file(self, name='default'):
        return os.path.join(self.configs, name, 'battle_preferences.json')

    def write_profile(self, values, name='default'):
        path = self.profile_file(name)
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as stream:
            stream.write(json.dumps(values).encode('utf-8'))

    def read_profile(self, name='default'):
        with open(self.profile_file(name), 'rb') as stream:
            return json.loads(stream.read().decode('utf-8-sig'))

    def write_package(self, path=None, mod_id='driftkings.removefog'):
        target = path or self.package
        with zipfile.ZipFile(target, 'w') as archive:
            archive.writestr('meta.xml', '<root><id>%s</id></root>' % mod_id)

    # Launch and controller wiring, in production order
    def launch(self, listeners=()):
        """Materialize defaults as SectionDefinition does, resolve the preference, connect, then startup."""
        from driftkings.settings.service import restore
        from driftkings.settings.settings_data import defaults
        section = _Section(SECTION, defaults(SECTION))
        restore(section.data, self.service._read(section))
        controller = self.fog['FogPackageController'](section)
        controller.active = True
        controller.root = self.client
        controller.version = '2.4.2.0'
        controller.target = self.package
        controller.scheduled = []
        controller.schedule = lambda desired: controller.scheduled.append(desired)
        controller.prepare(self.loader.path(SECTION))
        self.service.onModSettingsChanged.connect(controller.changed, SECTION, (MASTER, FOG))
        controller.startup()
        for name, listener in listeners:
            self.service.onModSettingsChanged.connect(listener, name, None)
        self.section = section
        self.controller = controller
        return controller

    def reload_section(self, section=None):
        """What opening the settings panel does for every section."""
        return self.service.reload(section or self.section)

    # 1-3: reloads of intact, deleted and key-less files
    def test_reload_with_intact_true_file_schedules_nothing(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.reload_section()
        self.assertEqual(self.controller.scheduled, [])
        self.assertIs(self.section.data[FOG], True)

    def test_reload_after_file_was_deleted_schedules_nothing(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        os.remove(self.profile_file())
        self.reload_section()
        self.assertEqual(self.controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))
        # The loader materialized the default for the file; the controller's intent is unchanged.
        self.assertIs(self.controller.current_intent(), True)

    def test_reload_after_key_was_removed_does_not_order_removal(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.write_profile({MASTER: True})
        self.reload_section()
        self.assertEqual(self.controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))
        self.assertIs(self.controller.current_intent(), True)

    # 4-5: explicit values and the panel opening without interaction
    def test_reload_with_true_value_keeps_preference(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.reload_section()
        self.assertEqual(self.read_profile()[FOG], True)
        self.assertEqual(self.controller.scheduled, [])

    def test_reload_with_false_value_does_not_remove(self):
        self.write_profile({FOG: False, MASTER: True})
        self.write_package()
        self.launch()
        self.reload_section()
        self.assertEqual(self.controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    def test_opening_the_panel_without_interaction_schedules_nothing(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.section.data[FOG] = False  # a stale in-memory value must not matter
        self.reload_section()
        self.assertEqual(self.controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    # 6-7: explicit user changes
    def test_manual_true_to_false_schedules_removal_after_close(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.service.apply(self.section, {FOG: False})
        self.assertEqual(self.controller.scheduled, [False])
        self.assertIs(self.read_profile()[FOG], False)
        self.assertTrue(os.path.isfile(self.package))

    def test_explicit_master_switch_changes_are_applied(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.service.apply(self.section, {MASTER: False})
        self.assertEqual(self.controller.scheduled, [False])

    def test_explicit_master_switch_on_installs_when_missing(self):
        self.write_profile({FOG: True, MASTER: False})
        self.launch()
        self.service.apply(self.section, {MASTER: True})
        self.assertEqual(self.controller.scheduled, [True])

    # 8: profile switching, in session and on the next launch
    def test_profile_switch_in_session_schedules_nothing(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.write_profile({FOG: False, MASTER: True}, name='other')
        self.loader.select('other')
        self.reload_section()
        self.assertEqual(self.controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    def test_next_launch_on_a_false_profile_does_not_remove_the_package(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        self.write_profile({FOG: False, MASTER: True}, name='other')
        self.loader.select('other')
        self.new_runtime()
        self.launch()
        self.assertEqual(self.controller.scheduled, [])
        self.assertTrue(os.path.isfile(self.package))

    # 9: hold
    def test_ambiguous_state_holds_signals_and_writes(self):
        # A file without the key next to a package that is not Driftkings' own is ambiguous (unreadable files
        # and invalid values already fail when the section loads, before any fog code runs).
        self.write_profile({MASTER: True})
        self.write_package(mod_id='someone.else')
        before = open(self.profile_file(), 'rb').read()
        self.launch()
        self.assertTrue(self.controller.hold)
        self.service.onModSettingsChanged.emit(SECTION, self.changes({MASTER: False}))
        self.assertEqual(self.controller.scheduled, [])
        self.assertEqual(open(self.profile_file(), 'rb').read(), before)
        self.assertTrue(os.path.isfile(self.package))

    # 10: other components keep their reload contract
    def test_other_sections_still_receive_reloads_and_defaults(self):
        from driftkings.settings.settings_data import defaults
        listener = _Listener()
        other = _Section('vehicle_health', defaults('vehicle_health'))
        self.service.onModSettingsChanged.connect(listener, 'vehicle_health', None)
        with open(os.path.join(self.configs, 'default', 'vehicle_health.json'), 'wb') as stream:
            stream.write(json.dumps({'enabled': False}).encode('utf-8'))
        self.service.reload(other)
        # Missing keys still come from the defaults, as before; the listener sees the reload as a change.
        self.assertEqual(other.data, dict(defaults('vehicle_health'), enabled=False))
        self.assertEqual([origin for _, origin, _ in listener.calls], ['reload'])

    # 11-12: no unrequested scheduling, realms and clients
    def test_no_unrequested_scheduling_across_a_session(self):
        self.write_profile({FOG: True, MASTER: True})
        self.write_package()
        self.launch()
        for _ in range(3):
            self.reload_section()
        self.write_profile({MASTER: True})
        self.reload_section()
        os.remove(self.profile_file())
        self.reload_section()
        self.assertEqual(self.controller.scheduled, [])

    def test_another_clients_package_is_never_touched(self):
        other_client = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, other_client)
        other_package = os.path.join(other_client, 'Driftkings.RemoveFog.wotmod')
        self.write_package(path=other_package)
        self.write_profile({FOG: False, MASTER: True})
        self.launch()
        self.reload_section()
        self.service.apply(self.section, {FOG: True})
        self.assertTrue(os.path.isfile(other_package))
        self.assertEqual(self.controller.scheduled, [True])

    # Signal contract used above
    def test_reload_emits_an_origin_tag_that_survives_delivery(self):
        listener = _Listener()
        self.write_profile({FOG: True, MASTER: True})
        self.launch(listeners=[(SECTION, listener)])
        os.remove(self.profile_file())
        self.reload_section()
        origins = [origin for _, origin, _ in listener.calls]
        self.assertIn('reload', origins)

    @staticmethod
    def changes(values):
        from driftkings.settings.service import SettingsChanges
        return SettingsChanges(values)
