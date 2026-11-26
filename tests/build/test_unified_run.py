"""Unified run layout: publication is a mirror of verified output, frozen releases are protected, and
distribution checks are separate from WOTMOD verification."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from build_tools import compiler as c
from build_tools.build_installer import release_directory


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'build').mkdir()
        self.config = dict(package=dict(output='build/unified/driftkings.wotmod'),
                           python=dict(archive_root='res/scripts/client', staging_root='build/staging/res/scripts/client'))
        self.run = self.root / 'build/runs/run-1'
        self.output = self.run / 'output'
        self.output.mkdir(parents=True)
        write(self.output / 'driftkings.wotmod', b'package-a')
        write(self.output / 'release.json', b'{"schema": 2}')
        write(self.run / 'evidence/build-report.json', b'{"status": "success"}')

    def publish(self, destination, release):
        c.publish_local(self.root, self.output, destination, self.config, {}, self.run / 'workspace/compiled',
                        dict(python=[]), release=release)

    def test_run_output_is_mirrored_and_never_moved(self):
        destination = self.root / 'build/debug/beta/0.1.8-beta.1'
        self.publish(destination, release=False)
        self.assertEqual((self.output / 'driftkings.wotmod').read_bytes(), b'package-a')
        self.assertEqual((destination / 'driftkings.wotmod').read_bytes(), b'package-a')
        self.assertEqual((self.root / 'build/unified/driftkings.wotmod').read_bytes(), b'package-a')

    def test_development_replacement_keeps_previous_directory(self):
        destination = self.root / 'build/debug/beta/0.1.8-beta.1'
        write(destination / 'driftkings.wotmod', b'older')
        self.publish(destination, release=False)
        self.assertEqual((destination / 'driftkings.wotmod').read_bytes(), b'package-a')
        self.assertTrue(list((self.root / 'build/previous').glob('0.1.8-beta.1-*/driftkings.wotmod')))

    def test_frozen_release_with_different_bytes_is_refused(self):
        destination = self.root / 'build/releases/stable/0.1.7'
        write(destination / 'driftkings.wotmod', b'published')
        write(destination / 'release.json', b'{"schema": 2}')
        with self.assertRaisesRegex(ValueError, 'Frozen release 0.1.7 already exists'):
            self.publish(destination, release=True)
        self.assertEqual((destination / 'driftkings.wotmod').read_bytes(), b'published')
        self.assertFalse((self.root / 'build/unified/driftkings.wotmod').exists())

    def test_frozen_release_with_extra_attested_files_is_refused(self):
        destination = self.root / 'build/releases/stable/0.1.7'
        write(destination / 'driftkings.wotmod', b'package-a')
        write(destination / 'release.json', b'{"schema": 2}')
        write(destination / '.official-build-attestation.json', b'{"attested": true}')
        with self.assertRaisesRegex(ValueError, 'Frozen release 0.1.7 already exists'):
            self.publish(destination, release=True)
        self.assertEqual((destination / '.official-build-attestation.json').read_bytes(), b'{"attested": true}')

    def test_identical_frozen_release_is_reused_despite_new_report(self):
        destination = self.root / 'build/releases/stable/0.1.8'
        write(destination / 'driftkings.wotmod', b'package-a')
        write(destination / 'release.json', b'{"schema": 2}')
        write(destination / 'build-report.json', b'older report')
        self.publish(destination, release=True)
        self.assertEqual((destination / 'build-report.json').read_bytes(), b'older report')
        self.assertEqual((self.root / 'build/unified/driftkings.wotmod').read_bytes(), b'package-a')


class DistributionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name) / 'output'
        self.folder.mkdir()
        self.package = self.folder / 'driftkings.wotmod'
        self.package.write_bytes(b'package-a')
        self.manifest = dict(file='driftkings.wotmod', size=9, sha256=c.sha(self.package), gameVersion='2.4.2.0')
        with zipfile.ZipFile(self.folder / 'Driftkings-0.1.8-WoT-2.4.2.0.zip', 'w') as archive:
            archive.writestr('mods/2.4.2.0/driftkings.wotmod', b'package-a')
            archive.writestr('Driftkings-defaults.zip', b'defaults')
            archive.writestr('INSTALL.txt', b'install')

    def test_distribution_passes_when_manifest_and_zip_match(self):
        self.assertEqual(c.verify_distribution(self.folder, self.package, self.manifest, '0.1.8')['status'], 'passed')

    def test_manifest_must_describe_the_verified_wotmod(self):
        self.manifest['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'does not describe the verified WOTMOD'):
            c.verify_distribution(self.folder, self.package, self.manifest, '0.1.8')

    def test_distribution_zip_must_contain_the_same_package(self):
        with zipfile.ZipFile(self.folder / 'Driftkings-0.1.8-WoT-2.4.2.0.zip', 'w') as archive:
            archive.writestr('mods/2.4.2.0/driftkings.wotmod', b'other')
            archive.writestr('Driftkings-defaults.zip', b'defaults')
            archive.writestr('INSTALL.txt', b'install')
        with self.assertRaisesRegex(ValueError, 'differs from the verified package'):
            c.verify_distribution(self.folder, self.package, self.manifest, '0.1.8')

    def test_checksums_detect_later_modification(self):
        write(self.folder / 'release.json', b'{}')
        c.write_checksums(self.folder)
        c.verify_checksums(self.folder)
        write(self.folder / 'release.json', b'{"changed": true}')
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch: release.json'):
            c.verify_checksums(self.folder)


class InstallerPathTests(unittest.TestCase):
    def test_run_directory_resolves_to_its_release_output(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        run = Path(temp.name) / 'run-1'
        write(run / 'output/release.json', json.dumps({}).encode())
        self.assertEqual(release_directory(run), (run / 'output').resolve())
        self.assertEqual(release_directory(run / 'output'), (run / 'output').resolve())


if __name__ == '__main__':
    unittest.main()
