"""Regression tests for the binary writer used by AccountManager."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.settings import store as publication

spec = importlib.util.spec_from_file_location('binary_writer', ROOT / 'source/scripts/client/Driftkings/common/utils/filesystem.py')
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)


class BinaryWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'nested' / 'sample.bin'

    def test_create_and_replace_with_client_python27_publication(self):
        with patch.object(publication.os, 'replace', None), patch.object(publication.os, 'name', 'nt'):
            writer.atomicWrite(str(self.path), b'first sample')
            self.assertEqual(self.path.read_bytes(), b'first sample')
            writer.atomicWrite(str(self.path), b'second sample')
        self.assertEqual(self.path.read_bytes(), b'second sample')
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ['sample.bin'])

    def test_failed_publication_restores_old_file(self):
        writer.atomicWrite(str(self.path), b'original')
        rename = os.rename
        def fail_publish(source, target):
            if os.path.basename(source).startswith('.driftkings-'):
                raise OSError('simulated write failure')
            return rename(source, target)
        with patch.object(publication.os, 'replace', None), patch.object(publication.os, 'name', 'nt'):
            with patch.object(publication.os, 'rename', side_effect=fail_publish):
                with self.assertRaises(OSError):
                    writer.atomicWrite(str(self.path), b'replacement')
        self.assertEqual(self.path.read_bytes(), b'original')
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ['sample.bin'])

    def test_interrupted_publication_recovers_previous_file(self):
        writer.atomicWrite(str(self.path), b'original')
        self.path.rename(str(self.path) + '.previous')
        writer.recoverFile(str(self.path))
        self.assertEqual(self.path.read_bytes(), b'original')

    def test_recovery_preserves_already_published_file(self):
        writer.atomicWrite(str(self.path), b'current')
        Path(str(self.path) + '.previous').write_bytes(b'old')
        writer.recoverFile(str(self.path))
        self.assertEqual(self.path.read_bytes(), b'current')


if __name__ == '__main__':
    unittest.main()
