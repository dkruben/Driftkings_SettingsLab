"""Direct stable route: a stable candidate that was never published as a beta, using mocked GitHub and fixtures.

Nothing here performs a real release mutation, signs anything or rebuilds a candidate.
"""
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / 'tests/build') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tests/build'))

from build_tools import promote_release as promotion
from build_tools import publish_release as publisher
from test_release_promotion import (FakeContext, STABLE_COMMIT, StableBuildCase, ci_run, signature_module, signed)
from test_validation_record import approved, BETA, COMMIT, PACKAGE, STABLE

def direct_record(commit=STABLE_COMMIT, package=PACKAGE):
    """A complete record for the stable version itself; no beta record is involved."""
    return approved().replace(BETA, STABLE).replace(COMMIT, commit).replace(PACKAGE, package)


def direct_identity(commit=STABLE_COMMIT):
    return dict(beta=None, stable=STABLE, tag='v' + STABLE, commit=commit, route='direct')


class DirectContext(FakeContext):
    """The fixture world with the stable release published nowhere and the beta never published."""
    def __init__(self):
        super().__init__()
        self.releases = [dict(id=1, tag_name='v1.2.2', draft=False, prerelease=False, assets=[])]
        self.queried = []

    def query(self, path, missing_ok=False):
        self.queried.append(path)
        return super().query(path, missing_ok)


class DirectPreflightTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(promotion, 'signature_module', signature_module)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.context = DirectContext()
        self.text = direct_record()

    def run_direct(self, text=None, commit=STABLE_COMMIT, resume=False):
        state, results = promotion.preflight_direct(self.context, STABLE, commit, self.text if text is None else text,
                                                    resume)
        return state, {name: (result, detail) for name, result, detail in results}

    def test_a_stable_is_promoted_without_any_published_beta(self):
        state, results = self.run_direct()
        self.assertEqual({name: result for name, (result, _) in results.items()},
                         {'identity': 'PASS', 'record': 'PASS', 'ci': 'PASS', 'slot': 'PASS'}, results)
        self.assertEqual(state['identity']['route'], 'direct')
        self.assertFalse([path for path in self.context.queried if ('v' + BETA) in path or 'beta' in path.lower()])

    def test_missing_applicable_ci_on_the_artifact_commit_blocks(self):
        self.context.ci[STABLE_COMMIT] = []
        _, results = self.run_direct()
        self.assertEqual(results['ci'][0], 'FAIL')
        self.assertIn('No ', results['ci'][1])

    def test_failed_ci_on_the_artifact_commit_blocks(self):
        self.context.ci[STABLE_COMMIT] = [ci_run(STABLE_COMMIT, 'failure', branch='main')]
        _, results = self.run_direct()
        self.assertEqual(results['ci'][0], 'FAIL')

    def test_missing_approval_in_the_record_blocks(self):
        _, results = self.run_direct(self.text.replace('| Decisão | APPROVED |', '| Decisão | PENDING |'))
        self.assertEqual(results['record'][0], 'FAIL')
        self.assertIn('Record decision is PENDING', results['record'][1])

    def test_record_for_another_artifact_commit_is_rejected(self):
        _, results = self.run_direct(direct_record(commit='c' * 40))
        self.assertEqual(results['record'][0], 'FAIL')
        self.assertIn('differs', results['record'][1])

    def test_record_for_a_beta_is_not_stable_evidence(self):
        _, results = self.run_direct(approved())
        self.assertEqual(results['record'][0], 'FAIL')

    def test_artifact_commit_with_another_release_identity_is_rejected(self):
        self.context.files[STABLE_COMMIT]['build_data/release.json'] = json.dumps(
            dict(version=BETA, channel='beta', repository='x/y', package_id='driftkings.unified', changelog=[]))
        _, results = self.run_direct()
        self.assertEqual(results['identity'][0], 'FAIL')

    def test_a_beta_name_is_never_a_direct_stable(self):
        with self.assertRaisesRegex(ValueError, 'not 1.2.3-beta.4'):
            promotion.direct_identity(self.context, BETA, STABLE_COMMIT)

    def test_an_existing_stable_is_never_replaced(self):
        self.context.releases.append(dict(id=9, tag_name='v' + STABLE, draft=False, prerelease=False, assets=[]))
        _, results = self.run_direct()
        self.assertEqual(results['slot'][0], 'FAIL')
        self.assertIn('never overwritten', results['slot'][1])

    def test_the_record_must_be_an_explicit_file(self):
        with self.assertRaisesRegex(ValueError, 'needs --record'):
            promotion.read_record_file(None)

    def test_a_signature_is_required_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'release.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'Missing release.json.sig'):
                publisher.verify_signature(folder, signature_module())
            (folder / 'release.json.sig').write_bytes(b'not a signature')
            with self.assertRaisesRegex(ValueError, 'not valid'):
                publisher.verify_signature(folder, signature_module())


