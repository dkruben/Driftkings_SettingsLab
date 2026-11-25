# -*- coding: utf-8 -*-
"""Flash input acquisition: manifest and identity validation, verified extraction, cache reuse, recovery,
safe paths, read-only client access, tree installation and the absence of network access.

Every test uses synthetic client folders and manifests in a temporary directory. The one test that touches a real
installed client runs only when DRIFTKINGS_NA_CLIENT names a client folder, and it writes to a temporary cache.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import acquire_flash_inputs as acq  # noqa: E402

REAL_SWC = acq.SWC_DIR
REAL_MANIFEST = REAL_SWC / 'manifest.na999.json'
FROZEN_REPORT = ROOT / 'build' / 'releases' / 'beta' / '0.1.7-beta.2' / 'build-report.json'
PAYLOAD = {'na999-a.swc': b'A' * 4096, 'na999-b.swc': b'B' * 2048}
ENTRY = {'na999-a.swc': 'gui/flash/swc/a-1.0-SNAPSHOT.swc', 'na999-b.swc': 'gui/flash/swc/b.swc'}
PACKAGE = {'na999-a.swc': 'gui-part1.pkg', 'na999-b.swc': 'gui-part2.pkg'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_client(root, build='999', revision='2664941', realm='NA', version='2.4.2.0'):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'version.xml').write_text(
        '<version.xml>\n\t<version> v.%s #%s </version>\n\t<meta>\n\t\t<client> %s </client>\n'
        '\t\t<realm> %s </realm>\n\t</meta>\n</version.xml>\n' % (version, build, revision, realm), encoding='utf-8')
    packages = root / 'res' / 'packages'
    packages.mkdir(parents=True, exist_ok=True)
    for name, resource in ENTRY.items():
        package = packages / PACKAGE[name]
        mode = 'a' if package.exists() else 'w'
        with zipfile.ZipFile(str(package), mode) as archive:
            archive.writestr(resource, PAYLOAD[name])
    return root


def write_manifest(path, libraries=None, **overrides):
    document = {'source_version': '2.4.2.5523', 'game_version': '2.4.2.0', 'realm': 'NA', 'build': '999',
                'revision': '2664941',
                'libraries': libraries if libraries is not None else [
                    {'name': name, 'sha256': sha(PAYLOAD[name]), 'package': PACKAGE[name], 'resource': ENTRY[name]}
                    for name in sorted(PAYLOAD)]}
    document.update(overrides)
    path.write_text(json.dumps(document, indent=2), encoding='utf-8')
    return path


def snapshot(root):
    result = {}
    for base, _, files in os.walk(str(root)):
        for name in files:
            full = os.path.join(base, name)
            stat = os.stat(full)
            with open(full, 'rb') as handle:
                result[os.path.relpath(full, str(root))] = (stat.st_size, stat.st_mtime_ns, sha(handle.read()))
    return result


class FlashAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='flash-acq-'))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.saved = (acq.BUILD_DIR, acq.SWC_DIR)
        self.addCleanup(self._restore)
        acq.BUILD_DIR = self.tmp / 'build'
        acq.SWC_DIR = self.tmp / 'swc'
        self.client = write_client(self.tmp / 'client')
        self.manifest = write_manifest(self.tmp / 'manifest.na999.json')
        self.cache = self.tmp / 'build' / 'cache' / 'flash_inputs'

    def _restore(self):
        acq.BUILD_DIR, acq.SWC_DIR = self.saved

    def run_acquire(self, **kwargs):
        options = dict(manifest_path=self.manifest, cache_root=self.cache, client_root=self.client,
                       realm='NA', build='999')
        options.update(kwargs)
        return acq.acquire(**options)

    def libs(self):
        return self.cache / 'na-999-2664941' / 'libs'

    # Manifest parsing

    def test_production_manifest_parses(self):
        parsed = acq.load_manifest(REAL_MANIFEST)
        self.assertEqual((parsed['realm'], parsed['build'], parsed['revision'], parsed['game_version']),
                         ('NA', '999', '2664941', '2.4.2.0'))
        self.assertEqual(len(parsed['libraries']), 8)
        self.assertEqual(len(set(item['name'] for item in parsed['libraries'])), 8)
        for item in parsed['libraries']:
            self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')
            self.assertTrue(item['resource'].startswith('gui/flash/swc/'))

    def test_manifest_without_required_keys_is_rejected(self):
        path = self.tmp / 'bad.json'
        path.write_text(json.dumps({'realm': 'NA'}), encoding='utf-8')
        with self.assertRaisesRegex(acq.AcquisitionError, 'lacks'):
            acq.load_manifest(path)

    def test_malformed_pins_and_names_are_rejected(self):
        good = {'name': 'na999-a.swc', 'sha256': sha(b'x'), 'package': 'gui-part1.pkg', 'resource': ENTRY['na999-a.swc']}
        cases = [
            ('sha256', dict(good, sha256='ABC')),
            ('package', dict(good, package='../gui-part1.pkg')),
            ('name', dict(good, name='../evil.swc')),
            ('name', dict(good, name='sub/evil.swc')),
            ('resource', dict(good, resource='gui/../../evil.swc')),
            ('resource', dict(good, resource='/gui/flash/swc/a.swc')),
            ('resource', dict(good, resource='gui\\flash\\swc\\a.swc')),
            ('resource', dict(good, resource='other/a.swc')),
        ]
        for label, item in cases:
            path = write_manifest(self.tmp / ('m-%s-%d.json' % (label, len(str(item)))), libraries=[item])
            with self.assertRaises(acq.AcquisitionError, msg=str(item)):
                acq.load_manifest(path)

    def test_duplicate_library_names_are_rejected(self):
        item = {'name': 'na999-a.swc', 'sha256': sha(b'x'), 'package': 'gui-part1.pkg', 'resource': ENTRY['na999-a.swc']}
        path = write_manifest(self.tmp / 'dup.json', libraries=[item, dict(item)])
        with self.assertRaisesRegex(acq.AcquisitionError, 'duplicate'):
            acq.load_manifest(path)

    def test_ct_style_manifest_without_client_pins_is_rejected(self):
        path = write_manifest(self.tmp / 'ct.json', libraries=[{'name': 'battle.swc', 'sha256': sha(b'x')}])
        with self.assertRaisesRegex(acq.AcquisitionError, 'client pins are required'):
            acq.load_manifest(path)

    # Realm and identity

    def test_excluded_realms_are_rejected_everywhere(self):
        for realm in ('RU', 'PT_RU', 'LESTA'):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(acq.main(['--realm', realm, '--build', '1', '--check-cache']), 2)
            path = write_manifest(self.tmp / ('r-%s.json' % realm), realm=realm)
            with self.assertRaisesRegex(acq.AcquisitionError, 'excluded'):
                acq.load_manifest(path)

    def test_unknown_realm_is_rejected(self):
        path = write_manifest(self.tmp / 'x.json', realm='XX')
        with self.assertRaisesRegex(acq.AcquisitionError, 'unsupported realm'):
            acq.load_manifest(path)

    def test_client_identity_must_match_the_manifest(self):
        for build, realm, label in (('998', 'NA', 'build'), ('999', 'EU', 'realm')):
            client = write_client(self.tmp / ('client-' + label), build=build, realm=realm)
            report = self.run_acquire(client_root=client)
            self.assertEqual(report['status'], 'failed')
            self.assertIn(label, ' '.join(report['errors']))
            self.assertFalse(self.libs().exists() and any(self.libs().iterdir()), 'nothing may be written')

    def test_requested_identity_must_match_the_manifest(self):
        report = self.run_acquire(build='998')
        self.assertEqual(report['status'], 'failed')
        self.assertIn('requested build', report['errors'][0])

    # Successful acquisition and report

    def test_successful_acquisition_writes_verified_cache_and_report(self):
        report = self.run_acquire()
        self.assertEqual(report['status'], 'ok', report['errors'])
        self.assertEqual(sorted(item['name'] for item in report['libraries']), sorted(PAYLOAD))
        for item in report['libraries']:
            self.assertEqual(item['status'], 'extracted')
            self.assertEqual(item['actual_sha256'], item['expected_sha256'])
            self.assertEqual((self.libs() / item['name']).read_bytes(), PAYLOAD[item['name']])
        report_file = json.loads((self.cache / 'na-999-2664941' / 'acquisition-report.json').read_text(encoding='utf-8'))
        self.assertEqual(report_file['status'], 'ok')
        self.assertEqual(report_file['client']['build'], '999')
        self.assertEqual(sorted(report_file['client']['packages']), sorted(PACKAGE.values()))

    def test_report_records_no_absolute_paths(self):
        report = self.run_acquire()
        text = json.dumps(report)
        self.assertNotIn(str(self.tmp), text)
        self.assertNotIn(str(self.client), text)

    # Rejections (nothing is written in any of them)

    def test_missing_package_is_rejected_without_writes(self):
        (self.client / 'res' / 'packages' / 'gui-part2.pkg').unlink()
        report = self.run_acquire()
        self.assertEqual(report['status'], 'failed')
        self.assertIn('missing client package: gui-part2.pkg', report['errors'][0])
        self.assertFalse(self.libs().exists() and any(p.name.startswith('na999') for p in self.libs().iterdir()))

    def test_missing_resource_is_rejected_without_writes(self):
        libraries = [{'name': 'na999-a.swc', 'sha256': sha(PAYLOAD['na999-a.swc']), 'package': 'gui-part1.pkg',
                      'resource': 'gui/flash/swc/absent.swc'}]
        self.manifest = write_manifest(self.tmp / 'missing-resource.json', libraries=libraries)
        report = self.run_acquire()
        self.assertEqual(report['status'], 'failed')
        self.assertIn('missing resource gui/flash/swc/absent.swc', report['errors'][0])
        self.assertFalse(self.libs().exists() and any(self.libs().iterdir()))

    def test_hash_mismatch_is_rejected_and_nothing_is_written(self):
        libraries = [{'name': 'na999-a.swc', 'sha256': sha(b'different'), 'package': 'gui-part1.pkg',
                      'resource': ENTRY['na999-a.swc']},
                     {'name': 'na999-b.swc', 'sha256': sha(PAYLOAD['na999-b.swc']), 'package': 'gui-part2.pkg',
                      'resource': ENTRY['na999-b.swc']}]
        self.manifest = write_manifest(self.tmp / 'mismatch.json', libraries=libraries)
        report = self.run_acquire()
        self.assertEqual(report['status'], 'failed')
        self.assertIn('hash mismatch for na999-a.swc', report['errors'][0])
        self.assertEqual([item['status'] for item in report['libraries']], ['hash-mismatch'])
        self.assertFalse(self.libs().exists() and any(p.name == 'na999-b.swc' for p in self.libs().iterdir()),
                         'a valid library must not be written when another one fails')

    def test_unexpected_cache_file_is_rejected_and_kept(self):
        self.libs().mkdir(parents=True)
        extra = self.libs() / 'intruder.swc'
        extra.write_bytes(b'not in the manifest')
        report = self.run_acquire()
        self.assertEqual(report['status'], 'failed')
        self.assertIn('unexpected files', report['errors'][0])
        self.assertTrue(extra.is_file(), 'unexpected files are reported, never deleted')

    # Cache reuse and recovery

    def test_repeated_run_reuses_the_cache_without_opening_packages(self):
        self.assertEqual(self.run_acquire()['status'], 'ok')
        for name in PACKAGE.values():
            (self.client / 'res' / 'packages' / name).unlink()
        report = self.run_acquire(client_root=None)
        self.assertEqual(report['status'], 'ok', report['errors'])
        self.assertEqual([item['status'] for item in report['libraries']], ['cache-hit', 'cache-hit'])

    def test_incomplete_cache_without_a_client_is_rejected(self):
        report = self.run_acquire(client_root=None)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('no client given', report['errors'][0])

    def test_corrupt_cache_file_is_quarantined_and_reacquired(self):
        self.assertEqual(self.run_acquire()['status'], 'ok')
        target = self.libs() / 'na999-a.swc'
        target.write_bytes(b'truncated')
        report = self.run_acquire()
        self.assertEqual(report['status'], 'ok', report['errors'])
        states = dict((item['name'], item['status']) for item in report['libraries'])
        self.assertEqual(states['na999-a.swc'], 'quarantined-and-reacquired')
        self.assertEqual(target.read_bytes(), PAYLOAD['na999-a.swc'])
        quarantined = [p for p in self.libs().iterdir() if p.name.startswith('.quarantine-')]
        self.assertEqual([p.read_bytes() for p in quarantined], [b'truncated'], 'the bad copy is kept')

    def test_interrupted_write_leftovers_are_removed_at_the_next_run(self):
        self.libs().mkdir(parents=True)
        leftover = self.libs() / '.partial-99999-na999-a.swc'
        leftover.write_bytes(b'half written')
        report = self.run_acquire()
        self.assertEqual(report['status'], 'ok', report['errors'])
        self.assertFalse(leftover.exists())

    # Safe paths

    def test_cache_outside_the_build_directory_is_rejected(self):
        outside = self.tmp / 'elsewhere'
        report = self.run_acquire(cache_root=outside)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('git-ignored build directory', report['errors'][0])
        self.assertFalse(outside.exists())

    def test_cache_inside_tracked_sources_is_rejected(self):
        with self.assertRaises(acq.AcquisitionError):
            acq.safe_cache_root(acq.BUILD_DIR.parent / 'flash_source')

    # Read-only client access

    def test_client_folder_is_unchanged_by_acquisition(self):
        before = snapshot(self.client)
        self.assertEqual(self.run_acquire()['status'], 'ok')
        self.assertEqual(snapshot(self.client), before)

    # Tree installation

    def test_install_tree_places_absent_files_and_keeps_identical_ones(self):
        acq.SWC_DIR.mkdir(parents=True)
        (acq.SWC_DIR / 'na999-a.swc').write_bytes(PAYLOAD['na999-a.swc'])
        report = self.run_acquire(install_tree=True)
        self.assertEqual(report['status'], 'ok', report['errors'])
        installs = dict((item['name'], item['install']) for item in report['libraries'])
        self.assertEqual(installs, {'na999-a.swc': 'already-present-identical', 'na999-b.swc': 'installed'})
        self.assertEqual((acq.SWC_DIR / 'na999-b.swc').read_bytes(), PAYLOAD['na999-b.swc'])

    def test_install_tree_refuses_to_overwrite_a_differing_file(self):
        acq.SWC_DIR.mkdir(parents=True)
        (acq.SWC_DIR / 'na999-a.swc').write_bytes(b'someone else')
        report = self.run_acquire(install_tree=True)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('refusing to overwrite', report['errors'][0])
        self.assertEqual((acq.SWC_DIR / 'na999-a.swc').read_bytes(), b'someone else')
        self.assertFalse((acq.SWC_DIR / 'na999-b.swc').exists())

    # Offline check and network

    def test_check_cache_needs_no_client(self):
        self.assertEqual(self.run_acquire()['status'], 'ok')
        result = acq.check_cache(self.manifest, self.cache)
        self.assertEqual(result['status'], 'ok', result['errors'])
        (self.libs() / 'na999-b.swc').unlink()
        self.assertEqual(acq.check_cache(self.manifest, self.cache)['status'], 'failed')

    def test_tool_has_no_network_access(self):
        source = Path(acq.__file__).read_text(encoding='utf-8')
        for token in ('urllib', 'http.client', 'import socket', 'requests', 'ftplib', 'subprocess', 'urlopen'):
            self.assertNotIn(token, source, token)

    # Real installed client (optional)

    @unittest.skipUnless(os.environ.get('DRIFTKINGS_NA_CLIENT'),
                         'set DRIFTKINGS_NA_CLIENT to an installed NA client folder to run this check')
    def test_installed_na_client_yields_the_frozen_inputs(self):
        client = Path(os.environ['DRIFTKINGS_NA_CLIENT'])
        before = snapshot(client)
        report = acq.acquire(REAL_MANIFEST, self.cache, client_root=client, realm='NA', build='999')
        self.assertEqual(report['status'], 'ok', report['errors'])
        self.assertEqual(len(report['libraries']), 8)
        self.assertEqual(snapshot(client), before, 'the client must not change')
        if FROZEN_REPORT.is_file():
            frozen = json.loads(FROZEN_REPORT.read_text(encoding='utf-8'))['inputs']
            for item in report['libraries']:
                key = 'flash_source/shared/swc/' + item['name']
                self.assertEqual(item['actual_sha256'], frozen[key], item['name'])


if __name__ == '__main__':
    unittest.main()
