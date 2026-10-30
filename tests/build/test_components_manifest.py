import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.components import normalize_asset, normalize_component, read_components


class ComponentManifestTests(unittest.TestCase):
    def read(self, components, schema_version=2):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / 'components.json'
        path.write_text(json.dumps(dict(schema_version=schema_version, components=components)), encoding='utf-8')
        return read_components(temp.name, 'components.json')

    def test_string_assets_are_packaged_without_the_source_prefix(self):
        self.assertEqual(normalize_asset('mod/res/gui/example/**'),
                         dict(source='mod/res/gui/example/**', target='res/gui/example/**', generator=None))
        self.assertEqual(normalize_asset(dict(source='build/flash/a.swf', target='res/gui/flash/a.swf', generator='flash')),
                         dict(source='build/flash/a.swf', target='res/gui/flash/a.swf', generator='flash'))

    def test_assets_outside_mod_require_an_explicit_target(self):
        self.assertEqual(normalize_asset(dict(source='licence', target='licence'))['target'], 'licence')
        for asset in ('licence', dict(source='build/a.swf', generator='flash'), dict(source='mod/a', extra=1), 1):
            with self.assertRaises(ValueError):
                normalize_asset(asset)

    def test_feature_defaults_and_shared_modules(self):
        self.assertEqual(normalize_component(dict(entrypoint='battle.example')),
                         dict(kind='feature', enabled=True, entrypoint='battle.example', config_files=[], assets=[]))
        self.assertEqual(normalize_component(dict(kind='shared'))['entrypoint'], None)
        for item in (dict(), dict(entrypoint='battle.example', unknown=True), dict(entrypoint='battle.example', assets='x')):
            with self.assertRaises(ValueError):
                normalize_component(item)

    def test_reader_expands_the_compact_manifest(self):
        manifests = self.read({'example': {'entrypoint': 'battle.example', 'enabled': False,
                                           'assets': ['mod/res/example.json']}})
        self.assertEqual(manifests, [dict(schema_version=1, id='example', kind='feature', enabled=False,
                                          entrypoint='battle.example', config_files=[],
                                          assets=[dict(source='mod/res/example.json', target='res/example.json', generator=None)])])

    def test_reader_rejects_the_previous_schema_and_names_the_component(self):
        with self.assertRaisesRegex(ValueError, 'schema'):
            self.read({'example': {'entrypoint': 'battle.example'}}, schema_version=1)
        with self.assertRaisesRegex(ValueError, 'example: Feature component requires an entrypoint'):
            self.read({'example': {}})

    def test_repository_manifest_uses_the_compact_form(self):
        document = json.loads((ROOT / 'build_data/components.json').read_text(encoding='utf-8'))
        for name, item in document['components'].items():
            self.assertNotEqual(item.get('kind'), 'feature', name)
            self.assertNotIn(True, (item.get('enabled'),), name)
            self.assertNotEqual(item.get('config_files'), [], name)
            self.assertNotEqual(item.get('assets'), [], name)
            for asset in item.get('assets', []):
                if isinstance(asset, dict):
                    self.assertNotIn('generator', [key for key, value in asset.items() if value is None], name)
                    self.assertFalse(asset.get('generator') is None and asset['source'].startswith('mod/')
                                     and asset.get('target') in (None, asset['source'][4:]), name)


if __name__ == '__main__':
    unittest.main()
