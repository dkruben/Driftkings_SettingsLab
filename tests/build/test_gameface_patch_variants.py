"""Deterministic CT #995/#996 selection for the carousel and crew tooltip Gameface bridges.

These tests never read game bundles: they cover pin selection, identity rejection and
unknown-input refusal. Bundle-level checks run separately in an isolated scratch output.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.validate_build_data import apply_patch_set, ct_client_build, gameface_patch_for_build

CONFIG = json.loads((ROOT / 'build_data/build_config.json').read_text(encoding='utf-8'))
def gameface_spec(resource):
    matches = [spec for spec in CONFIG['generators'].values()
               if spec.get('kind') == 'gameface_patch' and spec.get('resource') == resource]
    assert len(matches) == 1, resource
    return matches[0]


CAROUSEL = gameface_spec('gui/gameface/_dist/production/mono/hangar/main/bundle.js')
TOOLTIP = gameface_spec('gui/gameface/_dist/production/mono/hangar/tooltips/bundle.js')
PINNED_SOURCES = {
    CAROUSEL['resource']: {'995': '7e28391b4c51daa555b04d103a4031f7734b8d0728df03f7b73b47fa781873e5',
                           '996': '81ba2baf167f428204e161e6cc058d657d60ca048cbe687641c6910f4f286250'},
    TOOLTIP['resource']: {'995': 'a7cb133ce2d0495bd8b9cc29794755c55bc6e694f36e6d257b17fc4b6a4967dd',
                          '996': 'd4ebef3be136dac60c31a504de15abb866143e61afb9f4fe3e274791213d857f'},
}
VERSION_XML = ('<root><version>v.2.4.2.0 Common Test #{build}</version>'
               '<meta><client>{revision}</client><realm>CT</realm></meta></root>')


class GamefacePatchVariantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_pinned_variants_match_their_build_identity_and_source_hash(self):
        for spec in (CAROUSEL, TOOLTIP):
            self.assertEqual(set(spec['patch_files']), set(CONFIG['reference']['ct_builds']))
            for build in ('995', '996'):
                patch = gameface_patch_for_build(ROOT, spec, build)
                self.assertEqual(patch['client_build'], build)
                self.assertEqual(patch['resource'], spec['resource'])
                self.assertEqual(patch['source_sha256'], PINNED_SOURCES[spec['resource']][build])

    def test_unknown_build_is_refused_without_fallback(self):
        for spec in (CAROUSEL, TOOLTIP):
            with self.assertRaises(ValueError):
                gameface_patch_for_build(ROOT, spec, '997')

    def test_variant_declaring_another_build_is_refused(self):
        patch = json.loads((ROOT / CAROUSEL['patch_files']['996']).read_text(encoding='utf-8'))
        patch['client_build'] = '995'
        (self.root / 'swapped.json').write_text(json.dumps(patch), encoding='utf-8')
        spec = dict(CAROUSEL, patch_files={'996': 'swapped.json'})
        with self.assertRaises(ValueError):
            gameface_patch_for_build(self.root, spec, '996')

    def test_unknown_input_bytes_are_rejected_by_each_variant(self):
        for spec in (CAROUSEL, TOOLTIP):
            for build in ('995', '996'):
                patch = gameface_patch_for_build(ROOT, spec, build)
                with self.assertRaises(ValueError):
                    apply_patch_set(b'not the pinned bundle', patch)

    def test_installed_ct_build_must_match_pinned_revision(self):
        game = self.root / 'game'
        game.mkdir()
        (game / 'version.xml').write_text(VERSION_XML.format(build=996, revision='2660091'), encoding='utf-8')
        self.assertEqual(ct_client_build(game, CONFIG), ('996', '2660091'))
        (game / 'version.xml').write_text(VERSION_XML.format(build=996, revision='wrong'), encoding='utf-8')
        with self.assertRaises(ValueError):
            ct_client_build(game, CONFIG)
        (game / 'version.xml').write_text(VERSION_XML.format(build=997, revision='2660091'), encoding='utf-8')
        with self.assertRaises(ValueError):
            ct_client_build(game, CONFIG)


if __name__ == '__main__':
    unittest.main()
