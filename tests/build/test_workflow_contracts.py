"""Workflow contracts and the direct-stable approval binding, checked from the YAML files and mocked GitHub only."""
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / 'tests/build') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tests/build'))

from build_tools import promote_release as promotion
from test_release_promotion import FakeContext, STABLE_COMMIT
from test_validation_record import approved, BETA, COMMIT, PACKAGE, STABLE

WORKFLOWS = ROOT / '.github/workflows'


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding='utf-8'))


def triggers(document):
    return document.get('on', document.get(True))


def expand(template, values):
    """Evaluate the run-name expressions the way GitHub does for the values we dispatch."""
    route = values['route']
    text = template
    text = text.replace("${{ inputs.route == 'direct' && 'direct ' || '' }}", 'direct ' if route == 'direct' else '')
    text = text.replace("${{ inputs.route == 'direct' && ' ' || '' }}", ' ' if route == 'direct' else '')
    for key in ('version', 'stable_commit', 'artifacts_digest', 'record_digest'):
        text = text.replace('${{ inputs.%s }}' % key, values.get(key, ''))
    assert '${{' not in text, text
    return text


class PythonPackageWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.document = load('python-package.yml')
        self.steps = [step.get('name', '') for step in self.document['jobs']['validate']['steps']]
        self.commands = ' '.join(step.get('run', '') for step in self.document['jobs']['validate']['steps'])

    def test_triggers_target_only_the_permanent_branches_and_release_branches_for_beta(self):
        found = triggers(self.document)
        self.assertEqual(set(found['push']['branches']), {'main', 'develop', 'release/**'})
        self.assertEqual(set(found['pull_request']['branches']), {'main', 'develop'})
        self.assertNotIn('master', str(found))

    def test_required_check_job_keeps_its_name(self):
        self.assertEqual(list(self.document['jobs']), ['validate'])

    def test_essential_validation_is_kept(self):
        for needle in ('--suite runtime', '--suite build', 'validate_build_data.py', 'validate_locales.py',
                       'check_undefined_names.py', 'isort', 'generate_defaults.py --check', 'python:2.7',
                       'npm --prefix build_tools/javascript run lint', 'npm --prefix build_tools/javascript test'):
            self.assertIn(needle, self.commands, needle)

    def test_ordinary_ci_builds_no_installer_or_release_package(self):
        self.assertNotIn('build_installer.py', self.commands)
        self.assertNotIn('compiler.py', self.commands)
        self.assertNotIn('--suite artifacts', self.commands)

    def test_concurrency_cancels_superseded_runs_of_the_same_ref(self):
        self.assertTrue(self.document['concurrency']['cancel-in-progress'])

    def test_node_syntax_check_is_covered_by_the_lint_step(self):
        self.assertNotIn('node --check', self.commands)


class PromotionGateWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.document = load('promotion-gate.yml')
        self.inputs = triggers(self.document)['workflow_dispatch']['inputs']

    def test_input_contract_is_route_aware_and_minimal(self):
        self.assertEqual(set(self.inputs), {'route', 'version', 'stable_commit', 'artifacts_digest', 'record_digest',
                                            'record', 'request_approval'})
        self.assertNotIn('beta_version', self.inputs)
        self.assertEqual(self.inputs['route']['options'], ['direct', 'beta'])

    def test_run_name_matches_the_titles_the_publisher_searches_for(self):
        template = self.document['run-name']
        digest, record = 'd' * 64, promotion.record_digest(approved())
        self.assertEqual(expand(template, dict(route='direct', version=STABLE, stable_commit=STABLE_COMMIT,
                                               artifacts_digest=digest, record_digest=record)),
                         promotion.direct_gate_title(STABLE, STABLE_COMMIT, digest, record))
        self.assertEqual(expand(template, dict(route='beta', version=BETA, stable_commit=STABLE_COMMIT,
                                               artifacts_digest=digest)),
                         promotion.gate_title(BETA, STABLE_COMMIT, digest))

    def test_approval_environment_and_its_dependency_are_unchanged(self):
        approve = self.document['jobs']['approve']
        self.assertEqual(approve['environment'], 'stable-release')
        self.assertEqual(approve['needs'], 'validate')
        self.assertEqual(self.document['permissions'], {})

    def test_check_step_verifies_the_record_before_using_it(self):
        validate = self.document['jobs']['validate']
        command = [step['run'] for step in validate['steps'] if 'promote_release.py' in step.get('run', '')][0]
        self.assertIn('--record-digest "$RECORD_DIGEST"', command)
        self.assertIn('--stable "$VERSION"', command)
        self.assertIn('--beta "$VERSION"', command)
        self.assertNotIn('waive', command)


class DirectApprovalBindingTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(promotion, 'signature_module', lambda: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.context = FakeContext()
        self.record = approved().replace(BETA, STABLE).replace(COMMIT, STABLE_COMMIT).replace(PACKAGE, 'd' * 64)
        self.digest = 'd' * 64
        self.title = promotion.direct_gate_title(STABLE, STABLE_COMMIT, self.digest, promotion.record_digest(self.record))
        self.context.gate = dict(workflow_runs=[dict(id=7, run_number=3, display_title=self.title, head_branch='main',
                                                     html_url='https://gate/7')])
        self.context.jobs = [dict(name=promotion.GATE_JOB, conclusion='success')]
        self.context.approvals = [dict(state='approved', user=dict(login='maintainer'))]

    def find(self, title=None, waive=False):
        return promotion.find_gate(self.context, STABLE, STABLE_COMMIT, self.digest, waive,
                                   title=title or self.title, direct=True)

    def test_an_approved_run_of_this_exact_candidate_is_accepted(self):
        self.assertEqual(self.find()['approvedBy'], ['maintainer'])

    def test_an_approval_of_another_record_is_rejected(self):
        other = promotion.direct_gate_title(STABLE, STABLE_COMMIT, self.digest, promotion.record_digest('other'))
        with self.assertRaisesRegex(ValueError, 'No approved'):
            self.find(title=other)

    def test_an_approval_of_another_artifact_or_commit_is_rejected(self):
        for title in (promotion.direct_gate_title(STABLE, STABLE_COMMIT, 'e' * 64, promotion.record_digest(self.record)),
                      promotion.direct_gate_title(STABLE, 'c' * 40, self.digest, promotion.record_digest(self.record)),
                      promotion.direct_gate_title('1.2.4', STABLE_COMMIT, self.digest, promotion.record_digest(self.record))):
            with self.subTest(title=title), self.assertRaisesRegex(ValueError, 'No approved'):
                self.find(title=title)

    def test_the_beta_title_cannot_approve_a_direct_candidate(self):
        with self.assertRaisesRegex(ValueError, 'No approved'):
            self.find(title=promotion.gate_title(STABLE, STABLE_COMMIT, self.digest))

    def test_the_environment_approval_is_required(self):
        self.context.approvals = [dict(state='pending', user=dict(login='maintainer'))]
        with self.assertRaisesRegex(ValueError, 'No approved'):
            self.find()

    def test_the_direct_route_never_accepts_a_waiver(self):
        self.context.gate['workflow_runs'] = []
        with self.assertRaisesRegex(ValueError, 'no waiver'):
            self.find(waive=True)

    def test_a_mismatched_record_digest_stops_the_check(self):
        with self.assertRaisesRegex(ValueError, 'dispatched record digest'):
            promotion.run_check(self.context, types.SimpleNamespace(
                beta=None, stable=STABLE, record=self._record_file(), record_digest='0' * 64, commit=STABLE_COMMIT,
                digest=self.digest))

    def test_a_missing_record_stops_the_direct_check(self):
        with self.assertRaisesRegex(ValueError, 'needs --record'):
            promotion.run_check(self.context, types.SimpleNamespace(
                beta=None, stable=STABLE, record=None, record_digest=None, commit=STABLE_COMMIT, digest=self.digest))

    def test_the_direct_preflight_never_looks_for_an_evidence_commit(self):
        with patch.object(promotion, 'authorized_evidence_commit', side_effect=AssertionError('evidence commit')):
            state, results = promotion.preflight_direct(self.context, STABLE, STABLE_COMMIT, self.record)
        self.assertTrue(all(result == 'PASS' for _, result, _ in results), results)

    def _record_file(self):
        import tempfile
        handle = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8')
        handle.write(self.record)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink())
        return Path(handle.name)


class DigestAndInputLimitTests(unittest.TestCase):
    def test_approval_titles_carry_complete_digests(self):
        title = promotion.direct_gate_title(STABLE, STABLE_COMMIT, 'a' * 64, promotion.record_digest(approved()))
        self.assertRegex(title, r' # [0-9a-f]{64} [0-9a-f]{64}$')

    def test_record_digest_ignores_only_trailing_newlines(self):
        text = approved()
        self.assertEqual(promotion.record_digest(text), promotion.record_digest(text + '\n\n'))
        self.assertNotEqual(promotion.record_digest(text), promotion.record_digest(text.replace('PASS', 'FAIL', 1)))

    def test_an_abbreviated_digest_never_passes_the_direct_check(self):
        with self.assertRaisesRegex(ValueError, 'Invalid artifacts digest'):
            promotion.run_check(FakeContext(), types.SimpleNamespace(
                beta=None, stable=STABLE, record=None, record_digest=None, commit=STABLE_COMMIT, digest='a' * 16))

    def test_a_record_too_large_for_the_gate_input_is_refused(self):
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as handle:
            handle.write('x' * (promotion.MAX_GATE_RECORD + 1))
        self.addCleanup(lambda: Path(handle.name).unlink())
        with self.assertRaisesRegex(ValueError, 'gate input limit'):
            promotion.read_record_file(handle.name)


class ExistingIntegrationTests(unittest.TestCase):
    def test_discord_release_notifications_are_unchanged(self):
        document = load('discord-releases.yml')
        self.assertEqual(triggers(document)['release']['types'], ['published'])

    def test_dependabot_still_covers_actions_and_npm(self):
        config = yaml.safe_load((ROOT / '.github/dependabot.yml').read_text(encoding='utf-8'))
        ecosystems = {item['package-ecosystem'] for item in config['updates']}
        self.assertEqual(ecosystems, {'github-actions', 'npm'})
        self.assertTrue(all(item['target-branch'] == 'develop' for item in config['updates']))

    def test_every_action_is_pinned_to_a_commit(self):
        for name in ('python-package.yml', 'promotion-gate.yml', 'discord-releases.yml'):
            text = (WORKFLOWS / name).read_text(encoding='utf-8')
            for reference in re.findall(r'uses: (\S+)', text):
                self.assertRegex(reference, r'@[0-9a-f]{40}$', name)


if __name__ == '__main__':
    unittest.main()
