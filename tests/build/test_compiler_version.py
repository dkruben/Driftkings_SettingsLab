"""Build tooling runs on Python 3; client source remains Python 2.7 compatible."""
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.compiler import select_version, sync_release_version, sync_source_version, version_contract


class SourceVersionTests(unittest.TestCase):
    def test_json_is_authoritative_and_cli_override_remains_available(self):
        contract = version_contract()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'version.py').write_text("VERSION = '0.1.2-beta.5'\n", encoding='utf-8')
            release = dict(version_source='version.py', version='0.1.2', channel='stable')
            with patch('build_tools.compiler.version_contract', return_value=contract):
                self.assertEqual(select_version(root, release, None, 'auto'),
                                 ('0.1.2', 'stable', '0.1.2-beta.5'))
                self.assertEqual(select_version(root, release, '0.1.3-beta.1', 'beta')[:2],
                                 ('0.1.3-beta.1', 'beta'))
                release['channel'] = 'beta'
                with self.assertRaises(ValueError):
                    select_version(root, release, None, 'auto')

    def test_cli_version_persists_in_json_and_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'version.py').write_text("VERSION = '0.1.2-beta.5'\n", encoding='utf-8')
            release = dict(version_source='version.py', version='0.1.2-beta.5', channel='beta')
            sync_release_version(root, release, '0.1.2', 'stable')
            import json
            saved = json.loads((root / 'build_data/release.json').read_text(encoding='utf-8'))
            self.assertEqual((saved['version'], saved['channel']), ('0.1.2', 'stable'))
            self.assertIn("VERSION = '0.1.2'", (root / 'version.py').read_text(encoding='utf-8'))

    def test_sync_preserves_other_code_and_line_endings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'version.py'
            source.write_bytes(b"# coding: utf-8\r\nVERSION = '0.1.2-beta.5'  # runtime\r\nOTHER = 1\r\n")
            sync_source_version(root, {'version_source': 'version.py'}, '0.1.2-beta.6')
            self.assertEqual(source.read_bytes(),
                             b"# coding: utf-8\r\nVERSION = '0.1.2-beta.6'  # runtime\r\nOTHER = 1\r\n")
            stamp = source.stat().st_mtime_ns
            sync_source_version(root, {'version_source': 'version.py'}, '0.1.2-beta.6')
            self.assertEqual(source.stat().st_mtime_ns, stamp)
