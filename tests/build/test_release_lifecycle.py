"""Candidate lifecycle, WGMods Setup archive and full-digest beta approvals, with temporary fixtures and mocks only."""
import hashlib
import json
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import build_installer as bi
from build_tools import compiler
from build_tools import promote_release as promotion
from build_tools import publication_state as ps
from build_tools.package_tools import sha

RUN = '20261128T010203Z-0badc0de'
WOTMOD = b'wotmod bytes'
SETUP = b'MZ final setup bytes'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


class ReleaseRunFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'repo'
        self.run = self.root / 'build/runs' / RUN
        self.output = self.run / 'output'
        write(self.output / 'driftkings.wotmod', WOTMOD)
        digest = hashlib.sha256(WOTMOD).hexdigest()
        write(self.output / 'release.json', json.dumps(dict(schema=2, version='0.1.8', channel='stable',
                                                             gameVersion='2.4.2.0', sha256=digest)))
        write(self.output / 'build-report.json', json.dumps(dict(
            status='success', mode='release', profile='production', realm='NA', version='0.1.8', gameVersion='2.4.2.0',
            run_id=RUN, channel='stable', artifacts={'driftkings.wotmod': dict(sha256=digest),
                                                     'release.json': dict(sha256=sha(self.output / 'release.json'))})))
        write(self.root / 'build_data/build_config.json', json.dumps(dict(package=dict(
            release_root='build/releases', debug_root='build/debug'))))
        write(self.run / 'evidence/build-report.json', json.dumps(dict(run_id=RUN, status='success', mode='release',
                                                                       channel='stable', version='0.1.8')))
        write(self.output / 'SHA256SUMS.txt', '')
        self.setup_source = self.run / 'workspace/installer/output/Driftkings-0.1.8-WoT-2.4.2.0-Setup.exe'
        write(self.setup_source, SETUP)


class SetupArchiveTests(ReleaseRunFixture):
    def build(self, name='archive.zip'):
        return bi.build_setup_archive(self.setup_source, self.run / name)

    def test_the_archive_holds_exactly_the_final_executable(self):
        archive = self.build()
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(bundle.namelist(), [self.setup_source.name])
            self.assertEqual(bundle.read(self.setup_source.name), SETUP)
        self.assertEqual(bi.verify_setup_archive(archive, self.setup_source), sha(self.setup_source))

    def test_identical_bytes_give_identical_archives(self):
        first = self.build('first.zip')
        second = self.build('second.zip')
        self.assertEqual(sha(first), sha(second))

    def test_altered_executable_inside_the_archive_is_rejected(self):
        archive = self.build()
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr(self.setup_source.name, b'MZ tampered bytes')
        with self.assertRaisesRegex(ValueError, 'size differs|not the standalone executable'):
            bi.verify_setup_archive(archive, self.setup_source)

    def test_same_size_alteration_is_rejected_by_digest(self):
        archive = self.build()
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr(self.setup_source.name, SETUP[:-1] + b'X')
        with self.assertRaisesRegex(ValueError, 'not the standalone executable'):
            bi.verify_setup_archive(archive, self.setup_source)

    def test_unexpected_entries_are_rejected(self):
        archive = self.build()
        with zipfile.ZipFile(archive, 'a') as bundle:
            bundle.writestr('notes.txt', b'extra')
        with self.assertRaisesRegex(ValueError, 'exactly the Setup executable'):
            bi.verify_setup_archive(archive, self.setup_source)

    def test_unsafe_entry_names_are_rejected(self):
        for name in ('../' + self.setup_source.name, '/' + self.setup_source.name, 'sub/' + self.setup_source.name):
            with self.subTest(name=name):
                archive = self.run / 'unsafe.zip'
                with zipfile.ZipFile(archive, 'w') as bundle:
                    bundle.writestr(name, SETUP)
                with self.assertRaises(ValueError):
                    bi.verify_setup_archive(archive, self.setup_source)

    def test_stable_and_beta_names_follow_the_release_convention(self):
        self.assertEqual(bi.setup_archive_name({'version': '0.1.8', 'gameVersion': '2.4.2.0'}),
                         'Driftkings-0.1.8-WoT-2.4.2.0-Setup.zip')
        self.assertEqual(bi.setup_archive_name({'version': '0.1.8-beta.1', 'gameVersion': '2.4.2.0'}),
                         'Driftkings-0.1.8-beta.1-WoT-2.4.2.0-Setup.zip')


