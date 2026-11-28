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
        self.identity = dict(stable=STABLE, version=STABLE, channel='stable', commit=COMMIT, route='direct',
                             tag='v' + STABLE)
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
            with self.assertRaisesRegex(ValueError, 'takes no signing key'):
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
            self.finalize(identity=dict(self.identity, version='0.1.9'))
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




class GitCheckoutContext(promotion.Context):
    """A real temporary Git repository with the same read-only calls the promotion tool makes."""

    def __init__(self, root):
        self.root = root
        self.repository = 'owner/synthetic'
        self.version_source = 'mod/res/scripts/client/driftkings/__init__.py'
        self.promoted = []

    def git(self, *args):
        return subprocess.run(['git'] + list(args), cwd=self.root, check=True,
                              stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

    def read(self, commit, path):
        return subprocess.run(['git', 'show', '%s:%s' % (commit, path)], cwd=self.root, check=True,
                              stdout=subprocess.PIPE).stdout.decode('utf-8')

    def is_ancestor(self, ancestor, commit):
        return subprocess.run(['git', 'merge-base', '--is-ancestor', ancestor, commit], cwd=self.root).returncode == 0

    def promote(self, folder, version):
        self.promoted.append(version)
        return Path('promoted') / version


class ArtifactPredatesTooling(unittest.TestCase):
    """A stable artifact built before the signing tooling is finalized from the later checkout, and nothing else."""

    def commit(self, message, changes):
        for path, text in changes.items():
            write(self.repo / path, text)
        subprocess.run(['git', 'add', '-A'], cwd=self.repo, check=True)
        subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '-m', message],
                       cwd=self.repo, check=True)
        return self.context.git('rev-parse', 'HEAD')

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name).resolve() / 'repo'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)
        self.context = GitCheckoutContext(self.repo)
        self.artifact = self.commit('release', {
            '.gitignore': 'build/\n',
            'build_data/release.json': json.dumps(dict(version=STABLE, channel='stable')),
            'mod/res/scripts/client/driftkings/__init__.py': "VERSION = '%s'\n" % STABLE,
            'build_tools/sign_candidate.py': '# before the tooling commit\n'})
        self.key = self.repo.parent / 'synthetic.key'
        write(self.key, SYNTHETIC_SEED.hex())
        self.module = sign_release.load_signature()
        self.trusted = types.SimpleNamespace(
            TRUSTED_KEYS=(self.module.public_key(SYNTHETIC_SEED).hex(),),
            verify_manifest=self.module.verify_manifest, SIGNATURE_ASSET=self.module.SIGNATURE_ASSET)
        self.run = self.repo / 'build/runs' / RUN
        self.output, self.evidence = self.run / 'output', self.run / 'evidence'
        self.build_signed_candidate(self.artifact)

    def build_signed_candidate(self, commit):
        write(self.output / 'driftkings.wotmod', WOTMOD)
        write(self.output / 'release.json', json.dumps(dict(schema=2, version=STABLE, channel='stable',
                                                             gameVersion='2.4.2.0')))
        write(self.output / SETUP_NAME, SETUP)
        report = dict(status='success', mode='release', profile='production', realm='NA', version=STABLE,
                      channel='stable', gameVersion='2.4.2.0', target=TARGET, verification_result='passed',
                      git=dict(commit=commit, dirty=False),
                      artifacts={name: dict(size=(self.output / name).stat().st_size, sha256=sha(self.output / name))
                                 for name in ('driftkings.wotmod', 'release.json', SETUP_NAME)})
        write(self.output / 'build-report.json', json.dumps(report))
        names = sorted(set(report['artifacts']) | {'build-report.json'})
        sums = ''.join('%s  %s\n' % (sha(self.output / n), n) for n in names)
        write(self.output / 'SHA256SUMS.txt', sums)
        write(self.evidence / 'build-report.json', json.dumps(report))
        write(self.evidence / promotion.UNSIGNED_INVENTORY, sums)
        write(self.evidence / promotion.UNSIGNED_EVIDENCE, json.dumps(dict(
            schema=1, stage='unsigned', version=STABLE, channel='stable', target=TARGET, commit=commit,
            artifactSuite='passed', wotmodSha256=sha(self.output / 'driftkings.wotmod'),
            inventorySha256=sha(self.output / 'SHA256SUMS.txt'))))
        sign_release.sign_folder(self.output, self.key, self.module)

    def finalize_from(self, artifact, head):
        identity = promotion.artifact_identity(
            self.context, lambda ctx, commit: promotion.direct_identity(ctx, STABLE, commit), artifact, head)
        return promotion.finalize_candidate(self.context, self.output, identity, TARGET, signature=self.trusted)

    def test_a_later_tooling_commit_finalizes_the_original_artifact_commit(self):
        tooling = self.commit('signing automation', {'build_tools/sign_candidate.py': '# after the tooling commit\n',
                                                     'docs/releases/README.md': 'notes\n'})
        promoted = self.finalize_from(self.artifact, tooling)
        self.assertEqual(promoted, Path('promoted') / STABLE)
        report = json.loads((self.output / 'build-report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['git']['commit'], self.artifact)  # the source identity is never rewritten
        meta = json.loads((self.evidence / promotion.UNSIGNED_EVIDENCE).read_text(encoding='utf-8'))
        self.assertEqual(meta['commit'], self.artifact)

    def test_a_package_change_after_the_artifact_refuses_finalization(self):
        bad = self.commit('compiler change', {'build_tools/compiler.py': '# reaches the package\n'})
        with self.assertRaisesRegex(ValueError, 'reach the package: build_tools/compiler.py'):
            self.finalize_from(self.artifact, bad)

    def test_a_runtime_change_after_the_artifact_refuses_finalization(self):
        bad = self.commit('runtime change', {'mod/res/scripts/client/driftkings/core/accounts.py': '# runtime\n'})
        with self.assertRaisesRegex(ValueError, 'reach the package'):
            self.finalize_from(self.artifact, bad)

    def test_an_artifact_that_is_not_an_ancestor_of_the_checkout_is_refused(self):
        tooling = self.commit('signing automation', {'build_tools/sign_candidate.py': '# later\n'})
        with self.assertRaisesRegex(ValueError, 'not an ancestor of the checkout'):
            promotion.artifact_identity(self.context, lambda ctx, commit: promotion.direct_identity(ctx, STABLE, commit),
                                        tooling, self.artifact)

    def test_a_checkout_at_the_artifact_commit_needs_no_descendant_rule(self):
        identity = promotion.artifact_identity(
            self.context, lambda ctx, commit: promotion.direct_identity(ctx, STABLE, commit), self.artifact, self.artifact)
        self.assertEqual(identity['commit'], self.artifact)

    def test_a_tampered_artifact_is_still_refused_from_a_later_checkout(self):
        tooling = self.commit('signing automation', {'build_tools/sign_candidate.py': '# later\n'})
        write(self.output / 'driftkings.wotmod', WOTMOD + b' tampered')
        with self.assertRaisesRegex(ValueError, 'differs from the unsigned build'):
            self.finalize_from(self.artifact, tooling)



class FinalizeOutputTests(unittest.TestCase):
    """The finalization command reports the artifact commit without a NameError, for both channels."""

    def run_route(self, **route):
        import contextlib
        import io as stdio
        args = types.SimpleNamespace(commit=None, folder=Path('unused'), target=TARGET, **route)
        identity = dict(version=route.get('stable') or route.get('beta'),
                        channel='stable' if route.get('stable') else 'beta', commit=COMMIT)
        output = stdio.StringIO()
        with mock.patch.object(promotion, 'require_clean_checkout'),                 mock.patch.object(promotion, 'artifact_identity', return_value=identity),                 mock.patch.object(promotion, 'finalize_candidate', return_value=Path('promoted')),                 contextlib.redirect_stdout(output):
            promotion.run_finalize(FakeContext(Path('unused')), args)
        return identity, output.getvalue()

    def test_stable_finalization_reports_the_artifact_commit(self):
        identity, text = self.run_route(stable=STABLE)
        self.assertIn('Finalized 0.1.8/stable from %s' % COMMIT[:12], text)

    def test_beta_finalization_reports_the_artifact_commit(self):
        identity, text = self.run_route(beta='0.1.8-beta.25')
        self.assertIn('Finalized 0.1.8-beta.25/beta from %s' % COMMIT[:12], text)


class UnsignedBetaIdentityTests(unittest.TestCase):
    """The unsigned beta route accepts only committed beta release data for the requested beta."""

    def context(self, version, channel):
        release = json.dumps(dict(version=version, channel=channel))
        source = "\"\"\"Runtime package.\"\"\"\nVERSION = '%s'\n" % version
        return types.SimpleNamespace(
            version_source='mod/res/scripts/client/driftkings/__init__.py',
            read=lambda commit, path: release if path == promotion.RELEASE_DATA else source)

    def test_a_committed_beta_is_accepted_on_the_beta_channel(self):
        identity = promotion.unsigned_beta_identity(self.context('0.1.8-beta.25', 'beta'), '0.1.8-beta.25', COMMIT)
        self.assertEqual((identity['version'], identity['channel'], identity['commit']),
                         ('0.1.8-beta.25', 'beta', COMMIT))

    def test_a_stable_or_mismatched_release_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'not 0.1.8-beta.25/beta'):
            promotion.unsigned_beta_identity(self.context('0.1.8', 'stable'), '0.1.8-beta.25', COMMIT)
        with self.assertRaisesRegex(ValueError, 'such as 1.2.3-beta.4'):
            promotion.unsigned_beta_identity(self.context('0.1.8', 'stable'), '0.1.8', COMMIT)


if __name__ == '__main__':
    unittest.main()
