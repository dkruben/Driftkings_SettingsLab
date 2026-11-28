"""Unsigned stable build, owner-controlled offline signing and finalization, with temporary fixtures and synthetic keys.

No production key is read, no compiler, installer or suite runs, and nothing is published: every external step is mocked.
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
from build_tools import promote_release as promotion
from build_tools import sign_release
from build_tools.package_tools import sha

RUN = '20261128T070000Z-5eed0001'
COMMIT = 'a' * 40
STABLE = '0.1.8'
TARGET = 'na1010'
WOTMOD = b'stable wotmod bytes'
SETUP = b'MZ stable installer bytes'
SETUP_NAME = 'Driftkings-0.1.8-WoT-2.4.2.0-Setup.exe'
SYNTHETIC_SEED = bytes(range(32))
OTHER_SEED = bytes(range(1, 33))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


class FakeContext(promotion.Context):
    """A Context without GitHub or the real repository; promote() is recorded, never executed."""
    def __init__(self, root):
        self.root = root
        self.promoted = []

    def git(self, *args):
        return COMMIT if args[:1] == ('rev-parse',) else ''

    def promote(self, folder, stable):
        self.promoted.append((folder, stable))
        return Path('promoted') / stable


class CandidateFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'repo'
        self.run = self.root / 'build/runs' / RUN
        self.output = self.run / 'output'
        self.evidence = self.run / 'evidence'
        self.module = sign_release.load_signature()
        self.key = Path(temp.name) / 'synthetic-release.key'
        write(self.key, SYNTHETIC_SEED.hex())
        write(self.root / 'build_data/build_config.json',
              json.dumps(dict(package=dict(release_root='build/releases'))))
        self.context = FakeContext(self.root)
        self.identity = dict(stable=STABLE, commit=COMMIT, route='direct', tag='v' + STABLE)
        self.build_unsigned_candidate()

    def build_unsigned_candidate(self):
        """What the compiler and the installer attachment leave behind, before any signature."""
        digest = hashlib.sha256(WOTMOD).hexdigest()
        write(self.output / 'driftkings.wotmod', WOTMOD)
        write(self.output / 'release.json', json.dumps(dict(schema=2, version=STABLE, channel='stable',
                                                             gameVersion='2.4.2.0', sha256=digest)))
        write(self.output / SETUP_NAME, SETUP)
        report = dict(status='success', mode='release', profile='production', realm='NA', version=STABLE,
                      channel='stable', gameVersion='2.4.2.0', target=TARGET, publishable=False,
                      git=dict(commit=COMMIT, dirty=False), tools={'python': 'local'}, output=str(self.output),
                      evidence=str(self.evidence), workspace='local', logs='local', wotmod='local', canonical='local',
                      artifacts={'driftkings.wotmod': dict(size=len(WOTMOD), sha256=digest),
                                 'release.json': dict(size=(self.output / 'release.json').stat().st_size,
                                                      sha256=sha(self.output / 'release.json'))})
        # The evidence copy is written before the installer is attached, so it lacks the installer entries.
        evidence_report = json.loads(json.dumps(report))
        write(self.evidence / 'build-report.json', json.dumps(evidence_report))
        report['artifacts'][SETUP_NAME] = dict(size=len(SETUP), sha256=sha(self.output / SETUP_NAME))
        report['setupArchive'] = None
        write(self.output / 'build-report.json', json.dumps(report))
        names = sorted(set(report['artifacts']) | {'build-report.json'})
        write(self.output / 'SHA256SUMS.txt', ''.join('%s  %s\n' % (sha(self.output / n), n) for n in names))
        promotion.write_unsigned_evidence(self.output, STABLE, TARGET, COMMIT)

    def sign(self, key=None):
        sign_release.sign_folder(self.output, key or self.key)

    def trusted(self, *seeds):
        keys = tuple(self.module.public_key(seed).hex() for seed in seeds)
        return types.SimpleNamespace(TRUSTED_KEYS=keys, SIGNATURE_ASSET=self.module.SIGNATURE_ASSET,
                                     verify_manifest=self.module.verify_manifest)

    def finalize(self, signature=None, identity=None):
        return promotion.finalize_candidate(self.context, self.output, identity or self.identity, TARGET,
                                            signature=signature or self.trusted(SYNTHETIC_SEED))


class UnsignedBuildTests(CandidateFixture):
    def test_unsigned_compile_reads_no_key_and_runs_no_signing_step(self):
        completed = subprocess.CompletedProcess([], 0, stdout='  output:   %s\n' % self.output, stderr=None)
        context = promotion.Context.__new__(promotion.Context)
        context.root = self.root
        with mock.patch.object(promotion.subprocess, 'run', return_value=completed) as run, \
                mock.patch.object(promotion, 'sign_folder') as sign:
            folder = promotion.Context.compile_unsigned(context, STABLE, TARGET)
        sign.assert_not_called()
        commands = [' '.join(str(part) for part in call.args[0]) for call in run.call_args_list]
        self.assertFalse(any('--key' in command or 'release-signing' in command for command in commands))
        self.assertTrue(any('--suite artifacts' in command for command in commands))
        self.assertEqual(folder, self.output)

    def test_a_failed_artifact_suite_stops_the_unsigned_build(self):
        completed = subprocess.CompletedProcess([], 0, stdout='  output:   %s\n' % self.output, stderr=None)

        def fake(command, **kwargs):
            if 'artifacts' in command:
                raise subprocess.CalledProcessError(1, command)
            return completed
        context = promotion.Context.__new__(promotion.Context)
        context.root = self.root
        with mock.patch.object(promotion.subprocess, 'run', side_effect=fake):
            with self.assertRaises(subprocess.CalledProcessError):
                promotion.Context.compile_unsigned(context, STABLE, TARGET)

    def test_unsigned_output_cannot_be_promoted_or_published(self):
        with self.assertRaisesRegex(ValueError, 'stamped and signed'):
            compiler.promote_run(self.root, self.run)
        with self.assertRaisesRegex(ValueError, 'run it first'):
            promotion.require_build_stamp(self.output, COMMIT)
        self.assertFalse((self.output / promotion.BUILD_STAMP).exists())

    def test_unsigned_build_refuses_a_signing_key(self):
        args = types.SimpleNamespace(stable=STABLE, beta=None, key=self.key, unsigned=True, target=TARGET)
        with mock.patch.object(promotion, 'require_clean_checkout'):
            with self.assertRaisesRegex(ValueError, 'takes the direct stable route and no signing key'):
                promotion.run_build(self.context, args)


class FinalizeTests(CandidateFixture):
    def test_a_correctly_signed_candidate_is_finalized_without_compiling_or_signing(self):
        self.sign()
        with mock.patch.object(promotion.subprocess, 'run', side_effect=AssertionError('no subprocess')), \
                mock.patch.object(promotion, 'sign_folder', side_effect=AssertionError('no signing')):
            promoted = self.finalize()
        self.assertEqual(promoted, Path('promoted') / STABLE)
        self.assertEqual(self.context.promoted, [(self.output, STABLE)])
        stamp = json.loads((self.output / promotion.BUILD_STAMP).read_text(encoding='utf-8'))
        self.assertEqual(stamp, dict(commit=COMMIT, digest=promotion.artifacts_digest(self.output),
                                     manifestSha256=sha(self.output / 'release.json'), artifactSuite='passed'))
        compiler.verify_checksums(self.output)  # signatures and the stamp are outside the inventory, as designed

    def test_finalized_candidate_is_promotable_by_the_existing_promotion_copy(self):
        from build_tools import sign_release
        self.sign()
        self.finalize()
        with mock.patch.object(sign_release, 'load_signature', return_value=self.trusted(SYNTHETIC_SEED)):
            destination = compiler.promote_run(self.root, self.run)
        self.assertEqual(destination, self.root / 'build/releases/stable' / STABLE)
        self.assertEqual((destination / 'driftkings.wotmod').read_bytes(), WOTMOD)

    def test_a_second_finalization_is_refused(self):
        self.sign()
        self.finalize()
        with self.assertRaisesRegex(ValueError, 'already stamped'):
            self.finalize()

    def test_an_incorrect_signature_is_rejected(self):
        self.sign()
        write(self.output / 'release.json.sig', b'AAAA' * 22 + b'\n')  # not a valid 64-byte signature
        with self.assertRaisesRegex(ValueError, 'not valid for a trusted production key'):
            self.finalize()

    def test_an_unexpected_public_key_is_rejected(self):
        self.sign(key=self.key)
        with self.assertRaisesRegex(ValueError, 'not valid for a trusted production key'):
            self.finalize(signature=self.trusted(OTHER_SEED))

    def test_an_empty_trust_list_is_rejected(self):
        self.sign()
        with self.assertRaisesRegex(ValueError, 'TRUSTED_KEYS is empty'):
            self.finalize(signature=types.SimpleNamespace(TRUSTED_KEYS=(), SIGNATURE_ASSET=self.module.SIGNATURE_ASSET,
                                                          verify_manifest=self.module.verify_manifest))

    def test_a_modified_wotmod_is_rejected(self):
        self.sign()
        write(self.output / 'driftkings.wotmod', WOTMOD + b' changed')
        with self.assertRaisesRegex(ValueError, 'differs from the unsigned build: driftkings.wotmod'):
            self.finalize()

    def test_a_modified_installer_is_rejected(self):
        self.sign()
        write(self.output / SETUP_NAME, SETUP + b' changed')
        with self.assertRaisesRegex(ValueError, 'differs from the unsigned build: ' + SETUP_NAME):
            self.finalize()

    def test_a_missing_artifact_is_rejected(self):
        self.sign()
        (self.output / SETUP_NAME).unlink()
        with self.assertRaisesRegex(ValueError, 'Missing artifacts'):
            self.finalize()

    def test_an_unexpected_file_is_rejected(self):
        self.sign()
        write(self.output / 'extra.txt', 'not part of the candidate')
        with self.assertRaisesRegex(ValueError, 'Unexpected files'):
            self.finalize()

    def test_incomplete_evidence_is_rejected(self):
        self.sign()
        (self.evidence / promotion.UNSIGNED_EVIDENCE).unlink()
        with self.assertRaisesRegex(ValueError, 'Incomplete build evidence'):
            self.finalize()

    def test_failed_artifact_tests_prevent_finalization(self):
        self.sign()
        write(self.evidence / promotion.UNSIGNED_EVIDENCE,
              json.dumps(dict(json.loads((self.evidence / promotion.UNSIGNED_EVIDENCE).read_text()),
                              artifactSuite='failed')))
        with self.assertRaisesRegex(ValueError, 'did not pass its artifact suite'):
            self.finalize()

    def test_wrong_commit_version_or_target_is_rejected(self):
        self.sign()
        with self.assertRaisesRegex(ValueError, 'another commit'):
            self.finalize(identity=dict(self.identity, commit='b' * 40))
        with self.assertRaisesRegex(ValueError, 'is not 0.1.9/stable'):
            self.finalize(identity=dict(self.identity, stable='0.1.9'))
        with self.assertRaisesRegex(ValueError, 'for target eu1007'):
            promotion.finalize_candidate(self.context, self.output, self.identity, 'eu1007',
                                         signature=self.trusted(SYNTHETIC_SEED))

    def test_a_folder_outside_build_runs_is_rejected(self):
        self.sign()
        outside = self.root / 'elsewhere' / 'output'
        with self.assertRaisesRegex(ValueError, 'under build/runs'):
            promotion.finalize_candidate(self.context, outside, self.identity, TARGET,
                                         signature=self.trusted(SYNTHETIC_SEED))


class PublicationGateTests(unittest.TestCase):
    def test_the_protected_approval_gate_stays_mandatory_for_the_direct_route(self):
        context = types.SimpleNamespace(repository='owner/repo',
                                        query=lambda path, missing_ok=False: {'workflow_runs': []})
        with self.assertRaisesRegex(ValueError, 'No approved'):
            promotion.find_gate(context, STABLE, COMMIT, 'f' * 64, False, title='Promotion direct 0.1.8', direct=True)


class CheckedInventoryTests(CandidateFixture):
    def test_the_inventory_ignores_only_signature_and_stamp_files(self):
        self.sign()
        self.finalize()
        compiler.verify_checksums(self.output)
        write(self.output / 'extra.txt', 'unlisted')
        with self.assertRaisesRegex(ValueError, 'Checksum inventory mismatch'):
            compiler.verify_checksums(self.output)


if __name__ == '__main__':
    unittest.main()