class InventoryIntegrationTests(ReleaseRunFixture):
    def test_attachment_adds_the_archive_to_the_inventory_and_keeps_the_release_manifest(self):
        before = json.loads((self.output / 'release.json').read_text())
        setup = bi.attach_installer(self.output, self.setup_source)
        report = json.loads((self.output / 'build-report.json').read_text())
        archive = self.output / 'Driftkings-0.1.8-WoT-2.4.2.0-Setup.zip'
        self.assertEqual(report['setupArchive'], archive.name)
        self.assertEqual(report['artifacts'][archive.name]['sha256'], sha(archive))
        self.assertEqual(json.loads((self.output / 'release.json').read_text()), before)  # runtime manifest unchanged
        self.assertEqual(bi.verify_setup_archive(archive, setup), sha(setup))
        sums = dict(reversed(line.split('  ', 1)) for line in (self.output / 'SHA256SUMS.txt').read_text().splitlines())
        self.assertIn(archive.name, sums)

    def test_a_modified_archive_breaks_the_checksum_inventory(self):
        bi.attach_installer(self.output, self.setup_source)
        archive = self.output / 'Driftkings-0.1.8-WoT-2.4.2.0-Setup.zip'
        write(archive, b'changed after finalization')
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            compiler.verify_checksums(self.output)

    def test_development_builds_never_get_an_archive(self):
        report = json.loads((self.output / 'build-report.json').read_text())
        report['mode'] = 'dev'
        write(self.output / 'build-report.json', json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'Only a successful release build'):
            bi.attach_installer(self.output, self.setup_source)
        self.assertFalse(list(self.output.glob('*.zip')))


