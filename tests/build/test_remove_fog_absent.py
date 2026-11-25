# -*- coding: utf-8 -*-
"""Remove Fog is excluded from production: no packaging, runtime, setting, string or default remains."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding='utf-8-sig', errors='replace')


class RemoveFogAbsentTests(unittest.TestCase):
    def test_build_has_no_fog_helper_generator_or_component_asset(self):
        config = json.loads(read('build_data/build_config.json'))
        self.assertNotIn('fog_package_helper', config['generators'])
        components = json.loads(read('build_data/components.json'))['components']
        for name, manifest in components.items():
            for asset in manifest.get('assets', []):
                target = asset['target'] if isinstance(asset, dict) else asset
                self.assertNotIn('fog', target.lower(), name)

    def test_runtime_controller_and_helper_source_are_removed(self):
        self.assertFalse((ROOT / 'mod/res/scripts/client/driftkings/core/fog_package.py').exists())
        self.assertFalse((ROOT / 'installer/source/fogpackage.cs').exists())

    def test_no_runtime_reference_to_the_fog_controller(self):
        for path in (ROOT / 'mod/res/scripts/client').rglob('*.py'):
            text = path.read_text(encoding='utf-8', errors='replace')
            self.assertNotIn('fog_package', text, str(path))
            self.assertNotIn('REMOVE_FOG', text, str(path))
            self.assertNotIn('coordinated_restart', text, str(path))

    def test_setting_default_and_strings_are_removed(self):
        self.assertNotIn('removeFog', read('mod/res/scripts/client/driftkings/settings/default_values.py'))
        self.assertNotIn('removeFog', read('mod/res/scripts/client/driftkings/settings/settings_data.py'))
        self.assertNotIn('removeFog', read('mod/res/scripts/client/driftkings/settings/definitions/battle/battle_preferences.py'))
        self.assertNotIn('removeFog', json.loads(read('res/configs/driftkings/default/battle_preferences.json')))
        for path in (ROOT / 'mod/res/mods/driftkings/text').glob('*.yml'):
            text = path.read_text(encoding='utf-8', errors='replace')
            self.assertNotIn('UI_fog_', text, path.name)
            self.assertNotIn('UI_setting_removeFog_', text, path.name)

    def test_changelog_no_longer_mentions_remove_fog(self):
        changelog = json.loads(read('build_data/release.json'))['changelog']
        self.assertFalse(any('fog' in item.lower() for item in changelog))


if __name__ == '__main__':
    unittest.main()
