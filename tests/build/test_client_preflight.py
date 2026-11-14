"""CT identity checks only: never invoke compilation or write build outputs."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.compiler import CT_REFERENCE_FILES, check_client
from build_tools.validate_build_data import apply_patch_set


class ClientPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game, self.source = self.root / 'game', self.root / 'source'
        self.game.mkdir()
        self.source.mkdir()
        self.config = json.loads((ROOT / 'build_data/build_config.json').read_text())
        self.tools = dict(game_root=str(self.game), reference_root=str(self.source))
        self.version(996, '2660091')
        for directory in ('sources', 'sources_as', 'sources_gameface', '__stubs'):
            (self.source / directory).mkdir()
        self.manifest = dict(schema=1, realm='CT', consistent=True, version_name='2.4.2.0 Common Test',
                             game_version=dict(raw='v.2.4.2.0 Common Test #996', number='2.4.2.0', suffix='Common Test',
                                               build=996, client_revision='2660091', realm='CT'),
                             entries={})
        for relative in CT_REFERENCE_FILES:
            target = self.source / 'sources/res/scripts/client' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'# fixture contract\n')
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            self.manifest['entries']['res/scripts/client/' + relative[:-3] + '.pyc'] = dict(
                sha256=digest, decompiled=dict(status='success', input_sha256=digest,
                                              output=target.relative_to(self.source).as_posix(), sha256=digest))
        (self.source / '.version_name').write_text('2.4.2.0 Common Test #996')
        self.save()

    def version(self, build, revision, realm='CT'):
        (self.game / 'version.xml').write_text(
            '<root><version>v.2.4.2.0 Common Test #%s</version><meta><realm>%s</realm>'
            '<client>%s</client></meta></root>' % (build, realm, revision))

    def save(self):
        (self.source / 'manifest.json').write_text(json.dumps(self.manifest))

    def check(self):
        return check_client(ROOT, self.config, self.tools)

    def test_accepts_996_and_ignores_historical_reports(self):
        (self.source / 'README.md').write_text('Common Test #995')
        (self.source / 'report.json').write_text('{"game_version":{"build":995}}')
        self.assertEqual(self.check(), 'CT')

    def test_preserves_995_modern_and_exact_legacy_contract(self):
        self.version(995, '2655094')
        self.manifest['game_version'].update(raw='v.2.4.2.0 Common Test #995', build=995, client_revision='2655094')
        self.save()
        (self.source / '.version_name').write_text('2.4.2.0 Common Test #995')
        self.assertEqual(self.check(), 'CT')
        (self.source / 'manifest.json').unlink()
        (self.source / '.version_name').write_text('2.4.2.5516')
        self.assertEqual(self.check(), 'CT')

    def test_legacy_label_does_not_hide_a_contradictory_manifest(self):
        self.version(995, '2655094')
        (self.source / '.version_name').write_text('2.4.2.5516')
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            self.check()

    def test_wrong_installed_build_revision_version_or_realm_rejected(self):
        for build, revision, realm in [(997, '2660091', 'CT'), (996, 'wrong', 'CT'),
                                       (996, '2660091', 'EU')]:
            with self.subTest(build=build, revision=revision, realm=realm):
                self.version(build, revision, realm)
                with self.assertRaises(ValueError):
                    self.check()
        self.version(996, '2660091')
        path = self.game / 'version.xml'
        path.write_text(path.read_text().replace('2.4.2.0', '2.4.3.0'))
        with self.assertRaises(ValueError):
            self.check()

    def test_wrong_unknown_or_legacy_reference_cannot_claim_996(self):
        for name in ('2.4.2.0 Common Test #995', '2.4.2', '2.4.2.5518',
                     '2.4.2.5516', '2.4.2.0 Common Test #997'):
            with self.subTest(name=name):
                (self.source / '.version_name').write_text(name)
                with self.assertRaises(ValueError):
                    self.check()

    def test_conflicting_identity_metadata_rejected(self):
        mutations = [('realm', 'EU'), ('build', 995), ('client_revision', '2655094'),
                     ('number', '2.4.3.0'), ('suffix', 'Production'), ('build', True),
                     ('raw', 'v.2.4.2.0 Common Test #995')]
        original = copy.deepcopy(self.manifest)
        for key, value in mutations:
            with self.subTest(key=key):
                self.manifest = copy.deepcopy(original)
                self.manifest['game_version'][key] = value
                self.save()
                with self.assertRaises(ValueError):
                    self.check()
        self.manifest = copy.deepcopy(original)
        self.manifest['consistent'] = False
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_incomplete_root_or_manifest_rejected(self):
        manifest = self.source / 'manifest.json'
        raw = manifest.read_bytes()
        manifest.unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.check()
        manifest.write_bytes(raw)
        (self.source / 'sources_as').rmdir()
        with self.assertRaises(ValueError):
            self.check()
        self.version(995, '2655094')
        manifest.unlink()
        (self.source / '.version_name').write_text('2.4.2.5516')
        (self.source / 'sources/res/scripts/client' / CT_REFERENCE_FILES[0]).unlink()
        with self.assertRaises(ValueError):
            self.check()

    def test_tampered_missing_or_wrong_provenance_file_rejected(self):
        relative = CT_REFERENCE_FILES[0]
        target = self.source / 'sources/res/scripts/client' / relative
        raw = target.read_bytes()
        target.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.check()
        target.unlink()
        with self.assertRaises(ValueError):
            self.check()
        target.write_bytes(raw)
        key = 'res/scripts/client/' + relative[:-3] + '.pyc'
        self.manifest['entries'][key]['decompiled']['input_sha256'] = 'wrong'
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_independent_resource_hash_guard_still_rejects_wrong_bundle(self):
        self.assertEqual(self.check(), 'CT')
        patch = dict(source_sha256='0' * 64, output_sha256='0' * 64, operations=[])
        with self.assertRaisesRegex(ValueError, 'bundle hash'):
            apply_patch_set(b'wrong bundle', patch)
