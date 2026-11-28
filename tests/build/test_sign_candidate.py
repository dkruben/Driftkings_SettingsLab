"""Owner-controlled signing automation, with temporary fixtures and synthetic test-only keys.

No production key is read, no compiler or installer runs, and nothing is published: external calls are mocked.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import compiler
from build_tools import sign_candidate as sc
from build_tools import sign_release
from build_tools.package_tools import sha

COMMIT = 'c' * 40
TARGET = 'na1010'
WOTMOD = b'synthetic wotmod'
SETUP = b'MZ synthetic setup'
SETUP_NAME = 'Driftkings-%s-WoT-2.4.2.0-Setup.exe'
ZIP_NAME = 'Driftkings-%s-WoT-2.4.2.0.zip'
SYNTHETIC_SEED = bytes(range(32))
OTHER_SEED = bytes(range(1, 33))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


class CandidateFixture(unittest.TestCase):
    version = '0.1.8'
    channel = 'stable'

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.run = self.base / 'repo/build/runs/20261128T070000Z-5eed0002'
        self.output = self.run / 'output'
        self.evidence = self.run / 'evidence'
        self.signing = self.base / 'signing'
        self.key = self.base / 'synthetic-owner.key'
        write(self.key, SYNTHETIC_SEED.hex())
        self.real = sign_release.load_signature()
        self.trusted = types.SimpleNamespace(
            TRUSTED_KEYS=(self.real.public_key(SYNTHETIC_SEED).hex(),), sign=self.real.sign,
            public_key=self.real.public_key, verify=self.real.verify,
            verify_manifest=self.real.verify_manifest, SIGNATURE_ASSET=self.real.SIGNATURE_ASSET)
        self.build()

    def build(self):
        """The files the build leaves behind: unsigned, complete, with its unsigned evidence."""
        version, channel = self.version, self.channel
        write(self.output / 'driftkings.wotmod', WOTMOD)
        write(self.output / 'release.json', json.dumps(dict(schema=2, version=version, channel=channel,
                                                             gameVersion='2.4.2.0')))
        write(self.output / 'modpack.json', '{}')
        setup, archive = SETUP_NAME % version, ZIP_NAME % version
        write(self.output / setup, SETUP)
        write(self.output / archive, b'zip')
        report = dict(status='success', mode='release', profile='production', realm='NA', version=version,
                      channel=channel, gameVersion='2.4.2.0', target=TARGET, verification_result='passed',
                      git=dict(commit=COMMIT, dirty=False), runtime_realms=['EU', 'NA'],
                      artifacts={name: dict(size=(self.output / name).stat().st_size, sha256=sha(self.output / name))
                                 for name in (setup, archive, 'driftkings.wotmod', 'release.json', 'modpack.json')})
        write(self.output / 'build-report.json', json.dumps(report))
        names = sorted(set(report['artifacts']) | {'build-report.json'})
        sums = ''.join('%s  %s\n' % (sha(self.output / n), n) for n in names)
        write(self.output / 'SHA256SUMS.txt', sums)
        write(self.evidence / 'build-report.json', json.dumps(report))
        write(self.evidence / sc.UNSIGNED_INVENTORY, sums)
        write(self.evidence / sc.UNSIGNED_EVIDENCE, json.dumps(dict(
            schema=1, stage='unsigned', version=version, channel=channel, target=TARGET, commit=COMMIT,
            artifactSuite='passed', wotmodSha256=sha(self.output / 'driftkings.wotmod'),
            inventorySha256=sha(self.output / 'SHA256SUMS.txt'))))
        # The candidate's report is not rewritten here: the inventory check compares the actual bytes.
        self.report_path = self.output / 'build-report.json'

    def use_candidate(self, version, channel):
        """A fresh run for another version or channel, so no file from another candidate is left behind."""
        self.version, self.channel = version, channel
        self.run = self.base / 'repo/build/runs' / ('run-' + version)
        self.output, self.evidence = self.run / 'output', self.run / 'evidence'
        self.build()

    def settings(self, key=None):
        return dict(signing_root=str(self.signing), signing_key=str(key or self.key))

    def prepare(self):
        with mock.patch.object(sc, 'settings', return_value=self.settings()):
            return sc.prepare(self.run, out=lambda *_: None)

    def sign(self, confirm=lambda phrase: True, key=None):
        with mock.patch.object(sc, 'settings', return_value=self.settings(key)), \
                mock.patch.object(sc.sign_release, 'load_signature', return_value=self.trusted):
            return sc.sign(self.destination(), confirm=confirm, out=lambda *_: None)

    def destination(self):
        return self.signing / self.channel / self.version

    def finalize(self, returncode=0):
        completed = subprocess.CompletedProcess([], returncode)
        with mock.patch.object(sc, 'settings', return_value=self.settings()), \
                mock.patch.object(sc.sign_release, 'load_signature', return_value=self.trusted), \
                mock.patch.object(sc.subprocess, 'run', return_value=completed) as run:
            code = sc.finalize(self.run, out=lambda *_: None)
        return code, run


class ChannelTests(CandidateFixture):
    def test_stable_version_selects_the_stable_folder(self):
        self.assertEqual(self.prepare(), self.signing / 'stable' / '0.1.8')

    def test_beta_version_selects_the_beta_folder(self):
        self.use_candidate('0.1.8-beta.25', 'beta')
        self.assertEqual(self.prepare(), self.signing / 'beta' / '0.1.8-beta.25')


class PrepareTests(CandidateFixture):
    def test_a_valid_candidate_is_copied_with_a_manifest_and_nothing_is_signed(self):
        destination = self.prepare()
        manifest = json.loads((self.signing / 'stable' / '0.1.8.dk-candidate.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['status'], 'prepared')
        self.assertEqual(manifest['commit'], COMMIT)
        self.assertEqual(manifest['wotmodSha256'], sha(self.output / 'driftkings.wotmod'))
        self.assertFalse((destination / 'release.json.sig').exists())
        self.assertEqual(self.prepare(), destination)  # identical repeat is accepted

    def test_an_incomplete_build_is_rejected(self):
        report = json.loads(self.report_path.read_text(encoding='utf-8'))
        report['status'] = 'failure'
        write(self.report_path, json.dumps(report))
        with self.assertRaisesRegex(sc.Refused, 'successful production release build'):
            self.prepare()

    def test_development_artifacts_are_rejected(self):
        report = json.loads(self.report_path.read_text(encoding='utf-8'))
        report['mode'] = 'dev'
        write(self.report_path, json.dumps(report))
        with self.assertRaisesRegex(sc.Refused, 'successful production release build'):
            self.prepare()

    def test_a_modified_artifact_is_rejected(self):
        write(self.output / 'driftkings.wotmod', WOTMOD + b' changed')
        with self.assertRaisesRegex(sc.Refused, 'Modified artifact'):
            self.prepare()

    def test_a_different_existing_candidate_is_never_overwritten(self):
        self.prepare()
        manifest_path = self.signing / 'stable' / '0.1.8.dk-candidate.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['files']['driftkings.wotmod'] = 'f' * 64
        write(manifest_path, json.dumps(manifest))
        with self.assertRaisesRegex(sc.Refused, 'never overwritten'):
            self.prepare()

    def test_a_different_file_at_the_destination_is_refused(self):
        write(self.signing / 'stable' / '0.1.8' / 'driftkings.wotmod', b'other bytes')
        with self.assertRaisesRegex(sc.Refused, 'refusing to overwrite'):
            self.prepare()

    def test_an_interrupted_copy_is_recovered(self):
        destination = self.signing / 'stable' / '0.1.8'
        write(destination / ('driftkings.wotmod' + sc.PARTIAL), b'half')
        self.assertEqual(self.prepare(), destination)
        self.assertFalse(list(destination.glob('*' + sc.PARTIAL)))
        self.assertEqual((destination / 'driftkings.wotmod').read_bytes(), WOTMOD)


class SignTests(CandidateFixture):
    def test_owner_cancellation_reads_no_key(self):
        self.prepare()
        with mock.patch.object(sc.sign_release, 'read_seed', side_effect=AssertionError('key read')):
            with self.assertRaises(sc.Cancelled):
                self.sign(confirm=lambda phrase: False)
        self.assertFalse((self.destination() / 'release.json.sig').exists())

    def test_a_key_that_is_not_trusted_signs_nothing(self):
        self.prepare()
        write(self.base / 'other.key', OTHER_SEED.hex())
        with self.assertRaisesRegex(sc.Refused, 'not a trusted production key'):
            self.sign(key=self.base / 'other.key')
        self.assertFalse((self.destination() / 'release.json.sig').exists())

    def test_a_modified_candidate_file_is_rejected_before_signing(self):
        self.prepare()
        write(self.destination() / 'driftkings.wotmod', b'changed')
        with self.assertRaisesRegex(sc.Refused, 'Modified candidate file'):
            self.sign()

    def test_successful_signing_produces_both_verified_signatures_and_marks_the_candidate(self):
        self.prepare()
        self.sign()
        self.assertTrue((self.destination() / 'release.json.sig').is_file())
        self.assertTrue((self.destination() / 'SHA256SUMS.txt.sig').is_file())
        manifest = json.loads((self.signing / 'stable' / '0.1.8.dk-candidate.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['status'], 'signed')
        self.trusted.verify_manifest((self.destination() / 'release.json').read_bytes(),
                                     (self.destination() / 'release.json.sig').read_bytes(), self.trusted.TRUSTED_KEYS)
        with self.assertRaisesRegex(sc.Refused, 'already signed|only a prepared'):
            self.sign()

    def test_signing_does_not_contact_github_or_publish(self):
        source = Path(sc.__file__).read_text(encoding='utf-8')
        self.assertNotIn('publish_release', source)
        self.assertNotIn('gh api', source)


class FinalizeTests(CandidateFixture):
    def signed(self):
        self.prepare()
        self.sign()

    def test_finalize_refuses_an_unsigned_candidate(self):
        self.prepare()
        with self.assertRaisesRegex(sc.Refused, 'not signed yet'):
            self.finalize()

    def test_returns_only_the_four_signed_files_then_runs_the_existing_finalization(self):
        self.signed()
        before = sha(self.evidence / sc.UNSIGNED_EVIDENCE), sha(self.evidence / sc.UNSIGNED_INVENTORY)
        code, run = self.finalize()
        self.assertEqual(code, 0)
        for name in ('release.json.sig', 'SHA256SUMS.txt.sig', 'build-report.json', 'SHA256SUMS.txt'):
            self.assertTrue((self.output / name).is_file(), name)
        self.assertEqual((self.output / 'driftkings.wotmod').read_bytes(), WOTMOD)
        self.assertEqual(before, (sha(self.evidence / sc.UNSIGNED_EVIDENCE), sha(self.evidence / sc.UNSIGNED_INVENTORY)))
        command = run.call_args.args[0]
        self.assertIn('finalize', command)
        self.assertIn('--stable', command)
        self.assertEqual(command[command.index('--commit') + 1], 'c' * 40)
        self.assertIn('--folder', command)
        self.assertEqual(command[command.index('--folder') + 1], str(self.output))

    def test_beta_candidates_use_the_beta_route_of_the_same_finalization(self):
        self.use_candidate('0.1.8-beta.25', 'beta')
        self.signed()
        _, run = self.finalize()
        self.assertIn('--beta', run.call_args.args[0])

    def test_an_altered_immutable_artifact_is_rejected_before_anything_is_returned(self):
        self.signed()
        write(self.destination() / 'driftkings.wotmod', b'changed after signing')
        with self.assertRaisesRegex(sc.Refused, 'Immutable artifact differs'):
            self.finalize()
        self.assertFalse((self.output / 'release.json.sig').exists())

    def test_an_incorrect_signature_is_rejected(self):
        self.signed()
        write(self.destination() / 'release.json.sig', b'AAAA' * 22 + b'\n')
        with self.assertRaisesRegex(sc.Refused, 'do not verify'):
            self.finalize()
        self.assertFalse((self.output / 'release.json.sig').exists())

    def test_a_different_signature_already_in_the_run_is_not_replaced(self):
        self.signed()
        write(self.output / 'release.json.sig', b'someone else')
        with self.assertRaisesRegex(sc.Refused, 'refusing to replace'):
            self.finalize()

    def test_repeated_return_is_idempotent_until_the_promotion_step(self):
        self.signed()
        self.finalize()
        code, _ = self.finalize()
        self.assertEqual(code, 0)

    def test_failed_existing_finalization_reports_its_exit_code(self):
        self.signed()
        code, _ = self.finalize(returncode=1)
        self.assertEqual(code, 1)


class CommandLineTests(CandidateFixture):
    def test_cancelled_signing_exits_with_code_three(self):
        self.prepare()
        with mock.patch.object(sc, 'settings', return_value=self.settings()), \
                mock.patch.object(sc.sign_release, 'load_signature', return_value=self.trusted):
            code = sc.run_cli(['sign', '--candidate', str(self.destination())], confirm=lambda phrase: False)
        self.assertEqual(code, sc.EXIT_CANCELLED)

    def test_a_refused_prepare_exits_with_code_two(self):
        write(self.output / 'driftkings.wotmod', b'changed')
        with mock.patch.object(sc, 'settings', return_value=self.settings()):
            self.assertEqual(sc.run_cli(['prepare', '--run', str(self.run)]), sc.EXIT_REFUSED)


if __name__ == '__main__':
    unittest.main()
