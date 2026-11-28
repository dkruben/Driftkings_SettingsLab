"""Installer workspace migration: explicit run and artifact selection, run-owned intermediates, candidate freezing.

Temporary fixtures only; no Inno Setup, no game client and no real build.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import build_installer as bi
from build_tools import publication_state as ps

RUN = '20261127T010203Z-abcdef01'
WOTMOD = b'driftkings wotmod bytes'
VERSION = '0.1.8'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


class InstallerRunFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'repo'
        self.root.mkdir()
        self.run = self.root / 'build/runs' / RUN
        write(self.run / 'output/driftkings.wotmod', WOTMOD)
        write(self.run / 'evidence/build-report.json', json.dumps(dict(run_id=RUN, status='success')))
        self.digest = hashlib.sha256(WOTMOD).hexdigest()
        self.candidate = self.run / 'output'
        write(self.candidate / 'release.json', json.dumps(dict(version=VERSION, gameVersion='2.4.2.0', sha256=self.digest)))
        write(self.candidate / 'build-report.json', json.dumps(dict(status='success', mode='release', profile='production', realm='NA', version=VERSION,
                                                                    gameVersion='2.4.2.0', run_id=RUN,
                                                                    artifacts={'driftkings.wotmod': dict(sha256=self.digest)})))
        write(self.candidate / 'SHA256SUMS.txt', '')


class RunSelectionTests(InstallerRunFixture):
    def test_the_build_report_names_the_run_when_no_run_is_given(self):
        self.assertEqual(bi.run_directory(self.candidate, self.root), self.run.resolve())

    def test_an_explicit_run_directory_is_accepted(self):
        self.assertEqual(bi.run_directory(self.candidate, self.root, explicit=self.run), self.run.resolve())

    def test_a_report_without_a_run_needs_an_explicit_run(self):
        write(self.candidate / 'build-report.json', json.dumps(dict(status='success', version=VERSION)))
        with self.assertRaisesRegex(ValueError, 'names no compiler run'):
            bi.run_directory(self.candidate, self.root)

    def test_a_run_outside_build_runs_is_rejected(self):
        outside = self.root / 'elsewhere' / RUN
        write(outside / 'output/driftkings.wotmod', WOTMOD)
        write(outside / 'evidence/build-report.json', json.dumps(dict(run_id=RUN)))
        with self.assertRaisesRegex(ValueError, 'directly under build/runs'):
            bi.run_directory(self.candidate, self.root, explicit=outside)

    def test_run_metadata_must_match_its_directory(self):
        write(self.run / 'evidence/build-report.json', json.dumps(dict(run_id='other')))
        with self.assertRaisesRegex(ValueError, 'Run metadata does not match'):
            bi.run_directory(self.candidate, self.root)

    def test_the_run_wotmod_must_be_the_candidate_package(self):
        write(self.run / 'output/driftkings.wotmod', b'other bytes')
        with self.assertRaisesRegex(ValueError, 'not the candidate package'):
            bi.run_directory(self.candidate, self.root)


class WorkspaceTests(InstallerRunFixture):
    def test_the_workspace_lives_inside_the_run(self):
        layout = bi.installer_workspace(self.run)
        for folder in layout.values():
            self.assertTrue(folder.is_dir())
            self.assertTrue(folder.resolve().is_relative_to(self.run.resolve()), folder)

    def test_installer_input_is_generated_only_into_the_run_workspace(self):
        for relative in ('res/configs/driftkings', 'installer/setup', 'mod/res/mods/driftkings/text'):
            shutil.copytree(ROOT / relative, self.root / relative,
                            ignore=shutil.ignore_patterns('*.png', '*.bmp', '*.ico') if relative == 'installer/setup' else None)
        for relative in ('build_data/build_config.json', 'build_data/components.json',
                         'mod/res/scripts/client/driftkings/_constants.py'):
            write(self.root / relative, (ROOT / relative).read_bytes())
        layout = bi.installer_workspace(self.run)
        bi.generate_components(self.root, layout['input'])
        self.assertTrue((layout['input'] / 'components.generated.iss').is_file())
        self.assertFalse((self.root / 'build/installer_input').exists())
        self.assertFalse((self.root / 'build/installer').exists())

    def test_development_packages_cannot_be_installed(self):
        development = self.root / 'dev'
        write(development / 'driftkings.wotmod', WOTMOD)
        write(development / 'build-report.json', json.dumps(dict(status='success', version=VERSION)))
        with self.assertRaisesRegex(ValueError, 'Development packages have no distribution'):
            bi.prepare_payload(self.root, development, self.run / 'workspace/installer/input')


class CandidateLifecycleTests(InstallerRunFixture):
    def attach(self):
        setup = self.run / 'workspace/installer/output/Driftkings-0.1.8-WoT-2.4.2.0-Setup.exe'
        write(setup, b'MZ setup')
        return bi.attach_installer(self.candidate, setup)

    def test_the_candidate_states_are_distinct(self):
        self.assertEqual(ps.candidate_state(self.candidate), ps.CANDIDATE_STAGING)
        write(self.candidate / '.promotion-build.json', '{}')
        self.assertEqual(ps.candidate_state(self.candidate), ps.CANDIDATE_FROZEN)
        (self.candidate / '.promotion-build.json').unlink()
        write(self.candidate / 'release.json.sig', b'sig')
        self.assertEqual(ps.candidate_state(self.candidate), ps.CANDIDATE_FROZEN)

    def test_an_installer_attaches_before_finalization_and_keeps_the_package_identity(self):
        attached = self.attach()
        report = json.loads((self.candidate / 'build-report.json').read_text())
        self.assertIn(attached.name, report['artifacts'])
        self.assertEqual(report['artifacts']['driftkings.wotmod']['sha256'], self.digest)
        sums = dict(line.split('  ', 1)[::-1] for line in (self.candidate / 'SHA256SUMS.txt').read_text().splitlines())
        self.assertEqual(sums[attached.name], hashlib.sha256(attached.read_bytes()).hexdigest())

    def test_a_stamped_candidate_refuses_an_installer(self):
        write(self.candidate / '.promotion-build.json', '{}')
        with self.assertRaisesRegex(ValueError, 'frozen'):
            self.attach()

    def test_a_signed_candidate_refuses_an_installer_and_keeps_its_bytes(self):
        write(self.candidate / 'release.json.sig', b'sig')
        before = {p.name: p.read_bytes() for p in self.candidate.iterdir() if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'frozen'):
            self.attach()
        self.assertEqual({p.name: p.read_bytes() for p in self.candidate.iterdir() if p.is_file()}, before)


class CompilationTests(InstallerRunFixture):
    def fake_compiler(self, exit_code, setup=True):
        """A stand-in for ISCC.exe: it writes one setup next to the input folder, as Inno Setup would."""
        script = Path(self.root) / 'fake_iscc.py'
        script.write_text(
            'import pathlib, sys\n'
            'source = [a for a in sys.argv if a.startswith("/DInputDir=")][0].split("=", 1)[1]\n'
            'output = pathlib.Path(source).parent / "output"\n'
            'output.mkdir(parents=True, exist_ok=True)\n'
            + ('(output / "Driftkings-0.1.8-WoT-2.4.2.0-Setup.exe").write_bytes(b"MZ setup")\n' if setup else '')
            + 'sys.exit(%d)\n' % exit_code, encoding='utf-8')
        wrapper = Path(self.root) / 'fake_iscc.cmd'
        wrapper.write_text('@echo off\r\n"%s" "%s" %%*\r\n' % (sys.executable, script), encoding='utf-8')
        return str(wrapper)

    def setUp(self):
        super().setUp()
        if os.name != 'nt':
            self.skipTest('the compiler stand-in is a Windows command wrapper')
        write(self.root / 'installer/setup/driftkings.iss', '')

    def test_compilation_writes_setup_and_evidence_into_the_run_only(self):
        layout = bi.installer_workspace(self.run)
        setup = bi.compile_installer(self.root, layout, self.fake_compiler(0))
        self.assertTrue(setup.is_relative_to(self.run.resolve()))
        evidence = bi.record_installer_evidence(layout, setup, self.candidate, self.run)
        self.assertEqual(evidence['candidateWotmodSha256'], self.digest)
        self.assertEqual(evidence['run_id'], RUN)
        self.assertTrue((layout['logs'] / 'iscc.log').is_file())
        self.assertFalse((self.root / 'build/installer').exists())

    def test_a_failed_compilation_keeps_the_candidate_and_the_log(self):
        layout = bi.installer_workspace(self.run)
        before = {p.name: p.read_bytes() for p in self.candidate.iterdir() if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'Inno Setup failed'):
            bi.compile_installer(self.root, layout, self.fake_compiler(3, setup=False))
        self.assertTrue((layout['logs'] / 'iscc.log').is_file())
        self.assertEqual({p.name: p.read_bytes() for p in self.candidate.iterdir() if p.is_file()}, before)

    def test_exactly_one_setup_must_come_out(self):
        layout = bi.installer_workspace(self.run)
        with self.assertRaisesRegex(ValueError, 'exactly one installer'):
            bi.compile_installer(self.root, layout, self.fake_compiler(0, setup=False))


if __name__ == '__main__':
    unittest.main()
