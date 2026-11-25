"""Fail closed on source identity and keep research out of distributions."""
import tempfile
import unittest
from pathlib import Path

from build_tools.validate_build_data import (ROOT, build_plan, production_profile,
                                             production_realms, read_json, source_client)


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
        for realm, build in [('NA', '999'), ('ASIA', '998'), ('CN', '997')]:
            identity = self.identify(realm, 'v.2.4.2.0 #' + build, '2664941')
            self.assertEqual(identity, dict(realm=realm, build=build, revision='2664941'))
            with self.assertRaisesRegex(ValueError, 'version/build/revision mismatch'):
                self.identify(realm, 'v.2.4.2.0 #' + build, '2660091')
        with self.assertRaisesRegex(ValueError, 'No pinned production client'):
            self.identify('EU', 'v.2.4.1.1 #993', '2653317')

    def test_ct_can_be_identified_but_cannot_be_a_production_source(self):
        identity = self.identify('CT', 'v.2.4.2.0 Common Test #996', '2660091')
        with self.assertRaisesRegex(ValueError, 'pinned production client'):
            production_profile(self.root, self.config, identity)

    def test_unreviewed_profile_is_blocked_and_realms_use_profile_evidence(self):
        identity = self.identify('NA', 'v.2.4.2.0 #999', '2664941')
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
