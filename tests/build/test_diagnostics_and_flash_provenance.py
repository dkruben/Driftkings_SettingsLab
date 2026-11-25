# -*- coding: utf-8 -*-
"""D3: clock diagnostics stay out of production. D1: Flash library provenance manifest is complete and self-consistent.

The binaries themselves are not tracked (redistribution rights unverified), so these tests check the manifest and
lock records and the absence of unrelated binaries, not the SWC bytes.
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.validate_build_data import read_json

CLOCK = 'driftkings/gameface/lobby/clock_diagnostics.py'
CLIENT = ROOT / 'mod/res/scripts/client'
SWC_DIR = ROOT / 'flash_source/shared/swc'
MANIFEST = SWC_DIR / 'manifest.na999.json'
LOCK = ROOT / 'flash_source/vehicle_markers/native-lock.na999.json'
SHA256 = re.compile(r'^[0-9a-f]{64}$')
GUI_PART = re.compile(r'^gui-part[1-4]\.pkg$')


class ClockDiagnosticsExclusionTests(unittest.TestCase):
    def test_build_excludes_the_module_from_the_python_package(self):
        config = read_json(ROOT / 'build_data/build_config.json')
        self.assertIn('driftkings/gameface/lobby/clock_diagnostics.py', config['python']['exclude'])

    def test_no_production_module_imports_the_diagnostic_module(self):
        offenders = []
        for path in sorted(CLIENT.rglob('*.py')):
            if path.name == 'clock_diagnostics.py':
                continue
            text = path.read_text(encoding='utf-8', errors='replace')
            if re.search(r'clock_diagnostics', text):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_installer_and_distribution_tooling_do_not_reference_it(self):
        for relative in ('installer/source/installer.cs', 'installer/setup/wizard.iss', 'build_tools/build_installer.py',
                         'build_tools/publish_release.py', 'build_tools/compiler.py'):
            text = (ROOT / relative).read_text(encoding='utf-8', errors='replace')
            self.assertNotIn('clock_diagnostics', text, relative)

    def test_diagnostic_module_keeps_its_disabled_default(self):
        text = (CLIENT / 'driftkings/gameface/lobby' / 'clock_diagnostics.py').read_text(encoding='utf-8', errors='replace')
        self.assertRegex(text, r'(?m)^ENABLED = False\b')


class FlashProvenanceManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        self.lock = json.loads(LOCK.read_text(encoding='utf-8'))

    def test_manifest_identifies_the_realm_build_and_revision(self):
        self.assertEqual(self.manifest['game_version'], '2.4.2.0')
        self.assertEqual(self.manifest['realm'], 'NA')
        self.assertEqual(self.manifest['build'], '999')
        self.assertEqual(self.manifest['revision'], '2664941')

    def test_manifest_lists_eight_unique_libraries_with_valid_hashes(self):
        libraries = self.manifest['libraries']
        self.assertEqual(len(libraries), 8)
        self.assertEqual(len(set(item['name'] for item in libraries)), 8)
        for item in libraries:
            self.assertRegex(item['sha256'], SHA256, item['name'])
            self.assertRegex(item['library_swf_sha256'], SHA256, item['name'])
            self.assertRegex(item['package'], GUI_PART, item['name'])
            self.assertTrue(item['resource'].startswith('gui/flash/swc/'), item['name'])
            self.assertIs(item['equals_ct'], False, item['name'])

    def test_no_unrelated_binary_is_in_the_swc_folder(self):
        # Two families live here: the NA 2.4.2.0 libraries (na999-*, this manifest) and the CT libraries
        # already tracked since 0.1.7-beta.1 (listed by the CT manifest). Anything else is unrelated.
        listed = set(item['name'] for item in self.manifest['libraries'])
        ct = set(item['name'] for item in read_json(SWC_DIR / 'manifest.json')['libraries'])
        present = set(path.name for path in SWC_DIR.iterdir() if path.is_file())
        na = set(name for name in present if name.startswith('na999-'))
        expected_na = set(listed)  # manifest names already carry the na999- prefix
        self.assertEqual(sorted(na - expected_na), [], 'unlisted NA files')
        # The NA binaries are not tracked (D1). A clean checkout has none of them; a partial set is an error.
        if na:
            self.assertEqual(sorted(expected_na - na), [], 'partial NA library set')
        self.assertEqual(sorted(present - na - ct - {'manifest.json', 'manifest.na999.json'}), [],
                         'unrelated files in the SWC folder')

    def test_native_lock_matches_the_manifest_build(self):
        self.assertEqual(self.lock['gameVersion'], self.manifest['game_version'])
        self.assertEqual(self.lock['realm'], self.manifest['realm'])
        self.assertEqual(self.lock['clientBuild'], self.manifest['build'])
        self.assertEqual(self.lock['clientRevision'], self.manifest['revision'])
        self.assertRegex(self.lock['sha256'], SHA256)
        self.assertRegex(self.lock['package'], GUI_PART)


if __name__ == '__main__':
    unittest.main()
