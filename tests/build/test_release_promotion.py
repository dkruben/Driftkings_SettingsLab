import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / 'tests/build') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tests/build'))

from build_tools import promote_release as promotion
from build_tools import publish_release as publisher
from build_tools.sign_release import load_signature, scrub_report, sign_folder
from build_tools.update_release import require_stable_replacement_consent
from test_validation_record import approved, BETA, COMMIT as APPROVED, PACKAGE, STABLE

REPOSITORY = 'owner/project'
REPOSITORY_NAME = 'dkruben/Driftkings_SettingsLab'
SOURCE = 'version.py'
STABLE_COMMIT = 'e' * 40
SEED = bytes(range(32))
SIGNATURE = load_signature()
PUBLIC = SIGNATURE.public_key(SEED).hex()
RELEASE = dict(version=BETA, channel='beta', repository=REPOSITORY, package_id='driftkings.unified', changelog=['Beta'])


def signature_module():
    return types.SimpleNamespace(TRUSTED_KEYS=(PUBLIC,), SIGNATURE_ASSET=SIGNATURE.SIGNATURE_ASSET,
                                 verify_manifest=SIGNATURE.verify_manifest, verify=SIGNATURE.verify)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def signed(raw):
    return base64.b64encode(SIGNATURE.sign(SEED, raw)) + b'\n'


def ci_run(commit, conclusion='success', branch='develop', number=1):
    return dict(head_sha=commit, head_branch=branch, status='completed', conclusion=conclusion, run_number=number,
                html_url='https://ci/%s/%d' % (branch, number), head_repository=dict(full_name=REPOSITORY))


class FakeContext(object):
    """A consistent world in which the promotion is allowed; each test breaks one thing."""
    repository = REPOSITORY
    version_source = SOURCE

    def __init__(self):
        stable_release = dict(RELEASE, version=STABLE, channel='stable', changelog=['Stable'])
        self.files = {
            APPROVED: {'build_data/release.json': json.dumps(RELEASE), SOURCE: "VERSION = '%s'\n" % BETA},
            STABLE_COMMIT: {'build_data/release.json': json.dumps(stable_release), SOURCE: "VERSION = '%s'\n" % STABLE,
                            'docs/releases/%s-validation.md' % BETA: approved()},
        }
        self.changed = ['build_data/release.json', SOURCE, 'README.md', 'docs/releases/%s-validation.md' % BETA]
        self.ancestors = {(APPROVED, STABLE_COMMIT), (STABLE_COMMIT, 'origin/main')}
        self.tags = {'v' + BETA: APPROVED}
        self.ci = {APPROVED: [ci_run(APPROVED)], STABLE_COMMIT: [ci_run(STABLE_COMMIT, branch='main')]}
        self.denied = None
        self.blobs = {}
        self.releases = [dict(id=1, tag_name='v1.2.2', draft=False, prerelease=False, assets=[])]
        self.beta_inputs = {'mod/a.py': 'x', SOURCE: '1', 'build_data/release.json': '1'}
        self.publish_beta()
        self.created, self.published = [], []
        self.gate = dict(workflow_runs=[dict(id=7, run_number=3, display_title='', head_branch='main',
                                             html_url='https://gate/7')])
        self.jobs = [dict(name=promotion.GATE_JOB, conclusion='success')]
        self.approvals = [dict(state='approved', user=dict(login='maintainer'))]
        self.environment = None

    def asset(self, identifier, name, data):
        self.blobs[identifier] = data
        return dict(id=identifier, name=name, size=len(data))

    def publish_beta(self, report=None, manifest=None, signature=None, sums=None):
        manifest = manifest or dict(version=BETA, channel='beta', sha256=PACKAGE, gameVersion='2.4.1.1')
        report = report or dict(git=dict(commit=APPROVED, dirty=False), inputs=self.beta_inputs,
                                artifacts={'driftkings.wotmod': dict(sha256=PACKAGE)})
        raw, encoded = json.dumps(manifest).encode(), json.dumps(report).encode()
        lines = sums or '%s  release.json\n%s  build-report.json\n' % (digest(raw), digest(encoded))
        assets = [self.asset(11, 'release.json', raw), self.asset(12, 'release.json.sig', signature or signed(raw)),
                  self.asset(13, 'build-report.json', encoded), self.asset(14, 'SHA256SUMS.txt', lines.encode())]
        self.releases = [item for item in self.releases if item['tag_name'] != 'v' + BETA]
        self.releases.append(dict(id=2, tag_name='v' + BETA, draft=False, prerelease=True, assets=assets))

    def git(self, *args):
        if args[0] == 'diff':
            return '\n'.join(self.changed)
        raise AssertionError(args)

    def read(self, commit, path):
        try:
            return self.files[commit][path]
        except KeyError:
            raise ValueError('Missing %s at %s' % (path, commit[:12]))

    def is_ancestor(self, ancestor, commit):
        return (ancestor, commit) in self.ancestors

    def query(self, path, missing_ok=False):
        if self.denied:
            raise ValueError(self.denied)
        match = re.search(r'head_sha=([0-9a-f]+)', path)
        if match:
            return dict(workflow_runs=self.ci.get(match.group(1), []))
        if '/releases/tags/' in path:
            return next((item for item in self.releases if item['tag_name'] == path.rsplit('/', 1)[1]), None)
        if re.search(r'/releases\?', path):
            return self.releases
        if '/releases/' in path:
            return next(item for item in self.releases if str(item['id']) == path.rsplit('/', 1)[1])
        if 'promotion-gate.yml' in path:
            return self.gate
        if '/environments/' in path:
            return self.environment
        if path.endswith('/jobs'):
            return dict(jobs=self.jobs)
        if path.endswith('/approvals'):
            return self.approvals
        raise AssertionError(path)

    def tag_commit(self, tag):
        return self.tags.get(tag)

    def download(self, asset, target):
        Path(target).write_bytes(self.blobs[asset['id']])

    def create_draft(self, command, files, manifest):
        self.created.append(command)
        assets = [self.asset(100 + index, path.name, path.read_bytes()) for index, path in enumerate(files)]
        self.releases.append(dict(id=9, tag_name='v' + STABLE, draft=True, prerelease=False, assets=assets,
                                  target_commitish=STABLE_COMMIT))

    def publish_draft(self, release):
        self.published.append(release['id'])
        release['draft'] = False
        self.tags['v' + STABLE] = STABLE_COMMIT

    def viewer(self):
        return 'maintainer'


