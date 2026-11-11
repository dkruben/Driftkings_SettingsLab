"""Native crew transport and protected consumer contracts."""
import io
import json
import unittest

from build_tools import generate_ui_catalog as catalog
from build_tools.validate_build_data import build_plan
from support.baselines import PATH, baseline, changed_catalog_entries, json_hash, normalized_ast, protected_file, text_hash

# Content baseline recorded from commit fa8c6990 (native hangar marks plugin).
BASE = baseline('native_marks')


class NativeCrewCatalogTests(unittest.TestCase):
    def test_three_distinct_identities_and_only_crew_changes_transport(self):
        data = catalog.read_catalog()['GAMEFACE']
        self.assertEqual(changed_catalog_entries('native_marks', data), ['DriftkingsCrewProgression', 'driftkingsbattleEfficiency', 'DriftkingsCarouselStats'])
        names = ('DriftkingsHangarClock', 'DriftkingsMarksOnGunHangar', 'DriftkingsCrewProgression')
        native = [data[name] for name in names]
        self.assertTrue(all(x.get('transport') == 'native_user_missions' for x in native))
        urls = [x['plugin'] for x in native]
        identities = [(url.split('mono/')[1] if 'mono/' in url else '') or 'unknown' for url in urls]
        self.assertEqual(identities, ['unknown', 'driftkings/hangar_marks/marks_plugin.js',
                                      'driftkings/crew_progression/crew_plugin.js'])
        self.assertEqual(len(set(urls)), 3)
        self.assertEqual(len(set(x['resource'] for x in native)), 3)
        target = catalog.asset_target(native[-1]['plugin'])
        self.assertIn(target, {item['target'] for item in build_plan(catalog.ROOT)['assets']})
        self.assertTrue((catalog.ROOT / 'mod' / target).is_file())
        block = catalog.outputs()[catalog.BOOTSTRAP].split(catalog.START)[1].split(catalog.END)[0]
        for name in names:
            self.assertNotIn(name, block)
        legacy = [name for name, spec in data.items() if spec['owner'] is not None
                  and spec.get('transport', 'openwg') == 'openwg']
        self.assertEqual(len(legacy), 15)
        for name in legacy:
            self.assertIn(name, block)

    def test_calculations_patches_and_existing_integrations_preserved(self):
        paths = [
            'mod/res/scripts/client/driftkings/lobby/crew_management.py',
            'mod/res/scripts/client/driftkings/lobby/crew_progression.py',
            'mod/res/scripts/client/driftkings/core/crew_progression.py',
            'mod/res/scripts/client/driftkings/views/crew_progression_model.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/crew_details.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/common.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/main.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/hangar_marks_of_excellence.py',
            'mod/res/gui/gameface/mods/driftkings/main/clock_plugin.js',
            'mod/res/gui/gameface/mods/driftkings/mono/driftkings/hangar_marks/marks_plugin.js',
            'mod/res/gui/gameface/mods/driftkings/crew_progression/model.html',
            'build_data/patches/carousel_2.4.2_ct.json', 'build_data/patches/crew_tooltip_2.4.2_ct.json',
            'build_data/build_config.json']
        for path in paths:
            if path == 'build_data/build_config.json':
                current = json.loads((catalog.ROOT / path).read_text())
                self.assertEqual(current['generators'].pop('battleinfo_native')['kind'], 'native_battleinfo_patch')
                self.assertEqual(json_hash(current), BASE['build_config'])
                continue
            self.assertIn(protected_file(BASE, path), ('historical', 'format_only'), path)

    def test_format_only_revision_still_detects_functional_changes(self):
        path = 'mod/res/scripts/client/driftkings/gameface/lobby/hangar_marks_of_excellence.py'
        with io.open(PATH, encoding='utf-8') as stream:
            revision = json.load(stream)['format_only_revisions'][path]
        historical = revision['historical_source'].encode('utf-8')
        current = (catalog.ROOT / path).read_bytes().replace(b'\r\n', b'\n')
        # Provenance: the stored source is byte-for-byte the baseline commit's file.
        self.assertEqual(text_hash(historical), BASE['files'][path])
        self.assertEqual(protected_file(BASE, path, historical), 'historical')
        self.assertEqual(protected_file(BASE, path), 'format_only')
        self.assertNotEqual(historical, current)
        self.assertEqual(normalized_ast(historical), normalized_ast(current))
        anchor = b'    from gui.impl.pub.view_component import ViewComponent\n'
        self.assertEqual(current.count(anchor), 1)
        mutations = {
            'added statement': current.replace(anchor, anchor + b'    ViewComponent.driftkings_marker = True\n'),
            'removed import': current.replace(anchor, b''),
            'changed import target': current.replace(anchor, anchor.replace(b'view_component', b'view_impl')),
            'added import': current.replace(anchor, anchor + b'    import os\n'),
            'changed literal': current.replace(b'True', b'False', 1),
            'import moved after code': current.replace(anchor, b'').replace(b'\n    from driftkings.core.hooks import override\n',
                                                                         b'\n    from driftkings.core.hooks import override\n    override = override\n' + anchor),
        }
        for label, mutated in mutations.items():
            with self.subTest(change=label):
                self.assertNotEqual(mutated, current)
                with self.assertRaisesRegex(AssertionError, 'functional change'):
                    protected_file(BASE, path, mutated)
        # Format-only but unrecorded content (a comment) is still rejected: the exact revised hash is pinned.
        with self.assertRaisesRegex(AssertionError, 'recorded format-only revision'):
            protected_file(BASE, path, current + b'# unrecorded comment\n')
        # A file without a recorded revision keeps the exact historical hash contract.
        other = 'mod/res/scripts/client/driftkings/gameface/lobby/main.py'
        content = (catalog.ROOT / other).read_bytes()
        self.assertEqual(protected_file(BASE, other, content), 'historical')
        with self.assertRaisesRegex(AssertionError, 'no recorded format-only revision'):
            protected_file(BASE, other, content + b'\n')
