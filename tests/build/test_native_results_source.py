"""Source/buffer contracts only: never compile or create a WOTMOD."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile
from build_tools import validate_build_data
from build_tools.generate_ui_catalog import read_catalog, validate
from build_tools.isolated_output import IsolatedOutput
from build_tools.validate_build_data import (JAVASCRIPT_SETUP, apply_battleinfo_patch, apply_patch_set,
                                            battleinfo_parser_pin, build_plan, read_gameface_resource,
                                            require_battleinfo_toolchain)
from support.baselines import baseline, changed_catalog_entries, json_hash
ROOT = Path(__file__).resolve().parents[2]
CT = Path(os.environ.get('DK_CT_SOURCES', str(ROOT.parent / 'Driftkings_WoT_Sources/wot_src_CT')))
SOURCE = CT / 'sources/res/gui/gameface/_dist/production/mono/post_battle/random/bundle.js'
PATCH = ROOT / 'build_data/patches/battle_results_2.4.2_ct.json'


class NativeResultsSourceTests(unittest.TestCase):
    def test_catalog_changes_only_results_and_preserves_four_plugins(self):
        # Content baseline recorded from commit 769c81d1 (native carousel plugin).
        previous = baseline('native_carousel')['catalog']
        current = read_catalog()['GAMEFACE']
        self.assertEqual(changed_catalog_entries('native_carousel', current), ['driftkingsbattleEfficiency'])
        self.assertEqual(json_hash(current['DriftkingsBattleEfficiency']), previous['DriftkingsBattleEfficiency'])
        counts = validate()
        self.assertEqual((counts['native'], counts['injected']), (5, 15))

    def test_package_plan_contains_source_assets_and_exact_target_once(self):
        plan = build_plan(ROOT)
        targets = [x['target'] for x in plan['assets']]
        self.assertEqual(targets.count('res/gui/gameface/_dist/production/mono/post_battle/random/bundle.js'), 1)
        self.assertIn('res/gui/gameface/mods/driftkings/mono/driftkings/battle_results/results_extension.js', targets)
        self.assertFalse(any('node_modules' in n or '/tests/' in n for n in targets))

    @unittest.skipUnless(SOURCE.is_file(), 'Read-only CT fixture not available')
    def test_supported_buffer_is_deterministic_and_hash_pinned(self):
        raw = SOURCE.read_bytes()
        patch = json.loads(PATCH.read_text())
        a = apply_battleinfo_patch(raw, patch)
        self.assertEqual(a, apply_battleinfo_patch(raw, patch))
        self.assertEqual(hashlib.sha256(a).hexdigest(), patch['output_sha256'])
        with self.assertRaises(ValueError):
            apply_battleinfo_patch(raw + b' ', patch)
        with self.assertRaises(ValueError):
            apply_battleinfo_patch(a, patch)

    @unittest.skipUnless(SOURCE.is_file(), 'Read-only CT fixture not available')
    def test_manifest_output_and_runtime_inputs_fail_closed(self):
        raw = SOURCE.read_bytes()
        patch = json.loads(PATCH.read_text())
        patch['output_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            apply_battleinfo_patch(raw, patch)
        patch = json.loads(PATCH.read_text())
        patch['runtime_inputs'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            apply_battleinfo_patch(raw, patch)

    @unittest.skipUnless(SOURCE.is_file(), 'Read-only CT fixture not available')
    def test_patch_subprocess_stays_inside_isolated_output(self):
        # Optional integration: the real AST patcher under an active isolated scope.
        raw = SOURCE.read_bytes()
        patch = json.loads(PATCH.read_text())
        with tempfile.TemporaryDirectory() as temp:
            with IsolatedOutput(Path(temp)):
                output = apply_battleinfo_patch(raw, patch, ROOT)
                self.assertEqual(hashlib.sha256(output).hexdigest(), patch['output_sha256'])
            self.assertFalse(list(Path(temp).rglob('*.wotmod')))
            self.assertEqual([p.name for p in Path(temp).iterdir()], ['build'])

    def toolchain_fixture(self, temp, declared='8.19.0', locked='8.19.0', installed='8.19.0'):
        tools = Path(temp) / 'build_tools/javascript'
        tools.mkdir(parents=True)
        (tools / 'package.json').write_text(json.dumps({'devDependencies': {'acorn': declared}}))
        (tools / 'package-lock.json').write_text(json.dumps({'packages': {'node_modules/acorn': {'version': locked}}}))
        if installed:
            (tools / 'node_modules/acorn').mkdir(parents=True)
            (tools / 'node_modules/acorn/package.json').write_text(json.dumps({'version': installed}))
        return Path(temp)

    def test_node_and_locked_parser_prerequisites_fail_clearly(self):
        patch = json.loads(PATCH.read_text())
        found = lambda name: 'fixture-node'
        setup = 'npm --prefix build_tools/javascript ci --ignore-scripts'
        self.assertEqual(JAVASCRIPT_SETUP, setup)
        battleinfo_parser_pin(ROOT, patch)  # the repository pins the manifest parser version
        with tempfile.TemporaryDirectory() as temp:
            root = self.toolchain_fixture(temp)
            self.assertEqual(require_battleinfo_toolchain(root, patch, found), 'fixture-node')
            with self.assertRaisesRegex(ValueError, 'Node.js was not found on PATH.*' + setup):
                require_battleinfo_toolchain(root, patch, lambda name: None)
        for options, message in ((dict(installed=None), 'acorn is not installed.*' + setup),
                                 (dict(installed='8.0.0'), 'acorn 8.0.0 is installed.*8.19.0 is required.*' + setup),
                                 (dict(locked='8.0.0'), 'not pinned.*package-lock.json: 8.0.0'),
                                 (dict(declared='^8.19.0'), r'not pinned.*package.json: \^8.19.0')):
            with tempfile.TemporaryDirectory() as temp:
                root = self.toolchain_fixture(temp, **options)
                with self.assertRaisesRegex(ValueError, message):
                    require_battleinfo_toolchain(root, patch, found)
        # A missing prerequisite stops before any process is started, from any working directory.
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as elsewhere:
            root = self.toolchain_fixture(temp, installed=None)
            previous = os.getcwd()
            os.chdir(elsewhere)
            try:
                with mock.patch.object(validate_build_data.subprocess, 'run') as run:
                    with self.assertRaisesRegex(ValueError, 'acorn is not installed'):
                        apply_battleinfo_patch(b'fixture', patch, root)
                    run.assert_not_called()
            finally:
                os.chdir(previous)
            self.assertEqual(os.listdir(elsewhere), [])

    def test_legacy_replace_exact_unchanged(self):
        patch = {'source_sha256': hashlib.sha256(b'a').hexdigest(),
                 'output_sha256': hashlib.sha256(b'b').hexdigest(),
                 'operations': [{'find': 'a', 'replace': 'b', 'count': 1}]}
        self.assertEqual(apply_patch_set(b'a', patch), b'b')
        with self.assertRaises(ValueError):
            apply_patch_set(b'aa', patch)

    def test_ambiguous_or_missing_official_resource_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            for name in ('one.pkg', 'two.pkg'):
                with zipfile.ZipFile(Path(temp) / name, 'w') as z:
                    z.writestr('bundle.js', b'fixture')
            with self.assertRaises(ValueError):
                read_gameface_resource(temp, ['one.pkg', 'two.pkg'], 'bundle.js')
            with self.assertRaises(ValueError):
                read_gameface_resource(temp, ['one.pkg'], 'missing.js')
