# -*- coding: utf-8 -*-
"""Toolchain discovery (B1) and production reference snapshot checks.

Shallow repository paths must not fail because a default candidate cannot be formed, explicit overrides must
keep working, and missing defaults must resolve to None without an exception.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import toolchain  # noqa: E402

ANCHOR = Path(tempfile.gettempdir()).anchor or os.sep


class AncestorCandidatesTests(unittest.TestCase):
    def test_deep_root_keeps_the_two_default_candidates(self):
        root = Path(ANCHOR) / 'one' / 'two' / 'three' / 'repo'
        expected = [root.parent / 'Programas/Flex', root.parents[1] / 'Programas/Flex']
        self.assertEqual(toolchain.ancestor_candidates(root, 'Programas/Flex'), expected)

    def test_shallow_root_has_one_candidate_and_does_not_raise(self):
        root = Path(ANCHOR) / 'shallow'
        self.assertEqual(toolchain.ancestor_candidates(root, 'Programas/Flex'), [Path(ANCHOR) / 'Programas/Flex'])

    def test_root_without_ancestors_has_no_candidates(self):
        self.assertEqual(toolchain.ancestor_candidates(Path(ANCHOR), 'Programas/Flex'), [])


class DiscoverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='toolchain-'))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.files = {}
        for key, name in (('python27', 'python.exe'), ('hg', 'hg.exe'), ('mxmlc_jar', 'mxmlc.jar'),
                          ('playerglobal', 'playerglobal.swc'), ('java', 'java.exe'), ('csc', 'csc.exe')):
            path = self.tmp / name
            path.write_bytes(b'x')
            self.files[key] = str(path)
        for key in ('flex_home', 'rabcdasm_home', 'game_root', 'reference_root'):
            path = self.tmp / key
            path.mkdir()
            self.files[key] = str(path)
        self.shallow = Path(ANCHOR) / ('dk-shallow-' + os.path.basename(str(self.tmp)))

    def test_shallow_root_with_full_explicit_overrides_discovers_every_tool(self):
        result = toolchain.discover(self.shallow, dict(self.files))
        for key, value in self.files.items():
            self.assertEqual(os.path.normcase(result[key]), os.path.normcase(str(Path(value).resolve())), key)

    def test_explicit_missing_tool_is_still_rejected(self):
        overrides = dict(self.files, csc=str(self.tmp / 'absent-csc.exe'))
        with self.assertRaises(ValueError) as context:
            toolchain.discover(self.shallow, overrides)
        self.assertIn('Configured tool is missing: csc', str(context.exception))

    def test_missing_default_candidates_resolve_to_none_without_an_exception(self):
        overrides = dict(self.files)
        overrides.pop('flex_home')
        overrides.pop('mxmlc_jar')
        result = toolchain.discover(self.shallow, overrides)
        self.assertIsNone(result['flex_home'])
        self.assertIsNone(result['mxmlc_jar'])

    def test_flex_default_is_found_beside_a_deep_repository(self):
        repo = self.tmp / 'a' / 'Driftkings_SettingsLab'
        repo.mkdir(parents=True)
        flex = self.tmp / 'a' / 'Programas' / 'Flex'
        (flex / 'lib').mkdir(parents=True)
        (flex / 'lib' / 'mxmlc.jar').write_bytes(b'x')
        overrides = dict((k, v) for k, v in self.files.items() if k not in ('flex_home', 'mxmlc_jar'))
        result = toolchain.discover(repo, overrides)
        self.assertEqual(os.path.normcase(result['flex_home']), os.path.normcase(str(flex.resolve())))


class TargetSectionTests(unittest.TestCase):
    """Per-target paths: CLI override > DK_* environment > target section > local default > discovery."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='target-section-'))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop('DK_GAME_ROOT', None)
        self.root = self.tmp / 'repo'
        (self.root / 'build_data').mkdir(parents=True)
        self.base = {}
        for key, name in (('python27', 'python.exe'), ('hg', 'hg.exe'), ('mxmlc_jar', 'mxmlc.jar'),
                          ('playerglobal', 'playerglobal.swc'), ('java', 'java.exe'), ('csc', 'csc.exe')):
            path = self.tmp / name
            path.write_bytes(b'x')
            self.base[key] = str(path)
        for key in ('flex_home', 'rabcdasm_home', 'game_default', 'reference_default', 'game_na', 'reference_na',
                    'game_env'):
            (self.tmp / key).mkdir()
        self.dirs = {key: str((self.tmp / key).resolve()) for key in
                     ('game_default', 'reference_default', 'game_na', 'reference_na', 'game_env')}
        self.write({'game_root': self.dirs['game_default'], 'reference_root': self.dirs['reference_default'],
                    'targets': {'na999': {'game_root': self.dirs['game_na'],
                                          'reference_root': self.dirs['reference_na']}}})
        self.base['flex_home'] = str(self.tmp / 'flex_home')
        self.base['rabcdasm_home'] = str(self.tmp / 'rabcdasm_home')

    def write(self, settings):
        (self.root / 'build_data/toolchain.local.json').write_text(json.dumps(settings), encoding='utf-8')

    def resolved(self, result, key):
        return os.path.normcase(result[key])

    def test_target_section_supplies_its_paths(self):
        result = toolchain.discover(self.root, dict(self.base, target='na999'))
        self.assertEqual(self.resolved(result, 'game_root'), os.path.normcase(self.dirs['game_na']))
        self.assertEqual(self.resolved(result, 'reference_root'), os.path.normcase(self.dirs['reference_na']))

    def test_local_default_applies_without_target_or_for_other_targets(self):
        for overrides in (dict(self.base), dict(self.base, target='ct996')):
            result = toolchain.discover(self.root, overrides)
            self.assertEqual(self.resolved(result, 'game_root'), os.path.normcase(self.dirs['game_default']))

    def test_cli_override_beats_target_section(self):
        result = toolchain.discover(self.root, dict(self.base, target='na999', game_root=self.dirs['game_env']))
        self.assertEqual(self.resolved(result, 'game_root'), os.path.normcase(self.dirs['game_env']))

    def test_environment_beats_target_section(self):
        with patch.dict(os.environ, {'DK_GAME_ROOT': self.dirs['game_env']}):
            result = toolchain.discover(self.root, dict(self.base, target='na999'))
        self.assertEqual(self.resolved(result, 'game_root'), os.path.normcase(self.dirs['game_env']))

    def test_unknown_target_field_is_rejected(self):
        self.write({'targets': {'na999': {'python27': 'x'}}})
        with self.assertRaisesRegex(ValueError, 'Unknown local toolchain field for target na999'):
            toolchain.discover(self.root, dict(self.base, target='na999'))


class ReferenceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='reference-'))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def write_name(self, text):
        (self.tmp / '.version_name').write_bytes(text.encode('utf-8'))

    def test_matching_snapshot_is_accepted(self):
        self.write_name('2.4.2.5523\n')
        self.assertTrue(toolchain.reference_snapshot_matches(self.tmp, '2.4.2.5523'))

    def test_eu_reference_is_refused_for_the_na_pin(self):
        self.write_name('2.4.1.5514')
        self.assertFalse(toolchain.reference_snapshot_matches(self.tmp, '2.4.2.5523'))

    def test_byte_order_mark_is_tolerated(self):
        (self.tmp / '.version_name').write_bytes(b'\xef\xbb\xbf2.4.2.5523')
        self.assertTrue(toolchain.reference_snapshot_matches(self.tmp, '2.4.2.5523'))

    def test_missing_declaration_is_refused(self):
        self.assertFalse(toolchain.reference_snapshot_matches(self.tmp, '2.4.2.5523'))


if __name__ == '__main__':
    unittest.main()