class PreflightCase(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(promotion, 'signature_module', signature_module)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.context = FakeContext()

    def results(self, beta=BETA, commit=STABLE_COMMIT, **options):
        return {name: (result, detail) for name, result, detail in promotion.preflight(self.context, beta, commit, **options)[1]}

    def assertBlocked(self, check, reason, **options):
        results = self.results(**options)
        self.assertEqual(results[check][0], 'FAIL', results)
        self.assertRegex(results[check][1], reason)


class PreflightTests(PreflightCase):
    def test_allows_a_consistent_promotion(self):
        results = self.results()
        self.assertEqual({value[0] for value in results.values()}, {'PASS'}, results)

    def test_blocks_a_record_without_approval(self):
        self.context.files[STABLE_COMMIT]['docs/releases/%s-validation.md' % BETA] = \
            approved().replace('| Decisão | APPROVED |', '| Decisão | PENDING |')
        self.assertBlocked('record', 'decision is PENDING')
        self.assertEqual(self.results()['beta'][0], 'NOT RUN')

    def test_blocks_a_missing_record(self):
        del self.context.files[STABLE_COMMIT]['docs/releases/%s-validation.md' % BETA]
        self.assertBlocked('record', 'Missing')

    def test_blocks_wrong_stable_version_or_channel(self):
        source = self.context.files[STABLE_COMMIT]
        source['build_data/release.json'] = json.dumps(dict(RELEASE, version=STABLE, channel='beta'))
        self.assertBlocked('identity', 'not 1.2.3/stable')
        source['build_data/release.json'] = json.dumps(dict(RELEASE, version=STABLE, channel='stable'))
        source[SOURCE] = "VERSION = '1.2.2'\n"
        self.assertBlocked('identity', 'Runtime VERSION differs')

    def test_blocks_a_stable_requested_as_beta_or_an_abbreviated_commit(self):
        self.assertBlocked('identity', 'Only beta or rc', beta='1.2.3')
        self.assertBlocked('identity', 'full SHA-1', commit='abc1234')

    def test_blocks_a_commit_unrelated_to_the_approved_beta(self):
        self.context.ancestors.discard((APPROVED, STABLE_COMMIT))
        self.assertBlocked('history', 'not an ancestor')

    def test_blocks_a_stable_commit_outside_main(self):
        self.context.ancestors.discard((STABLE_COMMIT, 'origin/main'))
        self.assertBlocked('history', 'not on origin/main')

    def test_blocks_code_changes_after_the_approved_beta(self):
        self.context.changed.append('mod/res/scripts/client/driftkings/battle/feature.py')
        self.assertBlocked('changes', 'need a new beta.*feature.py')

    def test_blocks_changes_to_the_ci_workflow_and_compiler(self):
        for path in ('.github/workflows/python-package.yml', 'build_tools/compiler.py'):
            self.context.changed = [path]
            self.assertBlocked('changes', 'need a new beta')

    def test_blocks_a_version_source_changing_more_than_version(self):
        self.context.files[STABLE_COMMIT][SOURCE] = "VERSION = '1.2.3'\nDEBUG = True\n"
        self.assertBlocked('changes', 'changes more than VERSION')

    def test_blocks_release_data_changing_more_than_version_data(self):
        data = dict(RELEASE, version=STABLE, channel='stable', package_id='other')
        self.context.files[STABLE_COMMIT]['build_data/release.json'] = json.dumps(data)
        self.assertBlocked('changes', 'package_id')

    def test_blocks_a_record_about_another_tag_commit(self):
        self.context.tags['v' + BETA] = 'f' * 40
        self.assertBlocked('beta', 'does not point to the recorded commit')

    def test_blocks_a_beta_that_is_not_a_published_prerelease(self):
        next(item for item in self.context.releases if item['id'] == 2)['draft'] = True
        self.assertBlocked('beta', 'not a published prerelease')
        self.context.releases = [item for item in self.context.releases if item['id'] != 2]
        self.assertBlocked('beta', 'not a published prerelease')

    def test_blocks_incomplete_beta_metadata(self):
        release = next(item for item in self.context.releases if item['id'] == 2)
        release['assets'] = [asset for asset in release['assets'] if asset['name'] != 'release.json.sig']
        self.assertBlocked('beta', 'missing signed metadata')

    def test_blocks_an_invalid_beta_signature(self):
        self.context.publish_beta(signature=signed(b'another manifest'))
        self.assertBlocked('beta', 'signature rejected')

    def test_blocks_a_wrong_beta_checksum(self):
        self.context.publish_beta(sums='%s  release.json\n%s  build-report.json\n' % ('0' * 64, '0' * 64))
        self.assertBlocked('beta', 'checksum mismatch')

    def test_blocks_a_package_other_than_the_validated_one(self):
        self.context.publish_beta(manifest=dict(version=BETA, channel='beta', sha256='c' * 64, gameVersion='2.4.1.1'))
        self.assertBlocked('beta', 'not the published beta package')

    def test_blocks_a_manifest_of_another_version_or_channel(self):
        for version, channel in (('1.2.3-beta.3', 'beta'), (BETA, 'stable')):
            self.context.publish_beta(manifest=dict(version=version, channel=channel, sha256=PACKAGE, gameVersion='2.4.1.1'))
            self.assertBlocked('beta', 'manifest identity mismatch')

    def test_blocks_a_record_for_another_game_version(self):
        self.context.publish_beta(manifest=dict(version=BETA, channel='beta', sha256=PACKAGE, gameVersion='2.4.1.2'))
        self.assertBlocked('beta', 'different game versions')

    def test_blocks_a_dirty_or_foreign_beta_build(self):
        self.context.publish_beta(report=dict(git=dict(commit=APPROVED, dirty=True), inputs={}, artifacts={}))
        self.assertBlocked('beta', 'does not come from the recorded commit')

    def test_blocks_failed_or_missing_required_tests(self):
        self.context.ci[APPROVED] = [ci_run(APPROVED, 'failure')]
        self.assertBlocked('ci', 'did not pass')
        self.context.ci[APPROVED] = [ci_run(APPROVED)]
        self.context.ci[STABLE_COMMIT] = [dict(ci_run(STABLE_COMMIT), status='in_progress', conclusion=None)]
        self.assertBlocked('ci', 'did not pass')
        self.context.ci[STABLE_COMMIT] = []
        self.assertBlocked('ci', 'No python-package.yml run')

    def test_blocks_an_existing_stable(self):
        self.context.releases.append(dict(id=3, tag_name='v' + STABLE, draft=False, prerelease=False, assets=[]))
        self.assertBlocked('slot', 'never overwritten')

    def test_blocks_an_existing_draft_or_tag(self):
        self.context.releases.append(dict(id=3, tag_name='v' + STABLE, draft=True, prerelease=False, assets=[]))
        self.assertBlocked('slot', '1 draft')
        self.context.releases.pop()
        self.context.tags['v' + STABLE] = STABLE_COMMIT
        self.assertBlocked('slot', 'already exists on origin')

    def test_blocks_a_stable_older_than_the_published_one(self):
        self.context.releases.append(dict(id=3, tag_name='v1.3.0', draft=False, prerelease=False, assets=[]))
        self.assertBlocked('slot', 'newer or equal stable')

    def test_reports_missing_permissions_instead_of_passing(self):
        self.context.denied = 'GitHub query failed; check `gh auth status`: HTTP 403'
        results = self.results()
        for check in ('beta', 'ci', 'slot'):
            self.assertEqual(results[check][0], 'FAIL')
            self.assertIn('HTTP 403', results[check][1])


class GitHubAccessTests(unittest.TestCase):
    def failure(self, message):
        return subprocess.CompletedProcess([], 1, b'', message)

    def test_explains_missing_permissions(self):
        with patch.object(publisher.subprocess, 'run', return_value=self.failure(b'HTTP 403: Forbidden')):
            with self.assertRaisesRegex(ValueError, 'gh auth status.*HTTP 403'):
                publisher.github_json('repos/x')

    def test_only_an_allowed_404_counts_as_missing(self):
        with patch.object(publisher.subprocess, 'run', return_value=self.failure(b'HTTP 404: Not Found')):
            self.assertIsNone(publisher.github_json('repos/x', missing_ok=True))
            with self.assertRaises(ValueError):
                publisher.github_json('repos/x')


class PublisherGuardTests(unittest.TestCase):
    def setUp(self):
        self.green, self.unpublished, self.create = Mock(), Mock(), Mock()

    def publish(self, channel='beta', version=BETA):
        """The real main() up to the upload, with both GitHub guards observable."""
        report = dict(git=dict(commit=APPROVED, dirty=False))
        error = io.StringIO()
        with patch.object(publisher, 'prepare', return_value=(['gh'], [], report, dict(channel=channel, version=version))), \
                patch.object(publisher.subprocess, 'check_output', side_effect=[APPROVED.encode(), b'']), \
                patch.object(publisher, 'require_green_ci', self.green), \
                patch.object(publisher, 'require_unpublished', self.unpublished), \
                patch.object(publisher, 'create_release', self.create), \
                patch.object(sys, 'argv', ['publish_release.py', 'folder', '--publish']), patch.object(sys, 'stderr', error):
            try:
                publisher.main()
            except SystemExit as stopped:
                self.assertEqual(stopped.code, 1)
        return error.getvalue()

    def test_a_beta_reaches_the_upload_only_through_both_guards(self):
        self.assertEqual(self.publish(), '')
        self.green.assert_called_once_with(REPOSITORY_NAME, APPROVED)
        self.unpublished.assert_called_once_with(REPOSITORY_NAME, 'v' + BETA)
        self.create.assert_called_once()

    def test_a_red_ci_stops_the_upload(self):
        self.green.side_effect = ValueError('CI is red')
        self.assertIn('CI is red', self.publish())
        self.create.assert_not_called()

    def test_an_existing_release_stops_the_upload(self):
        self.unpublished.side_effect = ValueError('tag already has a draft')
        self.assertIn('tag already has a draft', self.publish())
        self.create.assert_not_called()

    def test_a_stable_is_refused_before_any_github_call(self):
        self.assertIn('promote_release.py', self.publish('stable', STABLE))
        self.green.assert_not_called()
        self.unpublished.assert_not_called()
        self.create.assert_not_called()

    def test_duplicate_draft_of_the_same_tag_is_refused(self):
        query = lambda path: [dict(tag_name='v1.0.0-beta.1', draft=True), dict(tag_name='v0.9.0', draft=False)]
        with self.assertRaisesRegex(ValueError, r'1 release\(s\).*draft'):
            publisher.require_unpublished(REPOSITORY, 'v1.0.0-beta.1', query)

    def test_existing_remote_tag_is_refused(self):
        with patch.object(publisher.subprocess, 'check_output', return_value=b'abc refs/tags/v1.0.0\n'):
            with self.assertRaisesRegex(ValueError, 'already exists on origin'):
                publisher.require_unpublished(REPOSITORY, 'v1.0.0', lambda path: [])

    def test_a_new_tag_is_accepted(self):
        with patch.object(publisher.subprocess, 'check_output', return_value=b''):
            publisher.require_unpublished(REPOSITORY, 'v1.0.0', lambda path: [])

    def test_a_red_commit_is_refused(self):
        query = lambda path: dict(workflow_runs=[ci_run(APPROVED, 'failure')])
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            publisher.require_green_ci(REPOSITORY, APPROVED, query)

    def test_a_run_from_a_fork_does_not_count(self):
        foreign = dict(ci_run(APPROVED), head_repository=dict(full_name='fork/project'))
        with self.assertRaisesRegex(ValueError, 'No python-package.yml run'):
            publisher.require_green_ci(REPOSITORY, APPROVED, lambda path: dict(workflow_runs=[foreign]))

    def test_a_rerun_replaces_an_older_failure_but_every_branch_must_pass(self):
        runs = [ci_run(APPROVED, 'failure', number=1), ci_run(APPROVED, number=2)]
        for order in (runs, runs[::-1]):
            self.assertEqual(publisher.require_green_ci(REPOSITORY, APPROVED, lambda path: dict(workflow_runs=order)),
                             ['https://ci/develop/2'])
        newest_failed = [ci_run(APPROVED, number=1), ci_run(APPROVED, 'failure', number=2)]
        for order in (newest_failed, newest_failed[::-1]):
            with self.assertRaisesRegex(ValueError, 'did not pass'):
                publisher.require_green_ci(REPOSITORY, APPROVED, lambda path: dict(workflow_runs=order))
        runs.append(ci_run(APPROVED, 'failure', branch='main', number=3))
        with self.assertRaisesRegex(ValueError, 'on main'):
            publisher.require_green_ci(REPOSITORY, APPROVED, lambda path: dict(workflow_runs=runs))

    def test_stable_assets_are_not_replaced_without_consent(self):
        require_stable_replacement_consent('beta', True, False)
        require_stable_replacement_consent('stable', False, False)
        require_stable_replacement_consent('stable', True, True)
        with self.assertRaisesRegex(ValueError, '--replace-stable-assets'):
            require_stable_replacement_consent('stable', True, False)


class StableBuildCase(PreflightCase):
    def setUp(self):
        super().setUp()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        raw = json.dumps(dict(version=STABLE, channel='stable', sha256='d' * 64)).encode()
        for name, data in (('release.json', raw), ('release.json.sig', signed(raw)), ('SHA256SUMS.txt', b'sums\n'),
                           ('driftkings.wotmod', b'package'), ('Driftkings-1.2.3-WoT-2.4.1.1-Setup.exe', b'MZ')):
            (self.folder / name).write_bytes(data)
        self.files = sorted(path for path in self.folder.iterdir())
        self.report = dict(version=STABLE, channel='stable', gameVersion='2.4.1.1',
                           git=dict(commit=STABLE_COMMIT, dirty=False), inputs=dict(self.context.beta_inputs))
        self.manifest = dict(version=STABLE, channel='stable', sha256='d' * 64, changelog=['Stable'])
        self.command = ['gh', 'release', 'create', 'v' + STABLE]
        self.digest = promotion.artifacts_digest(self.folder)
        self.context.gate['workflow_runs'][0]['display_title'] = promotion.gate_title(BETA, STABLE_COMMIT, self.digest)
        for name, value in (('prepare', self.prepared), ('stable_folder', lambda stable: self.folder)):
            patcher = patch.object(promotion, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def prepared(self, folder):
        return self.command, self.files, self.report, self.manifest

    def state(self):
        return promotion.preflight(self.context, BETA, STABLE_COMMIT)[0]


class StableBuildTests(StableBuildCase):
    def test_accepts_a_rebuilt_stable(self):
        promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_rejects_a_build_of_another_commit_or_a_dirty_build(self):
        self.report['git'] = dict(commit='0' * 40, dirty=False)
        with self.assertRaisesRegex(ValueError, 'does not come from the stable commit'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())
        self.report['git'] = dict(commit=STABLE_COMMIT, dirty=True)
        with self.assertRaisesRegex(ValueError, 'does not come from the stable commit'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_rejects_a_renamed_beta(self):
        self.manifest['sha256'] = PACKAGE
        with self.assertRaisesRegex(ValueError, 'must be rebuilt'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_rejects_beta_asset_names_and_prerelease_commands(self):
        self.files.append(self.folder / 'Driftkings-1.2.3-beta.4.zip')
        with self.assertRaisesRegex(ValueError, 'carries a beta name'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())
        self.files.pop()
        self.command.append('--prerelease')
        with self.assertRaisesRegex(ValueError, 'cannot be published as a prerelease'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_rejects_inputs_that_differ_from_the_approved_beta(self):
        self.report['inputs'] = dict(self.report['inputs'], **{'mod/a.py': 'y'})
        with self.assertRaisesRegex(ValueError, 'differ from the approved beta: mod/a.py'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_allows_version_and_release_tool_inputs_to_differ(self):
        self.report['inputs'] = dict(self.report['inputs'], **{SOURCE: '2', 'build_data/release.json': '2',
                                                               'build_tools/promote_release.py': '1'})
        promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_rejects_another_version_or_channel_in_the_build(self):
        for field, value in (('version', '1.2.4'), ('channel', 'beta')):
            original = self.report[field]
            self.report[field] = value
            with self.assertRaisesRegex(ValueError, 'not the expected stable'):
                promotion.verify_stable_folder(self.context, self.folder, self.state())
            self.report[field] = original
        self.manifest['channel'] = 'beta'
        with self.assertRaisesRegex(ValueError, 'not the expected stable'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_rejects_a_build_for_another_game_version(self):
        self.report['gameVersion'] = '2.4.1.2'
        with self.assertRaisesRegex(ValueError, 'different game versions'):
            promotion.verify_stable_folder(self.context, self.folder, self.state())

    def test_incomplete_or_tampered_artifacts_stop_at_the_publisher_checks(self):
        with patch.object(promotion, 'prepare', side_effect=ValueError('Incomplete release artifacts')):
            with self.assertRaisesRegex(ValueError, 'Incomplete release artifacts'):
                promotion.verify_stable_folder(self.context, self.folder, self.state())


class BuildCommandTests(StableBuildCase):
    def arguments(self):
        return types.SimpleNamespace(beta=BETA, key=Path('offline.key'))

    def test_a_finished_build_leaves_a_stamp_that_publication_accepts(self):
        self.prepare_checkout(lambda stable, key: self.folder)
        with patch.object(promotion, 'print_results'), patch('builtins.print') as output:
            promotion.run_build(self.context, self.arguments())
        promotion.require_build_stamp(self.folder, STABLE_COMMIT)
        self.assertIn(self.digest, ' '.join(str(call) for call in output.call_args_list))

    def test_another_checkout_never_compiles(self):
        self.context.git = lambda *args: 'f' * 40 if args[0] == 'rev-parse' else ''
        with self.assertRaisesRegex(ValueError, 'Check out the stable commit'):
            promotion.require_clean_checkout(self.context, STABLE_COMMIT)

    def prepare_checkout(self, compile_action):
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else '\n'.join(self.context.changed) if args[0] == 'diff' else ''
        self.context.compile = compile_action

    def test_compilation_failure_stops_before_verification(self):
        self.prepare_checkout(lambda stable, key: (_ for _ in ()).throw(subprocess.CalledProcessError(1, 'compiler')))
        with patch.object(promotion, 'print_results'), patch.object(promotion, 'verify_stable_folder') as verify:
            with self.assertRaises(subprocess.CalledProcessError):
                promotion.run_build(self.context, self.arguments())
        verify.assert_not_called()
        self.assertEqual(self.context.created, [])

    def test_a_blocked_preflight_never_compiles(self):
        self.context.ci[STABLE_COMMIT] = [ci_run(STABLE_COMMIT, 'failure', branch='main')]
        self.prepare_checkout(lambda stable, key: self.fail('compiled'))
        with patch.object(promotion, 'print_results'):
            with self.assertRaisesRegex(ValueError, 'Promotion blocked'):
                promotion.run_build(self.context, self.arguments())

    def test_a_dirty_checkout_never_compiles(self):
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else ' M file'
        self.context.compile = lambda stable, key: self.fail('compiled')
        with self.assertRaisesRegex(ValueError, 'uncommitted changes'):
            promotion.run_build(self.context, self.arguments())


class PublishCommandTests(StableBuildCase):
    def setUp(self):
        super().setUp()
        self.context.git = lambda *args: STABLE_COMMIT if args[0] == 'rev-parse' else '\n'.join(self.context.changed) if args[0] == 'diff' else ''
        patcher = patch.object(promotion, 'print_results')
        patcher.start()
        self.addCleanup(patcher.stop)
        promotion.write_build_stamp(self.folder, STABLE_COMMIT)

    def token(self):
        return 'v%s@%s' % (STABLE, promotion.artifacts_digest(self.folder))

    def publish(self, confirm='token', waive=False):
        confirm = self.token() if confirm == 'token' else confirm
        arguments = types.SimpleNamespace(beta=BETA, confirm=confirm, waive_environment_review=waive)
        promotion.run_publish(self.context, arguments)

    def provenance(self):
        return json.loads((self.folder / promotion.PROVENANCE).read_text(encoding='utf-8'))

    def test_without_confirmation_nothing_is_uploaded(self):
        with patch('builtins.print'):
            self.publish(confirm=None)
        self.assertEqual((self.context.created, self.context.published), ([], []))

    def test_a_wrong_confirmation_is_refused(self):
        for value in ('v1.2.2', 'v' + STABLE, 'v%s@%s' % (STABLE, '0' * 16)):
            with self.assertRaisesRegex(ValueError, 'must be exactly'):
                self.publish(confirm=value)
        self.assertEqual(self.context.created, [])

    def test_the_preview_shows_the_digest_of_every_asset(self):
        with patch('builtins.print') as output:
            self.publish(confirm=None)
        text = ' '.join(str(call) for call in output.call_args_list)
        self.assertIn(self.token(), text)
        self.assertIn(hashlib.sha256((self.folder / 'release.json').read_bytes()).hexdigest(), text)

    def test_a_folder_that_skipped_build_is_refused(self):
        (self.folder / promotion.BUILD_STAMP).unlink()
        with self.assertRaisesRegex(ValueError, 'did not come from'):
            self.publish(confirm=None)
        self.assertEqual(self.context.created, [])

    def test_a_build_changed_after_the_stamp_is_refused(self):
        for name in ('SHA256SUMS.txt', 'release.json'):
            original = (self.folder / name).read_bytes()
            (self.folder / name).write_bytes(original + b' ')
            with self.assertRaisesRegex(ValueError, 'changed after'):
                self.publish(confirm=None)
            (self.folder / name).write_bytes(original)

    def test_a_stamp_of_another_commit_is_refused(self):
        promotion.write_build_stamp(self.folder, 'f' * 40)
        with self.assertRaisesRegex(ValueError, 'changed after'):
            self.publish(confirm=None)

    def test_an_approval_of_other_artifacts_does_not_count(self):
        self.context.gate['workflow_runs'][0]['display_title'] = promotion.gate_title(BETA, STABLE_COMMIT, '0' * 16)
        with self.assertRaisesRegex(ValueError, 'No approved promotion-gate.yml run'):
            self.publish()

    def test_stamp_never_reaches_the_release(self):
        with patch('builtins.print'):
            self.publish()
        names = [asset['name'] for asset in self.context.releases[-1]['assets']]
        self.assertNotIn(promotion.BUILD_STAMP, names)
        self.assertIn(promotion.PROVENANCE, names)

    def test_publishes_with_full_traceability(self):
        with patch('builtins.print'):
            self.publish()
        self.assertEqual(self.context.published, [9])
        record = self.provenance()
        self.assertEqual((record['stable']['commit'], record['beta']['commit']), (STABLE_COMMIT, APPROVED))
        self.assertEqual(record['stable']['signingKey'], PUBLIC)
        self.assertEqual(record['gate'], dict(run='https://gate/7', approvedBy=['maintainer'], status='approved'))
        self.assertEqual(record['validation']['validatedRegions'], ['EU'])
        self.assertEqual(record['validation']['notValidatedRegions'], ['NA', 'ASIA'])
        self.assertEqual(record['promotedBy'], 'maintainer')

    def test_provenance_never_enters_the_signed_manifest(self):
        before = (self.folder / 'release.json').read_bytes()
        with patch('builtins.print'):
            self.publish()
        self.assertEqual((self.folder / 'release.json').read_bytes(), before)

    def gate_case(self, change):
        """One broken gate at a time, starting from a fully approved run."""
        context = self.context
        saved = (context.approvals, context.jobs, json.loads(json.dumps(context.gate)))
        change()
        try:
            with self.assertRaisesRegex(ValueError, 'No approved promotion-gate.yml run'):
                self.publish()
        finally:
            context.approvals, context.jobs, context.gate = saved
        self.assertEqual(context.created, [])

    def test_each_part_of_the_gate_is_required(self):
        context, run = self.context, lambda: self.context.gate['workflow_runs'][0]
        for change in (lambda: setattr(context, 'approvals', []),
                       lambda: setattr(context, 'approvals', [dict(state='rejected', user=dict(login='other'))]),
                       lambda: setattr(context, 'jobs', [dict(name=promotion.GATE_JOB, conclusion='skipped')]),
                       lambda: setattr(context, 'jobs', [dict(name='Validate promotion', conclusion='success')]),
                       lambda: run().__setitem__('head_branch', 'develop'),
                       lambda: run().__setitem__('display_title', promotion.gate_title(BETA, 'f' * 40, self.digest)),
                       lambda: setattr(context, 'gate', dict(workflow_runs=[])),
                       lambda: setattr(context, 'gate', None)):
            self.gate_case(change)

    def test_a_waiver_is_explicit_and_recorded(self):
        self.context.gate = None
        with patch('builtins.print'):
            self.publish(waive=True)
        self.assertEqual(self.provenance()['gate'], dict(run=None, approvedBy=[], status='waived'))

    def test_a_waiver_works_on_an_unprotected_environment(self):
        self.context.gate = None
        self.context.environment = dict(protection_rules=[dict(type='branch_policy')])
        with patch('builtins.print'):
            self.publish(waive=True)
        self.assertEqual(self.context.published, [9])

    def test_a_waiver_never_overrides_required_reviewers(self):
        self.context.gate = None
        self.context.environment = dict(protection_rules=[dict(type='required_reviewers')])
        with self.assertRaisesRegex(ValueError, 'cannot be waived'):
            self.publish(waive=True)
        self.assertEqual(self.context.created, [])

    def test_an_approved_run_needs_no_waiver_even_on_a_protected_environment(self):
        self.context.environment = dict(protection_rules=[dict(type='required_reviewers')])
        with patch('builtins.print'):
            self.publish()
        self.assertEqual(self.provenance()['gate']['status'], 'approved')

    def corrupt_upload(self, change):
        original = self.context.create_draft

        def create(command, files, manifest):
            original(command, files, manifest)
            change(self.context.releases[-1])

        self.context.create_draft = create

    def test_a_corrupted_upload_is_never_published(self):
        self.corrupt_upload(lambda draft: self.context.blobs.__setitem__(draft['assets'][0]['id'], b'x' * draft['assets'][0]['size']))
        with self.assertRaisesRegex(ValueError, 'digest differs'):
            self.publish()
        self.assertEqual(self.context.published, [])

    def test_an_incomplete_upload_is_never_published(self):
        self.corrupt_upload(lambda draft: draft['assets'].pop())
        with self.assertRaisesRegex(ValueError, 'Draft assets differ'):
            self.publish()
        self.assertEqual(self.context.published, [])

    def test_a_publication_failure_keeps_the_draft_and_can_be_resumed(self):
        self.context.publish_draft = lambda release: (_ for _ in ()).throw(subprocess.CalledProcessError(1, 'gh'))
        with self.assertRaises(subprocess.CalledProcessError):
            self.publish()
        self.assertEqual(len(self.context.created), 1)
        del self.context.publish_draft
        with patch('builtins.print'):
            self.publish()
        self.assertEqual(len(self.context.created), 1)
        self.assertEqual(self.context.published, [9])

    def test_a_foreign_draft_is_not_adopted(self):
        self.context.releases.append(dict(id=9, tag_name='v' + STABLE, draft=True, prerelease=False, assets=[],
                                          target_commitish='f' * 40))
        with self.assertRaisesRegex(ValueError, 'targets another commit'):
            self.publish()
        self.assertEqual(self.context.published, [])

    def test_a_published_stable_is_never_touched(self):
        with patch('builtins.print'):
            self.publish()
        with self.assertRaisesRegex(ValueError, 'Promotion blocked'):
            self.publish()
        self.assertEqual(self.context.published, [9])

    def test_a_second_draft_appearing_during_creation_stops_publication(self):
        def race(draft):
            self.context.releases.append(dict(draft, id=10))

        self.corrupt_upload(race)
        with self.assertRaisesRegex(ValueError, 'exactly one draft'):
            self.publish()
        self.assertEqual(self.context.published, [])

    def test_a_release_left_as_draft_or_prerelease_is_reported(self):
        for field in ('draft', 'prerelease'):
            gate = self.context.gate
            context = self.context = FakeContext()
            context.gate, context.git = gate, lambda *args, c=context: (
                STABLE_COMMIT if args[0] == 'rev-parse' else '\n'.join(c.changed) if args[0] == 'diff' else '')
            original = context.publish_draft

            def publish(release, original=original, field=field):
                original(release)
                release[field] = True

            context.publish_draft = publish
            with self.assertRaisesRegex(ValueError, 'was not published as stable'):
                self.publish()

    def test_a_public_asset_that_differs_is_reported(self):
        original = self.context.publish_draft

        def publish(release):
            original(release)
            asset = next(item for item in release['assets'] if item['name'] == 'release.json')
            self.context.blobs[asset['id']] = b'changed'

        self.context.publish_draft = publish
        with self.assertRaisesRegex(ValueError, 'Published asset differs'):
            self.publish()

    def test_a_failed_check_after_publication_is_reported(self):
        original = self.context.publish_draft

        def publish(release):
            original(release)
            self.context.tags['v' + STABLE] = 'f' * 40

        self.context.publish_draft = publish
        with self.assertRaisesRegex(ValueError, 'not the stable commit'):
            self.publish()


class ReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        (self.folder / 'dependencies').mkdir()
        (self.folder / 'dependencies/dep.wotmod').write_bytes(b'dependency')
        (self.folder / 'release.json').write_bytes(b'{}')
        self.report = dict(status='success', realm='EU', tools=dict(python27='C:\\Toolchain\\python.exe'),
                           logs='C:\\Users\\someone\\logs', git=dict(commit=APPROVED, dirty=False),
                           artifacts={'release.json': dict(size=2), 'dependencies/dep.wotmod': dict(size=10)})
        (self.folder / 'build-report.json').write_text(json.dumps(self.report), encoding='utf-8')
        (self.folder / 'SHA256SUMS.txt').write_bytes(b'stale\n')

    def test_scrub_removes_local_paths_and_refreshes_the_checksums(self):
        scrub_report(self.folder)
        report = json.loads((self.folder / 'build-report.json').read_text(encoding='utf-8'))
        self.assertNotIn('tools', report)
        self.assertNotIn('logs', report)
        self.assertEqual((report['realm'], report['git']), ('EU', self.report['git']))
        self.assertEqual(publisher.absolute_paths(report), [])
        lines = dict(reversed(line.split('  ', 1)) for line in
                     (self.folder / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines())
        self.assertEqual(set(lines), {'build-report.json', 'release.json', 'dependencies/dep.wotmod'})
        for name, value in lines.items():
            self.assertEqual(value, digest((self.folder / name).read_bytes()))

    def test_signing_scrubs_the_report(self):
        key = self.folder / 'offline.key'
        key.write_text(SEED.hex())
        sign_folder(self.folder, key)
        self.assertNotIn('tools', json.loads((self.folder / 'build-report.json').read_text(encoding='utf-8')))

    def test_scrub_leaves_a_clean_report_untouched(self):
        scrub_report(self.folder)
        (self.folder / 'SHA256SUMS.txt').write_bytes(b'kept\n')
        scrub_report(self.folder)
        self.assertEqual((self.folder / 'SHA256SUMS.txt').read_bytes(), b'kept\n')

    def test_recognizes_paths_of_either_platform_anywhere_in_the_report(self):
        for value in ('C:\\Users\\x', 'e:/build', '/home/x', {'a': ['C:\\Toolchain']}, {'D:\\key': 1}):
            self.assertTrue(publisher.absolute_paths(dict(field=value)), value)
        for value in ('https://github.com/x', 'mod/res/a.py', 'a:b', 12, None, dict(input='res/x.json')):
            self.assertEqual(publisher.absolute_paths(dict(field=value)), [], value)

    def real_build(self):
        """A build the publisher accepts; each test breaks one thing."""
        wotmod = self.folder / 'driftkings.wotmod'
        wotmod.write_bytes(b'package')
        setup = self.folder / 'Driftkings-1.2.3-WoT-2.4.1.1-Setup.exe'
        setup.write_bytes(b'MZ')
        names = {'driftkings.wotmod', 'release.json', 'modpack.json', 'Driftkings-defaults.zip', 'dist.zip', setup.name}
        for name in names - {'driftkings.wotmod', setup.name}:
            (self.folder / name).write_bytes(b'{}')
        manifest = dict(version=STABLE, channel='stable', schema=2, gameVersion='2.4.1.1', sha256=digest(b'package'), size=7,
                        download='https://github.com/%s/releases/download/v%s/driftkings.wotmod' % (REPOSITORY_NAME, STABLE))
        (self.folder / 'release.json').write_text(json.dumps(manifest), encoding='utf-8')
        report = dict(status='success', mode='release', publishable=True, version=STABLE, channel='stable',
                      artifacts={name: dict(size=(self.folder / name).stat().st_size,
                                            sha256=digest((self.folder / name).read_bytes())) for name in names},
                      verification=dict(modpack=dict(status='passed')), git=dict(commit=APPROVED))
        self.write_report(report)
        return report, setup

    def write_report(self, report):
        (self.folder / 'build-report.json').write_text(json.dumps(report), encoding='utf-8')
        names = sorted(set(report['artifacts']) | {'build-report.json'})
        (self.folder / 'SHA256SUMS.txt').write_bytes(''.join(
            '%s  %s\n' % (digest((self.folder / name).read_bytes()), name) for name in names).encode('utf-8'))

    def prepare(self):
        inventory = types.SimpleNamespace(distribution=dict(file='dist.zip'), files=[])
        with patch.object(publisher, 'verify_modpack', return_value=inventory), \
                patch.object(publisher, 'verify_signature', return_value='release.json'):
            return publisher.prepare(self.folder)

    def test_the_publisher_accepts_a_complete_build(self):
        self.real_build()
        self.assertEqual(len(self.prepare()[1]), 8)

    def test_the_publisher_refuses_a_build_without_the_installer(self):
        report, setup = self.real_build()
        setup.unlink()
        del report['artifacts'][setup.name]
        self.write_report(report)
        with self.assertRaisesRegex(ValueError, 'Incomplete release artifacts'):
            self.prepare()

    def test_the_publisher_refuses_a_report_with_local_paths(self):
        report, _ = self.real_build()
        report['logs'] = 'E:\\work\\logs'
        self.write_report(report)
        with self.assertRaisesRegex(ValueError, 'local paths'):
            self.prepare()


class GitHubCommandTests(unittest.TestCase):
    def setUp(self):
        self.context = promotion.Context()

    def test_drafts_are_created_as_drafts(self):
        with patch.object(promotion, 'create_release') as create:
            self.context.create_draft(['gh'], [], {})
        self.assertIn('--draft', create.call_args[0][0])

    def test_publication_is_a_stable_latest_release(self):
        with patch.object(promotion.subprocess, 'run') as run:
            self.context.publish_draft(dict(id=5))
        command = run.call_args[0][0]
        self.assertEqual(command[:4], ['gh', 'api', '-X', 'PATCH'])
        for field in ('draft=false', 'prerelease=false', 'make_latest=true'):
            self.assertIn(field, command)

    def test_a_tracked_or_missing_key_never_reaches_the_compiler(self):
        with tempfile.TemporaryDirectory() as temporary:
            key = Path(temporary) / 'offline.key'
            with patch.object(promotion.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'key is missing'):
                    self.context.compile(STABLE, key)
                run.assert_not_called()
                key.write_text('00' * 32)
                run.return_value = subprocess.CompletedProcess([], 0)
                with self.assertRaisesRegex(ValueError, 'tracked by git'):
                    self.context.compile(STABLE, key)
                self.assertEqual(run.call_count, 1)

    def test_a_failed_build_step_stops_before_signing(self):
        with tempfile.TemporaryDirectory() as temporary:
            key = Path(temporary) / 'offline.key'
            key.write_text('00' * 32)

            def run(command, **options):
                if command[0] == 'git':
                    return subprocess.CompletedProcess(command, 1)
                raise subprocess.CalledProcessError(1, command)

            with patch.object(promotion.subprocess, 'run', side_effect=run), \
                    patch.object(promotion, 'sign_folder') as sign:
                with self.assertRaises(subprocess.CalledProcessError):
                    self.context.compile(STABLE, key)
            sign.assert_not_called()

    def test_the_key_is_only_a_path_for_the_signer(self):
        with tempfile.TemporaryDirectory() as temporary:
            key = Path(temporary) / 'offline.key'
            key.write_text('ab' * 32)
            commands = []

            def run(command, **options):
                commands.append(' '.join(str(part) for part in command))
                return subprocess.CompletedProcess(command, 1 if command[0] == 'git' else 0)

            with patch.object(promotion.subprocess, 'run', side_effect=run), \
                    patch.object(promotion, 'sign_folder') as sign:
                self.context.compile(STABLE, key)
            sign.assert_called_once()
            self.assertNotIn('ab' * 32, ' '.join(commands))
            self.assertEqual(len([item for item in commands if str(key) in item]), 1)


class GateWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / '.github/workflows/promotion-gate.yml').read_text(encoding='utf-8')

    def test_only_runs_by_hand_from_the_stable_branch(self):
        triggers = self.text.split('\non:\n', 1)[1].split('\npermissions:', 1)[0]
        self.assertIn('workflow_dispatch:', triggers)
        for event in ('pull_request', 'push:', 'schedule', 'release:', 'workflow_run'):
            self.assertNotIn(event, triggers)
        self.assertIn("if: github.ref == 'refs/heads/main'", self.text)

    def test_has_least_privilege_and_cannot_write(self):
        self.assertIn('\npermissions: {}\n', self.text)
        self.assertNotIn(': write', self.text)
        self.assertIn('persist-credentials: false', self.text)

    def test_never_touches_secrets_or_release_commands(self):
        self.assertNotIn('secrets.', self.text)
        for word in ('--confirm', 'gh release', 'sign_release', ' publish '):
            self.assertNotIn(word, self.text)

    def test_serializes_runs_without_cancelling_an_approval(self):
        self.assertIn('group: promotion-gate', self.text)
        self.assertIn('cancel-in-progress: false', self.text)

    def test_inputs_reach_the_shell_only_through_the_environment(self):
        for line in self.text.splitlines():
            if line.strip().startswith('run:'):
                self.assertNotIn('${{', line)

    def test_defaults_to_validation_only(self):
        block = self.text.split('request_approval:', 1)[1].split('permissions', 1)[0]
        self.assertIn('default: false', block)
        self.assertIn('if: inputs.request_approval', self.text)
        self.assertIn('environment: stable-release', self.text)

    def test_actions_are_pinned_to_commits(self):
        for action in re.findall(r'uses:\s*(\S+)', self.text):
            self.assertRegex(action, r'@[0-9a-f]{40}$')

    def test_run_name_and_job_match_what_publication_looks_for(self):
        # Without the quotes YAML reads " # ..." as a comment and the digest never reaches the title.
        line = next(item for item in self.text.splitlines() if item.startswith('run-name:'))
        self.assertEqual(line, 'run-name: "Promotion ${{ inputs.beta_version }} @ ${{ inputs.stable_commit }} # '
                               '${{ inputs.artifacts_digest }}"')
        self.assertEqual(promotion.gate_title('B', 'C', 'D'), 'Promotion B @ C # D')
        self.assertIn('name: ' + promotion.GATE_JOB, self.text)


if __name__ == '__main__':
    unittest.main()
