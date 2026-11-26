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


class CompilerModeTests(unittest.TestCase):
    def test_dev_plan_is_read_only_and_uses_a_package_only_override(self):
        import contextlib
        import io
        import json
        from build_tools import compiler

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'build_data').mkdir()
            source = root / 'version.py'
            source.write_bytes(b"VERSION = '0.1.7'\r\n")
            manifest = root / 'build_data/release.json'
            manifest.write_text(json.dumps(dict(version_source='version.py', version='0.1.7', channel='stable')))
            (root / 'build_data/build_config.json').write_text(json.dumps(dict(
                package=dict(release_root='build/releases', debug_root='build/debug'))))
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            plan = {'python': [], 'assets': [], 'defaults': []}
            target = dict(name='ct996', identity=dict(realm='CT', build='996'), profile=None, reference_hashes={})
            with (patch.object(compiler, 'ROOT', root),
                  patch.object(compiler, 'check_release_identity'),
                  patch.object(compiler, 'version_contract', return_value=version_contract()),
                  patch.object(compiler, 'discover', return_value={'game_root': 'fixture'}),
                  patch.object(compiler, 'resolve_target', return_value=target) as resolve,
                  patch.object(compiler, 'build_plan', return_value=plan),
                  patch.object(compiler, 'run_worker') as worker,
                  contextlib.redirect_stdout(io.StringIO()) as output):
                args = compiler.argument_parser().parse_args(
                    ['--mode', 'dev', '--target', 'ct996', '--version', '0.1.8-beta.1', '--plan'])
                compiler.build(args)
                resolve.assert_called_once()
                worker.assert_not_called()
            preview = json.loads(output.getvalue())
            self.assertEqual(preview['target'], 'ct996')
            self.assertEqual(preview['version'], '0.1.8-beta.1')
            self.assertEqual(preview['source_version'], '0.1.7')
            self.assertFalse((root / 'build').exists())
            self.assertEqual({p: p.read_bytes() for p in root.rglob('*') if p.is_file()}, before)

            config = dict(python=dict(source_root='.', archive_root='res/scripts/client',
                                      component_list='component_list.py'))
            with patch.object(compiler, 'render_defaults', return_value='defaults'):
                overrides = compiler.python_overrides(root, config, json.loads(manifest.read_text()),
                                                       preview['version'], [])
            self.assertIn("VERSION = '0.1.8-beta.1'", overrides['res/scripts/client/version.pyc'])
            self.assertEqual(source.read_bytes(), before[source])
            self.assertEqual(manifest.read_bytes(), before[manifest])

    def test_release_rejects_overrides_and_inconsistent_metadata_before_tool_discovery(self):
        from build_tools import compiler

        for requested, source, error in (
                ('0.1.8', '0.1.7', 'only allowed in development'),
                (None, '0.1.6', 'source VERSION disagree')):
            with (self.subTest(requested=requested, source=source),
                  patch.object(compiler, 'read_json', return_value={'version': '0.1.7'}),
                  patch.object(compiler, 'check_release_identity'),
                  patch.object(compiler, 'select_version', return_value=(requested or '0.1.7', 'stable', source)),
                  patch.object(compiler, 'discover') as discover):
                flags = ['--mode', 'release', '--plan']
                if requested:
                    flags += ['--version', requested]
                with self.assertRaisesRegex(ValueError, error):
                    compiler.build(compiler.argument_parser().parse_args(flags))
                discover.assert_not_called()
