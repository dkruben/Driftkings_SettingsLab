import copy
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.settings.loader import SettingsLoader, SettingsData, part_name
from Driftkings.settings.profiles import ProfileSettings
from Driftkings.settings.registry import SettingsRegistry
from Driftkings.settings.store import SettingsStore
from Driftkings.settings.player_panel_store import PlayerPanelStore, FILES as PANEL_FILES
from Driftkings.settings.carousel_store import CarouselStore, FILES as CAROUSEL_FILES


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.loader = SettingsLoader(str(self.root))

    def write(self, path, value):
        SettingsStore(str(self.root / path)).write(value)

    def test_defaults_and_central_migration_only_once(self):
        old = {'version': 1, 'components': {'OwnHealth': {'enabled': False, 'custom': 'José'}}}
        self.write('Driftkings.json', old)
        legacy = Mock(return_value={'enabled': True})
        defaults = {'enabled': True, 'x': 0}
        result = self.loader.load('OwnHealth', defaults, legacy)
        self.assertEqual(result, {'enabled': False, 'x': 0, 'custom': 'José'})
        legacy.assert_not_called()
        self.assertEqual(json.loads((self.root/'load.json').read_text()), {'loadConfig': 'default'})
        self.write('Driftkings.json', {'version': 1, 'components': {}})
        self.assertEqual(self.loader.load('OwnHealth', defaults, legacy), result)
        self.assertEqual(defaults, {'enabled': True, 'x': 0})

    def test_old_individual_file_and_partial_saves(self):
        legacy = Mock(return_value={'color': '#123456', 'text': '{{c:r}}'})
        self.loader.load('MainGun', {'enabled': True, 'color': '#FFFFFF'}, legacy)
        self.loader.save('MainGun', {'enabled': False})
        data = json.loads((self.root/'default/main_gun.json').read_text())
        self.assertEqual(data, {'enabled': False, 'color': '#123456', 'text': '{{c:r}}'})
        legacy.assert_called_once()
        self.assertTrue((self.root/'default/main_gun.json.bak').is_file())

    def test_invalid_json_and_types_preserved(self):
        self.loader.load('OwnHealth', {'enabled': True, 'x': 0})
        path = self.root/'default/own_health.json'
        for text in ('{broken', '[]', '{"enabled": "false"}', '{"x": true}', '{"x": NaN}'):
            path.write_text(text)
            with self.assertRaises(ValueError):
                self.loader.load('OwnHealth', {'enabled': True, 'x': 0})
            self.assertEqual(path.read_text(), text)

    def test_other_profiles_use_defaults_and_session_stays_pinned(self):
        self.loader.load('OwnHealth', {'enabled': True}, lambda: {'enabled': False})
        (self.root/'fresh').mkdir()
        self.assertTrue(self.loader.select('fresh'))
        self.loader.save('OwnHealth', {'enabled': True})
        self.assertFalse((self.root/'fresh/own_health.json').exists())
        restarted = SettingsLoader(str(self.root))
        legacy = Mock(return_value={'enabled': False})
        self.assertEqual(restarted.load('OwnHealth', {'enabled': True}, legacy), {'enabled': True})
        legacy.assert_not_called()

    def test_clone_and_registry_dropdown(self):
        self.loader.load('OwnHealth', {'enabled': True})
        self.loader.settings.register(types.SimpleNamespace(ID='OwnHealth', data={}))
        page = ProfileSettings(self.loader)
        registry = SettingsRegistry()
        registry.register(page)
        values = registry.describe('Driftkings')['values']
        values['newProfile'] = 'custom'
        result = registry.apply('Driftkings', values)
        self.assertEqual(self.loader.selected(), 'custom')
        self.assertEqual(self.loader.active, 'default')
        self.assertEqual(result['values']['newProfile'], '')
        self.assertEqual(page.names[result['values']['profile']], 'custom')
        self.assertTrue((self.root/'custom/own_health.json').exists())
        registry.apply('Driftkings', dict(result['values'], profile=page.names.index('default')))
        self.assertEqual(self.loader.selected(), 'default')
        with self.assertRaises(ValueError): self.loader.clone('custom')

    def test_unsafe_profile_names_and_invalid_selector(self):
        for name in ('../outside', 'a/b', 'a\\b', '', '.', 'name\n', 'CON', 'LPT1'):
            with self.assertRaises(ValueError): self.loader.directory(name)
        with self.assertRaises(ValueError): part_name('OwnHealth\n')
        self.write('load.json', {'loadConfig': '../outside'})
        with self.assertRaises(ValueError): self.loader.load('OwnHealth', {})
        self.assertFalse((self.root/'default').exists())

    def test_shared_facade_tracks_replaced_dictionary(self):
        config = types.SimpleNamespace(ID='OwnHealth', data={'x': 1})
        shared = SettingsData()
        shared.register(config)
        self.assertIs(shared.own_health, config.data)
        config.data = {'x': 2}
        self.assertEqual(shared.own_health['x'], 2)

    def test_split_migration_preserves_macros_scales_and_empty_fields(self):
        for component, factory, files in (('PlayerPanelPro', PlayerPanelStore, PANEL_FILES), ('CarouselStats', CarouselStore, CAROUSEL_FILES)):
            legacy = factory(str(self.root/component))
            data = legacy.load()
            if component == 'PlayerPanelPro':
                data['profiles']['large']['textFields'] = {}
                data['tab']['formatLeftNick'] = '{{name}} {{c:r}}'
                data['colorScale'] = 2
            else:
                data['colorRating'] = 2
                data['carousel']['small']['extraFields'] = []
            legacy.save(data)
            snapshots = {p: p.read_bytes() for p in (self.root/component).glob('*.json')}
            migrated = self.loader.split_store(component, factory, files, str(self.root/component))
            self.assertEqual(migrated.load(), data)
            self.assertEqual({p: p.read_bytes() for p in snapshots}, snapshots)
            self.loader.clone('copy_' + component)
            clone = self.root/('copy_' + component)/part_name(component)
            self.assertEqual(factory(str(clone)).load(), data)

    def test_split_migration_recovers_pending_transaction(self):
        legacy = self.root/'PlayerPanelPro'
        old = PlayerPanelStore(str(legacy)).load()
        general = json.loads((legacy/'general.json').read_text())
        self.write('PlayerPanelPro/.transaction.json', {'general.json': general})
        self.write('PlayerPanelPro/general.json', dict(general, rating='eff'))
        new = self.loader.split_store('PlayerPanelPro', PlayerPanelStore, PANEL_FILES, str(legacy))
        self.assertEqual(new.load(), old)
        self.assertTrue((legacy/'.transaction.json').exists())

    def test_invalid_split_migration_never_publishes_partial_profile(self):
        self.write('CarouselStats/carousel.json', {})
        (self.root/'CarouselStats/carouselSmall.json').write_text('{broken')
        with self.assertRaises(ValueError):
            self.loader.split_store('CarouselStats', CarouselStore, CAROUSEL_FILES, str(self.root/'CarouselStats'))
        self.assertFalse((self.root/'default/carousel_stats').exists())
        self.assertEqual(list((self.root/'default').iterdir()), [])


if __name__ == '__main__': unittest.main()