class CandidateLifecycleTests(ReleaseRunFixture):
    def test_staging_is_mutable_and_a_frozen_candidate_is_not(self):
        self.assertEqual(ps.candidate_state(self.output), ps.CANDIDATE_STAGING)
        write(self.output / '.promotion-build.json', '{}')
        self.assertEqual(ps.candidate_state(self.output), ps.CANDIDATE_FROZEN)
        with self.assertRaisesRegex(ValueError, 'frozen'):
            ps.require_mutable(self.output)

    def test_a_signature_alone_freezes_the_candidate(self):
        write(self.output / 'release.json.sig', b'sig')
        self.assertEqual(ps.candidate_state(self.output), ps.CANDIDATE_FROZEN)

    def sign_candidate(self, seed=bytes(range(32))):
        """Synthetic signature over the candidate; returns the trust list that verifies it, never a production key."""
        from build_tools import sign_release
        module = sign_release.load_signature()
        key = self.root / 'synthetic.key'
        write(key, seed.hex())
        names = sorted(p.name for p in self.output.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt')
        write(self.output / 'SHA256SUMS.txt', ''.join('%s  %s\n' % (sha(self.output / n), n) for n in names))
        sign_release.sign_folder(self.output, key, module)
        return types.SimpleNamespace(TRUSTED_KEYS=(module.public_key(seed).hex(),),
                                     SIGNATURE_ASSET=module.SIGNATURE_ASSET, verify_manifest=module.verify_manifest)

    def test_promotion_takes_only_a_signed_candidate_and_copies_it_once(self):
        from build_tools import sign_release
        with self.assertRaisesRegex(ValueError, 'stamped and signed'):
            compiler.promote_run(self.root, self.run)
        trusted = self.sign_candidate()
        with mock.patch.object(sign_release, 'load_signature', return_value=trusted):
            destination = compiler.promote_run(self.root, self.run)
            self.assertEqual(destination, self.root / 'build/releases/stable/0.1.8')
            self.assertEqual((destination / 'driftkings.wotmod').read_bytes(), WOTMOD)
            self.assertEqual(compiler.promote_run(self.root, self.run), destination)  # identical bytes: no replacement

    def test_a_build_stamp_alone_is_not_a_signature(self):
        from build_tools import sign_release
        write(self.output / '.promotion-build.json', '{}')
        names = sorted(p.name for p in self.output.iterdir() if p.is_file() and p.name not in
                       ('SHA256SUMS.txt', '.promotion-build.json'))
        write(self.output / 'SHA256SUMS.txt', ''.join('%s  %s\n' % (sha(self.output / n), n) for n in names))
        module = sign_release.load_signature()
        with mock.patch.object(sign_release, 'load_signature', return_value=module):
            with self.assertRaisesRegex(ValueError, 'Missing signature'):
                compiler.promote_run(self.root, self.run)
        self.assertFalse((self.root / 'build/releases').exists())

    def test_a_candidate_signed_by_another_key_is_not_promoted(self):
        from build_tools import sign_release
        self.sign_candidate()
        from build_tools import sign_release as module_owner
        other = types.SimpleNamespace(TRUSTED_KEYS=(sign_release.load_signature().public_key(bytes(range(1, 33))).hex(),),
                                      SIGNATURE_ASSET='release.json.sig',
                                      verify_manifest=sign_release.load_signature().verify_manifest)
        with mock.patch.object(sign_release, 'load_signature', return_value=other):
            with self.assertRaisesRegex(ValueError, 'trusted production key'):
                compiler.promote_run(self.root, self.run)

    def test_promotion_refuses_a_different_frozen_release(self):
        from build_tools import sign_release
        destination = self.root / 'build/releases/stable/0.1.8'
        write(destination / 'driftkings.wotmod', b'published bytes')
        trusted = self.sign_candidate()
        with mock.patch.object(sign_release, 'load_signature', return_value=trusted):
            with self.assertRaisesRegex(ValueError, 'Frozen release 0.1.8 already exists'):
                compiler.promote_run(self.root, self.run)
        self.assertEqual((destination / 'driftkings.wotmod').read_bytes(), b'published bytes')

    def test_a_run_outside_build_runs_cannot_be_promoted(self):
        outside = self.root / 'elsewhere' / RUN
        with self.assertRaisesRegex(ValueError, 'build/runs'):
            compiler.promote_run(self.root, outside)


class FullDigestBetaTests(unittest.TestCase):
    def gate(self, title):
        class Context(object):
            repository = 'owner/project'

            def query(self_inner, path, missing_ok=False):
                if 'promotion-gate.yml' in path:
                    return dict(workflow_runs=[dict(id=7, run_number=1, display_title=title, head_branch='main',
                                                    html_url='https://gate/7')])
                if path.endswith('/jobs'):
                    return dict(jobs=[dict(name=promotion.GATE_JOB, conclusion='success')])
                if path.endswith('/approvals'):
                    return [dict(state='approved', user=dict(login='maintainer'))]
                if '/environments/' in path:
                    return None
                raise AssertionError(path)
        return Context()

    def test_a_new_beta_is_approved_only_by_the_complete_digest(self):
        full, short = 'a' * 64, 'a' * 16
        approved = promotion.gate_title('1.2.3-beta.4', 'c' * 40, full)
        self.assertEqual(promotion.find_gate(self.gate(approved), '1.2.3-beta.4', 'c' * 40, short, False,
                                             title=approved)['approvedBy'], ['maintainer'])
        legacy = promotion.gate_title('1.2.3-beta.4', 'c' * 40, short)
        with self.assertRaisesRegex(ValueError, 'No approved'):
            promotion.find_gate(self.gate(legacy), '1.2.3-beta.4', 'c' * 40, short, False, title=approved)

    def test_historical_beta_keeps_its_abbreviated_title(self):
        short = 'a' * 16
        legacy = promotion.gate_title('0.1.7-beta.2', 'c' * 40, short)
        self.assertEqual(promotion.find_gate(self.gate(legacy), '0.1.7-beta.2', 'c' * 40, short, False)['approvedBy'],
                         ['maintainer'])

    def test_a_new_beta_check_rejects_an_abbreviated_digest(self):
        with self.assertRaisesRegex(ValueError, 'Invalid artifacts digest'):
            promotion.run_check(types.SimpleNamespace(), types.SimpleNamespace(
                beta='1.2.3-beta.4', stable=None, record=None, record_digest=None, commit='c' * 40, digest='a' * 16))


class InventoryAuthenticityTests(ReleaseRunFixture):
    def sign_inventory(self):
        from build_tools import sign_release
        seed = bytes(range(32))
        key = self.root / 'seed.key'
        write(key, seed.hex())
        compiler.write_checksums(self.output)
        sign_release.sign_folder(self.output, key)
        module = sign_release.load_signature()
        return module, [module.public_key(seed).hex()]

    def test_the_inventory_signature_verifies_and_covers_no_signature_file(self):
        from build_tools import publish_release
        module, keys = self.sign_inventory()
        sums = (self.output / 'SHA256SUMS.txt').read_bytes()
        module.verify_manifest(sums, (self.output / 'SHA256SUMS.txt.sig').read_bytes(), keys)
        self.assertNotIn(b'.sig', sums)
        trusted = types.SimpleNamespace(TRUSTED_KEYS=tuple(keys), verify_manifest=module.verify_manifest)
        self.assertEqual(publish_release.verify_inventory_signature(self.output, trusted), 'SHA256SUMS.txt.sig')

    def test_an_altered_inventory_is_rejected(self):
        module, keys = self.sign_inventory()
        write(self.output / 'SHA256SUMS.txt', (self.output / 'SHA256SUMS.txt').read_bytes() + b'\n')
        with self.assertRaises(ValueError):
            module.verify_manifest((self.output / 'SHA256SUMS.txt').read_bytes(),
                                   (self.output / 'SHA256SUMS.txt.sig').read_bytes(), keys)

    def test_an_inventory_that_covers_a_signature_is_refused(self):
        from build_tools import publish_release
        module, keys = self.sign_inventory()
        write(self.output / 'SHA256SUMS.txt', (self.output / 'SHA256SUMS.txt').read_bytes() +
              b'0' * 64 + b'  release.json.sig\n')
        trusted = types.SimpleNamespace(TRUSTED_KEYS=tuple(keys), verify_manifest=module.verify_manifest)
        with self.assertRaisesRegex(ValueError, 'must not cover signature files'):
            publish_release.verify_inventory_signature(self.output, trusted)


class DefaultsArchiveTests(unittest.TestCase):
    def test_the_defaults_archive_lives_only_inside_the_distribution(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / 'repo'
        package = Path(temp.name) / 'driftkings.wotmod'
        package.write_bytes(WOTMOD)
        candidate = Path(temp.name) / 'candidate'
        candidate.mkdir()
        compiler.write_distribution(root, {'game': {'version': '2.4.2.0'}}, {'defaults': [], 'dependencies': []},
                                    candidate, package, '0.1.8', 'stable')
        self.assertFalse((candidate / 'Driftkings-defaults.zip').exists())
        with zipfile.ZipFile(candidate / 'Driftkings-0.1.8-WoT-2.4.2.0.zip') as archive:
            self.assertIn('Driftkings-defaults.zip', archive.namelist())
            self.assertIn('mods/2.4.2.0/driftkings.wotmod', archive.namelist())


if __name__ == '__main__':
    unittest.main()
