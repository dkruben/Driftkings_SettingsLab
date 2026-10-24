# -*- coding: utf-8 -*-
"""Fresh profiles use current files without importing or deleting older layouts."""
import os
import shutil
import tempfile

from support import RuntimeTest, module


class CurrentSettingsTests(RuntimeTest):
    def setUp(self):
        super(CurrentSettingsTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.store = self.load('settings.store').SettingsStore
        self.defaults = self.load('settings.default_values').DEFAULTS
        self.loader = self.load('settings.loader').SettingsLoader(
            self.root, settings=module(configs=self.defaults))

    def write(self, relative, value):
        path = os.path.join(self.root, relative)
        self.store(path).write(value)
        return path

    def test_old_central_and_component_files_are_not_imported_or_deleted(self):
        central = self.write('driftkings.json', {'version': 1, 'components': {
            'clan_reward_collection': {'enabled': False}}})
        old = self.write('default/auto_claim_clan.json', {'enabled': False})
        removed = self.write('default/safe_shot.json', {})
        self.assertEqual(self.loader.load('clan_reward_collection', self.defaults['clan_reward_collection']),
                         self.defaults['clan_reward_collection'])
        for path in (central, old, removed):
            self.assertTrue(os.path.isfile(path))

    def test_hangar_clock_options_do_not_change_main_defaults(self):
        self.write('default/hangar_preferences.json', {
            'enabled': False, 'clock': False, 'clockX': 999, 'customClockText': 'old'})
        self.assertEqual(self.loader.load('main', self.defaults['main']), self.defaults['main'])

    def test_current_profile_can_be_cloned_and_selected_without_cross_imports(self):
        defaults = self.defaults['main']
        self.loader.load('main', defaults)
        self.loader.save('main', {'clock': {'enabled': False}})
        self.loader.clone('personal')
        self.assertEqual(self.loader.profiles(), ['default', 'personal'])
        self.assertTrue(self.loader.select('personal'))
        self.assertEqual(self.loader.active, 'default')
        restarted = type(self.loader)(self.root, settings=module(configs=self.defaults))
        self.assertFalse(restarted.load('main', defaults)['clock']['enabled'])
        restarted.save('main', {'clock': {'enabled': True}})
        self.assertFalse(self.loader.load('main', defaults)['clock']['enabled'])

    def test_split_stores_use_current_folders_only(self):
        self.write('default/carousel_stats/carousel.json', {'enabled': False})
        self.write('default/player_panel_pro/general.json', {'schemaVersion': 1})
        self.write('default/minimap_enhancements.json', {'enabled': False})
        carousel = self.load('settings.vehicle_carousel_store').CarouselStore
        panels = self.load('settings.team_panel_store').PlayerPanelStore
        self.assertEqual(self.loader.split_store('vehicle_carousel', carousel).load(),
                         self.defaults['vehicle_carousel'])
        self.assertEqual(self.loader.split_store('team_panels', panels).load(), self.defaults['team_panels'])
        self.assertEqual(self.loader.load('minimap_enhancements', self.defaults['minimap_enhancements']),
                         self.defaults['minimap_enhancements'])

    def test_old_panel_schema_is_rejected_without_converting_or_backing_up(self):
        path = self.write('default/team_panels/general.json', {'schemaVersion': 1})
        panels = self.load('settings.team_panel_store').PlayerPanelStore
        with self.assertRaises(ValueError):
            self.loader.split_store('team_panels', panels).load()
        self.assertFalse(os.path.exists(path + '.v1'))
        self.assertEqual(self.load('settings.store').read_object(path), {'schemaVersion': 1})

    def test_caches_start_empty_and_preserve_current_entries(self):
        self.write('Stats/cache/wn8exp.json', {'old': True})
        cache = self.load('core.cache').CacheDirectories(self.root)
        folder = cache.directory('stats')
        self.assertEqual(os.listdir(folder), [])
        path = self.write('cache/stats/wn8exp.json', {'current': True})
        self.assertEqual(cache.directory('stats'), folder)
        self.assertEqual(self.load('settings.store').read_object(path), {'current': True})
