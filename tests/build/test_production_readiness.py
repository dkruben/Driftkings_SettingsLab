"""Fail closed on source identity and keep research out of distributions."""
import tempfile
import unittest
from pathlib import Path

from build_tools.validate_build_data import (ROOT, build_plan, production_profile, production_realms,
                                             read_json, resolved_production_profile, source_client)


class ProductionReadinessTests(unittest.TestCase):
    def setUp(self):
        self.config = read_json(ROOT / 'build_data/build_config.json')
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def identify(self, realm, version, revision):
        (self.root / 'version.xml').write_text(
            '<root><version>%s</version><meta><client>%s</client><realm>%s</realm></meta></root>'
            % (version, revision, realm))
        return source_client(self.root, self.config)

    def test_identity_distinguishes_client_builds_and_revisions(self):
        for realm, build in [('NA', '1010'), ('EU', '1007'), ('ASIA', '1006'), ('CN', '1005')]:
            identity = self.identify(realm, 'v.2.4.2.0 #' + build, '2671446')
            self.assertEqual(identity, dict(realm=realm, build=build, revision='2671446'))
            with self.assertRaisesRegex(ValueError, 'version/build/revision mismatch'):
                self.identify(realm, 'v.2.4.2.0 #' + build, '2660091')
        # The outdated EU client (2.4.1.1 #993) is refused by its version, not by a missing pin.
        with self.assertRaisesRegex(ValueError, 'version/build/revision mismatch for EU'):
            self.identify('EU', 'v.2.4.1.1 #993', '2653317')
        # The superseded EU 1000 build of the NA999 era is no longer a production identity.
        with self.assertRaisesRegex(ValueError, 'version/build/revision mismatch for EU'):
            self.identify('EU', 'v.2.4.2.0 #1000', '2664941')

    def test_ct_can_be_identified_but_cannot_be_a_production_source(self):
        identity = self.identify('CT', 'v.2.4.2.0 Common Test #996', '2660091')
        with self.assertRaisesRegex(ValueError, 'pinned production client'):
            production_profile(self.root, self.config, identity)

    def test_unreviewed_profile_is_blocked_and_realms_use_profile_evidence(self):
        identity = self.identify('NA', 'v.2.4.2.0 #1010', '2671446')
        self.config['reference']['production_profiles'].pop('NA')
        with self.assertRaisesRegex(ValueError, 'Production resources are not verified'):
            production_profile(self.root, self.config, identity)
        (self.root / 'fixture.md').write_text('Test evidence')
        self.config['reference']['production_profiles']['NA'] = {
            'realm_evidence': {'NA': 'fixture.md', 'ASIA': 'fixture.md'}}
        report = dict(realm='NA', source_client=identity, runtime_realms=['ASIA', 'NA'])
        self.assertEqual(production_realms(self.root, self.config, report), ['ASIA', 'NA'])
        report['runtime_realms'].append('CN')
        with self.assertRaisesRegex(ValueError, 'realm evidence mismatch'):
            production_realms(self.root, self.config, report)

    def test_eu_shares_the_reviewed_na_pins_and_waits_for_its_own_evidence(self):
        identity = self.identify('EU', 'v.2.4.2.0 #1007', '2671446')
        self.assertEqual(identity, dict(realm='EU', build='1007', revision='2671446'))
        profile = resolved_production_profile(self.config, 'EU')
        self.assertEqual(profile['pinned_identity']['realm'], 'NA')
        self.assertEqual(profile['reference_sha256']['sources/version.xml'],
                         '7ea45ea36d2657fdad208d53ae5e3fe9e39f33751bafd5ac64c8b683af5dbbc3')
        na_profile = self.config['reference']['production_profiles']['NA']
        self.assertNotEqual(na_profile['reference_sha256']['sources/version.xml'],
                            profile['reference_sha256']['sources/version.xml'])
        # Shared native pins are inherited; the EU evidence is technical only, and no owner approval is implied.
        self.assertIn('EU', profile['realm_evidence'])
        self.assertEqual(production_profile(ROOT, self.config, identity)['pinned_identity']['build'], '1010')
        self.config['reference']['production_profiles']['NA']['realm_evidence'].pop('EU')
        with self.assertRaisesRegex(ValueError, 'Owner realm evidence is missing for EU #1007'):
            production_profile(ROOT, self.config, identity)
        with self.assertRaisesRegex(ValueError, 'version/build/revision mismatch'):
            self.identify('EU', 'v.2.4.2.0 #1007', '2660091')

    def test_asia_and_cn_stay_unverified_without_their_own_profiles(self):
        for realm, build in [('ASIA', '1006'), ('CN', '1005')]:
            identity = self.identify(realm, 'v.2.4.2.0 #' + build, '2671446')
            with self.assertRaisesRegex(ValueError, 'Production resources are not verified'):
                production_profile(ROOT, self.config, identity)

    def test_alias_is_resolved_only_against_a_reviewed_profile(self):
        profiles = self.config['reference']['production_profiles']
        profiles['EU'] = {'alias_of': 'ASIA'}
        with self.assertRaisesRegex(ValueError, 'not a reviewed profile'):
            resolved_production_profile(self.config, 'EU')
        profiles['EU'] = {'alias_of': 'NA', 'generators': {}}
        with self.assertRaisesRegex(ValueError, 'unsupported fields'):
            resolved_production_profile(self.config, 'EU')
        profiles['EU'] = {'alias_of': 'NA', 'reference_sha256_overrides': {'sources/res/other.py': 'x' * 64}}
        with self.assertRaisesRegex(ValueError, 'unknown reference file'):
            resolved_production_profile(self.config, 'EU')

    def test_russian_realms_are_never_supported(self):
        for realm in ('RU', 'PT_RU', 'LESTA'):
            self.assertNotIn(realm, self.config['game']['supported_realms'])
            self.assertNotIn(realm, self.config['reference']['production_clients'])
            self.assertIsNone(resolved_production_profile(self.config, realm))

    def test_plan_excludes_research_sources_and_packages_the_optional_fog_helper(self):
        plan = build_plan(ROOT)
        targets = {file['target'].lower() for group in ('python', 'assets')
                   for file in plan[group]}
        self.assertTrue(any(target.endswith('/gameface/lobby/main.pyc') for target in targets))
        for target in targets:
            self.assertNotIn('clock_diagnostics.pyc', target)
        # Remove Fog is an optional, default-OFF feature: its controller and helper are packaged, never enabled.
        self.assertTrue(any(target.endswith('/core/fog_package.pyc') for target in targets))
        self.assertTrue(any(target.endswith('/gui/driftkings/fog/driftkings.fogpackage.exe') for target in targets))
