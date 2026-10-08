"""SAFE boundaries and fail-closed release behavior; no tool/network/game access."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'build_tools'))
import obfuscate_staging as safe
import build_safe_beta as beta
import build_lab


class SafeProtectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build/obfuscation')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_rejects_globs_traversal_hooks_conflicts_and_disabled_profiles(self):
        config = json.loads((ROOT / 'build_data/obfuscation.json').read_text())
        path = self.folder / 'profile.json'
        for changes in ({'include': ['Driftkings/**/*.pyc']}, {'include': ['../source/file.pyc']},
                        {'include': ['Driftkings/core/hooks.pyc']}, {'enabled': False},
                        {'exclude': ['Driftkings/core/']}, {'include': config['include'] * 2}):
            path.write_text(json.dumps(dict(config, **changes)))
            with self.subTest(changes=changes), self.assertRaises(ValueError): safe.load_profile(path)

    def test_candidate_sources_have_no_unreviewed_introspection(self):
        for module in safe.SAFE:
            self.assertEqual(safe.source_audit(module)['introspectionHits'], [])

    def test_package_rejects_missing_protection_and_non_python_asset_changes(self):
        clean, output = self.folder / 'clean.wotmod', self.folder / 'output.wotmod'
        name = 'Driftkings/core/marks_calculator.pyc'
        staging = self.folder / 'staging'
        target = staging / name
        target.parent.mkdir(parents=True)
        target.write_bytes(b'\x03\xf3\x0d\x0a' + b'protected')
        def write(path, module, asset):
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('meta.xml', '<root><version>0.1.2-beta.1</version></root>')
                archive.writestr('res/scripts/client/' + name, module)
                archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc', b'\x03\xf3\x0d\x0a' + b'entry')
                archive.writestr('res/example.js', asset)
        write(clean, b'\x03\xf3\x0d\x0a' + b'clean', b'asset')
        for module, asset in ((b'\x03\xf3\x0d\x0a' + b'clean', b'asset'), (target.read_bytes(), b'changed')):
            write(output, module, asset)
            with self.assertRaises(ValueError): beta.validate_package(clean, output, staging, {'include': [name]})
        write(output, target.read_bytes(), b'asset')
        self.assertEqual(beta.validate_package(clean, output, staging, {'include': [name]})['changed'], ['res/scripts/client/' + name])

    def test_release_tool_failure_removes_previous_beta_without_clear_fallback(self):
        folder, output = self.folder / 'safe', self.folder / 'beta'
        output.mkdir()
        fixture_root = self.folder / 'root'
        (fixture_root / 'build/obfuscation').mkdir(parents=True)
        shutil_source = fixture_root / 'build/unified/Driftkings.wotmod'
        shutil_source.parent.mkdir(parents=True)
        shutil_source.write_bytes(b'baseline')
        (fixture_root / 'build_data').mkdir()
        (fixture_root / 'build_data/obfuscation.json').write_bytes((ROOT / 'build_data/obfuscation.json').read_bytes())
        for name in ('Driftkings.wotmod', 'release.json', 'Driftkings.wotmod.sha256'): (output / name).write_bytes(b'stale')
        with patch.object(beta, 'FOLDER', folder), patch.object(beta, 'BETA', output), \
                patch.object(beta, 'ROOT', fixture_root), patch.object(beta, 'protect', side_effect=RuntimeError('tool failed')):
            with self.assertRaises(RuntimeError): beta.run('unused-hg', 'unused-tool', 'unused-python')
        self.assertFalse(shutil_source.exists())
        self.assertFalse(any(output.iterdir()))
        self.assertEqual(json.loads((fixture_root / 'build/obfuscation/report.json').read_text())['status'], 'failed')

    def test_debug_and_explicit_diagnostic_skip_tool_but_release_requires_it(self):
        folder = self.folder / 'beta'
        hg = self.folder / 'hg.exe'
        hg.touch()
        for flags, protected in (([], False), (['--release', '--no-obfuscation'], False), (['--release'], True)):
            with patch.object(sys, 'argv', ['build_lab.py', '--hg', str(hg)] + flags), \
                    patch.object(build_lab.subprocess, 'check_call') as calls, patch.object(beta, 'BETA', folder):
                build_lab.main()
            self.assertEqual(any('build_tools/build_safe_beta.py' in call.args[0] for call in calls.call_args_list), protected)
