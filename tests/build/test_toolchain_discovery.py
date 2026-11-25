# -*- coding: utf-8 -*-
"""Toolchain discovery (B1) and production reference snapshot checks.

Shallow repository paths must not fail because a default candidate cannot be formed, explicit overrides must
keep working, and missing defaults must resolve to None without an exception.
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

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
