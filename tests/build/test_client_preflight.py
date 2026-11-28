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

    def test_modern_995_identity_still_accepted(self):
        self.version(995, '2655094')
        self.manifest['game_version'].update(raw='v.2.4.2.0 Common Test #995', build=995, client_revision='2655094')
        self.save()
        (self.source / '.version_name').write_text('2.4.2.0 Common Test #995')
        self.assertEqual(self.check(), 'CT')

    def test_configured_source_label_accepted_for_996_without_manifest(self):
        (self.source / 'manifest.json').unlink()
        (self.source / '.version_name').write_text('2.4.2.5518')
        self.assertEqual(self.check(), 'CT')

    def test_configured_source_label_rejected_for_other_builds(self):
        (self.source / 'manifest.json').unlink()
        (self.source / '.version_name').write_text('2.4.2.5518')
        self.version(995, '2655094')
        with self.assertRaisesRegex(ValueError, 'bound to CT #996'):
            self.check()

    def test_old_5516_label_no_longer_accepted(self):
        (self.source / 'manifest.json').unlink()
        (self.source / '.version_name').write_text('2.4.2.5516')
        with self.assertRaises(ValueError):
            self.check()

    def test_configured_label_does_not_hide_a_contradictory_manifest(self):
        (self.source / '.version_name').write_text('2.4.2.5518')
        self.manifest['game_version']['client_revision'] = 'wrong'
        self.save()
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
        for name in ('2.4.2.0 Common Test #995', '2.4.2', '2.4.2.5516',
                     '2.4.2.0 Common Test #997'):
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


    def test_explicit_target_selection_and_legacy_inference(self):
        from unittest.mock import patch
        from build_tools import compiler

        with patch.object(compiler, 'source_client', wraps=compiler.source_client) as identify:
            target = compiler.resolve_target(ROOT, self.config, self.tools, 'ct996', 'dev')
            identify.assert_called_once_with(str(self.game), self.config)
        self.assertEqual(target['name'], 'ct996')
        self.assertEqual(target['identity']['build'], '996')
        self.assertIsNone(target['profile'])
        self.assertEqual(compiler.resolve_target(ROOT, self.config, self.tools, None, 'debug')['name'], 'ct996')

    def test_wrong_unknown_or_release_ct_target_is_rejected(self):
        from build_tools.compiler import resolve_target

        for name, mode, error in (
                ('unknown', 'dev', 'Unknown build target'),
                (None, 'dev', 'requires --target'),
                ('ct995', 'dev', 'does not match target'),
                ('ct996', 'release', 'cannot be used in release'),
                (None, 'release', 'cannot be used in release')):
            with self.subTest(name=name, mode=mode), self.assertRaisesRegex(ValueError, error):
                resolve_target(ROOT, self.config, self.tools, name, mode)

    def test_target_table_must_match_pinned_client_builds(self):
        from build_tools.compiler import validate_targets

        validate_targets(self.config)
        drifted = json.loads(json.dumps(self.config))
        drifted['targets']['na1010']['build'] = '998'
        with self.assertRaisesRegex(ValueError, 'does not match the pinned NA client build'):
            validate_targets(drifted)


class ProductionReferenceTests(unittest.TestCase):
    def setUp(self):
        from build_tools.validate_build_data import production_profile

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.source = Path(temp.name)
        self.config = json.loads((ROOT / 'build_data/build_config.json').read_text())
        self.identity = dict(realm='NA', build='1010', revision='2671446')
        self.profile = production_profile(ROOT, self.config, self.identity)
        self.python_path = self.profile['reference_python_lf'][0]
        for relative in self.profile['reference_sha256']:
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = b'\xef\xbb\xbf# exact reference\nVALUE = 1\n'
            if relative == 'sources/version.xml':
                raw = (b'<root><version>v.2.4.2.0 #1010</version><meta><realm>NA</realm>'
                       b'<client>2671446</client></meta></root>\n')
            elif relative == 'sources/paths.xml':
                raw = b'<paths/>\n'
            target.write_bytes(raw)
            self.profile['reference_sha256'][relative] = hashlib.sha256(raw).hexdigest()
        (self.source / '.version_name').write_text('2.4.2.5537')

    def verify(self):
        from build_tools.compiler import check_production_reference

        return check_production_reference(
            self.config, {'reference_root': str(self.source)}, self.identity, self.profile)

    def test_reviewed_lf_and_crlf_compare_equal_with_distinct_raw_provenance(self):
        path = self.source / self.python_path
        lf = self.verify()[self.python_path]
        path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
        crlf = self.verify()[self.python_path]
        self.assertEqual(crlf['canonical_sha256'], lf['canonical_sha256'])
        self.assertNotEqual(crlf['raw_sha256'], lf['raw_sha256'])
        self.assertEqual(crlf['raw_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_substantive_change_and_bare_cr_are_rejected(self):
        path = self.source / self.python_path
        original = path.read_bytes()
        for changed, message in (
                (original.replace(b'VALUE = 1', b'VALUE = 2'), 'source hash mismatch'),
                (original.replace(b'\n', b'\r'), 'Bare CR'),
                (original.removeprefix(b'\xef\xbb\xbf'), 'source hash mismatch'),
                (original.rstrip(b'\n'), 'source hash mismatch')):
            with self.subTest(message=message):
                path.write_bytes(changed)
                with self.assertRaisesRegex(ValueError, message):
                    self.verify()

    def test_xml_and_unlisted_python_still_use_raw_hashes(self):
        relative = 'sources/paths.xml'
        path = self.source / relative
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'\n', b'\r\n'))
        with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
            self.verify()
        self.profile['reference_python_lf'].append(relative)
        with self.assertRaisesRegex(ValueError, 'limited to reviewed Python'):
            self.verify()
        self.profile['reference_python_lf'] = []
        path.write_bytes(raw)
        path = self.source / self.python_path
        path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
        with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
            self.verify()

    def test_production_swc_pin_still_requires_exact_binary_bytes(self):
        from build_tools.compiler import production_generators

        binary = self.source / 'test.swc'
        raw = b'PK\x00\x01\r\n'
        binary.write_bytes(raw)
        (self.source / 'flash.json').write_text(json.dumps(dict(
            game_version='2.4.2.0', source_version='2.4.2.5537',
            libraries=[dict(name='test.swc', sha256=hashlib.sha256(raw).hexdigest())])))
        self.config['generators'] = {'flash': {'kind': 'flash'}}
        self.profile['generators'] = {'flash': 'flash.json'}
        production_generators(self.source, self.config, self.profile, self.identity)
        binary.write_bytes(raw.replace(b'\r\n', b'\n'))
        with self.assertRaisesRegex(ValueError, 'Flash library hash mismatch'):
            production_generators(self.source, self.config, self.profile, self.identity)
