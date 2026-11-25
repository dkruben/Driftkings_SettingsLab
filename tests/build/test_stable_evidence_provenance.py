# -*- coding: utf-8 -*-
"""Stable promotion evidence: record and CI come from an authorized descendant on main, 0.1.7 cycle only."""
import unittest
from unittest import mock

from build_tools import promote_release as promote

STABLE = '9a13d0833a4b4c35132460379b671d09cbd45da8'
TIP = '3afb37dea46c007270ef5f46a23260502ec2c5b0'
BETA = '2e7ceb06d672995280d93a8528659ee52f45e3a8'
IDENTITY = dict(beta='0.1.7-beta.2', stable='0.1.7', tag='v0.1.7', commit=STABLE)
INTERVENING = ['.github/workflows/python-package.yml', 'build_tools/publish_release.py',
               'build_tools/validation_record.py', 'docs/releases/0.1.7-beta.2-validation.md',
               'tests/build/test_prerelease_k2_exception.py']


class FakeContext(object):
    repository = 'dkruben/Driftkings_SettingsLab'

    def __init__(self, ancestor=True, changed=INTERVENING, tip=TIP):
        self.ancestor, self.changed, self.tip = ancestor, list(changed), tip
        self.reads = []

    def git(self, *args):
        if args[0] == 'rev-parse':
            return self.tip
        if args[0] == 'diff':
            return '\n'.join(self.changed)
        raise AssertionError(args)

    def is_ancestor(self, ancestor, commit):
        return self.ancestor

    def read(self, commit, path):
        self.reads.append(commit)
        return 'record'


class EvidenceCommitTests(unittest.TestCase):
    def test_authorized_descendant_with_allowlisted_changes_is_accepted(self):
        self.assertEqual(promote.authorized_evidence_commit(FakeContext(), IDENTITY), TIP)

    def test_functional_change_after_the_stable_commit_is_rejected(self):
        for path in ('mod/res/scripts/client/driftkings/__init__.py', 'build_data/build_config.json',
                     'build_tools/compiler.py', 'installer/setup/wizard.iss', 'res/configs/driftkings/default/main.json'):
            with self.assertRaisesRegex(ValueError, 'outside the evidence allowlist'):
                promote.authorized_evidence_commit(FakeContext(changed=INTERVENING + [path]), IDENTITY)

    def test_stable_commit_must_be_an_ancestor_of_main(self):
        with self.assertRaisesRegex(ValueError, 'not an ancestor'):
            promote.authorized_evidence_commit(FakeContext(ancestor=False), IDENTITY)

    def test_the_exception_is_limited_to_the_0_1_7_cycle(self):
        other = dict(IDENTITY, stable='0.1.8')
        with self.assertRaisesRegex(ValueError, 'only to the 0.1.7 release cycle'):
            promote.authorized_evidence_commit(FakeContext(), other)

    def test_the_stable_commit_itself_is_not_changed_by_the_exception(self):
        self.assertEqual(IDENTITY['commit'], STABLE)


class RecordAndCiTests(unittest.TestCase):
    def test_record_is_read_from_the_evidence_commit_not_the_stable_commit(self):
        context = FakeContext()
        with mock.patch.object(promote, 'evaluate', return_value={'ok': True}):
            summary = promote.check_record(context, IDENTITY)
        self.assertEqual(context.reads, [TIP])
        self.assertEqual(summary['evidenceCommit'], TIP)

    def test_ci_is_checked_on_the_evidence_commit_and_reported_as_tested(self):
        seen = []

        def fake_green(repository, commit, query):
            seen.append(commit)
            return ['https://example.invalid/run']
        record = {'evidenceCommit': TIP}
        with mock.patch.object(promote, 'require_green_ci', side_effect=fake_green):
            result = promote.check_ci(FakeContext(), IDENTITY, record)
        self.assertEqual(seen, [TIP])
        self.assertEqual(result['tested'], TIP)
        self.assertNotEqual(result['tested'], STABLE)

    def test_beta_commit_is_an_ancestor_of_the_evidence_commit_by_the_recorded_history_check(self):
        # check_history still requires the approved beta commit to be an ancestor of the stable commit.
        context = FakeContext()
        record = {'commit': BETA}
        self.assertTrue(promote.check_history(context, IDENTITY, record))


if __name__ == '__main__':
    unittest.main()
