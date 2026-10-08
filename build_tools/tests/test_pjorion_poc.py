"""POC isolation and failure detection; no invocation of the real tool here."""
import configparser
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'build_tools'))
import pjorion_poc as poc
import pjorion_probe


class POCBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def baseline(self):
        path = self.folder / 'baseline.wotmod'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('meta.xml', '<root><version>0.1.1-beta.6</version></root>')
            archive.writestr(poc.MODULE, b'original')
            archive.writestr('res/gui/gameface/example.js', b'unchanged asset')
        return path

    def test_experimental_package_changes_exactly_one_entry_and_keeps_assets(self):
        baseline = self.baseline()
        protected = self.folder / 'protected.pyc'
        protected.write_bytes(b'protected fixture')
        output = self.folder / 'experimental.wotmod'
        report = poc.package(baseline, protected, output)
        self.assertEqual(report['changed'], [poc.MODULE])
        self.assertFalse(report['published'])
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read('res/gui/gameface/example.js'), b'unchanged asset')
        self.assertEqual(report['sha256'], poc.sha(output))

    def test_unchanged_bytecode_cannot_be_accepted_as_protection(self):
        protected = self.folder / 'protected.pyc'
        protected.write_bytes(b'original')
        with self.assertRaises(ValueError):
            poc.package(self.baseline(), protected, self.folder / 'experimental.wotmod')

    def test_probe_cannot_target_source_or_pass_another_file_to_the_tool(self):
        with self.assertRaises(ValueError):
            pjorion_probe.probe('reject', [], ROOT / 'source/scripts/client/Driftkings/core/marks_calculator.py')
        target = pjorion_probe.POC / 'input/marks_calculator.pyc'
        with self.assertRaises(ValueError):
            pjorion_probe.probe('reject', ['--protect-bytecode-file=' + str(ROOT / 'source/anything.pyc'), '/exit'], target)

    def test_tool_failure_or_unchanged_output_remove_stale_artifact_and_report_failure(self):
        tool = self.folder / 'tool-original'
        tool.mkdir()
        (tool / 'DLLs').mkdir()
        for name in poc.TOOL_FILES: (tool / name).write_bytes(b'original tool fixture')
        config = configparser.ConfigParser()
        config.optionxform = str
        for section in ('GENERAL', 'PATHS', 'FILEASSOCIATIONS', 'CONTEXTMENU', 'WOTTRANSMISSION', 'OBFUSCATE', 'PROTECT'):
            config.add_section(section)
        with (tool / 'PjOrion.ini').open('w') as handle: config.write(handle)
        source = self.folder / 'source.py'
        source.write_text('def calculate(): return 1')
        for action in (dict(timeout=True, exitCode=1), dict(timeout=False, exitCode=0)):
            sandbox = self.folder / ('sandbox-' + str(action['exitCode']))
            sandbox.mkdir(exist_ok=True)
            artifact = sandbox / 'Driftkings-PJOrion-POC.wotmod'
            artifact.write_bytes(b'stale previous artifact')
            def compile_fixture(argv, name, **kwargs):
                Path(argv[-1]).write_bytes(b'\x03\xf3\x0d\x0a' + b'input fixture')
            with patch.object(poc, 'POC', sandbox), patch.object(poc, 'SOURCE', source), \
                    patch.object(poc, 'file_version', return_value='1.3.5.501'), \
                    patch.object(poc, 'run_checked', side_effect=compile_fixture), \
                    patch.object(poc, 'probe', return_value=action):
                with self.assertRaises((RuntimeError, ValueError)):
                    poc.run(tool, self.folder / 'python.exe', self.baseline())
            self.assertFalse(artifact.exists())
            report = json.loads((sandbox / 'report.json').read_text())
            self.assertEqual(report['status'], 'failed')
            self.assertTrue(report['failed'])
            self.assertTrue(report['sourceUnchanged'])
            self.assertTrue(report['originalToolUnchanged'])