class DirectCandidateTests(StableBuildCase):
    def state(self, record_package=None, game=None):
        record = dict(packageSha256=record_package or 'd' * 64, gameVersion=game or self.report['gameVersion'])
        return dict(identity=direct_identity(), record=record)

    def test_a_matching_candidate_is_accepted(self):
        promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_candidate_digest_that_differs_from_the_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'not the package the validation record approved'):
            promotion.verify_stable_folder(self.context, self.folder, self.state(record_package='c' * 64))

    def test_artifact_commit_mismatch_is_rejected(self):
        self.report['git']['commit'] = 'f' * 40
        with self.assertRaisesRegex(ValueError, 'does not come from the stable commit'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_game_version_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'different game versions'):
            promotion.verify_stable_folder(self.context, self.folder, self.state(game='2.4.0.0'))

    def test_a_beta_named_asset_is_rejected(self):
        (self.folder / 'driftkings-beta.zip').write_bytes(b'x')
        self.files = sorted(self.folder.iterdir())
        with self.assertRaisesRegex(ValueError, 'beta name'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_development_only_wotmod_is_never_publishable(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / 'build-report.json').write_text(json.dumps(dict(
                status='success', mode='dev', profile='ct-development', realm='CT', version=STABLE, channel='stable')))
            (folder / 'release.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Only signed-eligible'):
                publisher.prepare(folder)


class DirectCommandTests(StableBuildCase):
    def setUp(self):
        super().setUp()
        self.context = DirectContext()
        record = promotion.record_digest(direct_record(package='d' * 64))
        self.full_digest = promotion.artifacts_digest_full(self.folder)
        self.context.gate['workflow_runs'][0]['display_title'] = promotion.direct_gate_title(
            STABLE, STABLE_COMMIT, self.full_digest, record)
        promotion.write_build_stamp(self.folder, STABLE_COMMIT)

    def arguments(self, record_path, **options):
        values = dict(beta=None, stable=STABLE, record=record_path, target='na1010', key=Path('offline.key'),
                      commit=None, confirm=None, waive_environment_review=False)
        values.update(options)
        return types.SimpleNamespace(**values)

    def write_record(self, text):
        handle = tempfile.NamedTemporaryFile('w', suffix='-validation.md', delete=False, encoding='utf-8')
        handle.write(text)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return Path(handle.name)

    def test_build_compiles_once_for_the_explicit_target_and_never_needs_a_beta(self):
        compile_action = Mock(return_value=self.folder)
        self.context.compile = compile_action
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else ''
        record = self.write_record(direct_record(package='d' * 64))
        with patch.object(promotion, 'print_results'), patch('builtins.print'):
            promotion.run_build(self.context, self.arguments(record))
        compile_action.assert_called_once_with(STABLE, Path('offline.key'), 'na1010')
        self.assertFalse([path for path in self.context.queried if 'beta' in path.lower()])

    def test_publication_without_approval_is_refused(self):
        self.context.gate['workflow_runs'] = []
        record = self.write_record(direct_record(package='d' * 64))
        self.context.compile = Mock(side_effect=AssertionError('publication never rebuilds'))
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else ''
        with patch.object(promotion, 'print_results'), patch('builtins.print'):
            with self.assertRaisesRegex(ValueError, 'No approved'):
                promotion.run_publish(self.context, self.arguments(record, confirm='x'))
        self.context.compile.assert_not_called()
        self.assertEqual(self.context.created, [])

    def test_preview_publication_uploads_nothing_and_never_rebuilds(self):
        self.context.compile = Mock(side_effect=AssertionError('publication never rebuilds'))
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else ''
        self.context.created = []
        record = self.write_record(direct_record(package='d' * 64))
        with patch('builtins.print'):
            promotion.run_publish(self.context, self.arguments(record))
        self.assertEqual(self.context.created, [])
        self.context.compile.assert_not_called()

    def test_a_publish_target_must_match_the_report_client(self):
        self.report['source_client'] = dict(realm='EU', build='1000', revision='2664941')
        with self.assertRaisesRegex(ValueError, 'another client than na1010'):
            promotion.require_target_identity(self.report, 'na1010')
        promotion.require_target_identity(dict(self.report, source_client=dict(realm='NA', build='1010',
                                                                              revision='2671446')), 'na1010')

    def test_historical_reports_without_a_target_still_pass(self):
        promotion.require_target_identity(self.report, 'na1010')

    def test_initial_build_needs_no_record_and_no_candidate_digest(self):
        self.context.compile = Mock(return_value=self.folder)
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else ''
        with patch.object(promotion, 'print_results'), patch('builtins.print'):
            promotion.run_build(self.context, self.arguments(None))
        self.context.compile.assert_called_once_with(STABLE, Path('offline.key'), 'na1010')

    def test_publication_requires_the_record_and_binds_it_to_the_built_digest(self):
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else ''
        self.context.compile = Mock(side_effect=AssertionError('publication never rebuilds'))
        with self.assertRaisesRegex(ValueError, 'needs --record'):
            promotion.run_publish(self.context, self.arguments(None))
        record = self.write_record(direct_record(package='c' * 64))
        with patch.object(promotion, 'print_results'), patch('builtins.print'):
            with self.assertRaisesRegex(ValueError, 'not the package the validation record approved'):
                promotion.run_publish(self.context, self.arguments(record))
        self.context.compile.assert_not_called()
