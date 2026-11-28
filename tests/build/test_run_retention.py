"""Run retention against temporary fixtures only; the real build/runs directory is never touched."""
import contextlib
import subprocess
import datetime as dt
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from build_tools import run_retention as rr

NOW = dt.datetime(2026, 11, 26, 12, 0, tzinfo=dt.timezone.utc)
WOTMOD = b'package-bytes'


def stamp(days_ago, suffix='aaaaaaaa'):
    return (NOW - dt.timedelta(days=days_ago)).strftime('%Y%m%dT%H%M%SZ') + '-' + suffix


def settle(path, moment):
    """Give every file and folder of a fixture an explicit old modification time, never the real clock."""
    stamp_value = moment.timestamp()
    for dirpath, dirnames, filenames in os.walk(str(path)):
        for name in dirnames + filenames:
            os.utime(os.path.join(dirpath, name), (stamp_value, stamp_value))
    os.utime(str(path), (stamp_value, stamp_value))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


class RetentionFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        write(self.root / 'build_data/build_config.json',
              json.dumps({'targets': {'na999': {'realm': 'NA', 'build': '999'},
                                      'ct996': {'realm': 'CT', 'build': '996'}}}))
        self.runs = self.root / 'build/runs'
        self.runs.mkdir(parents=True)

    def make_run(self, name, *, mode='dev', target='ct996', status='success', workspace=True, state=True,
                 wotmod=WOTMOD):
        run = self.runs / name
        write(run / 'output/driftkings.wotmod', wotmod)
        report = dict(schema=1, run_id=name, status=status, mode=mode, target=target,
                      artifacts={'driftkings.wotmod': dict(sha256=rr.file_sha256(run / 'output/driftkings.wotmod'))})
        write(run / 'evidence/build-report.json', json.dumps(report))
        if state:
            write(run / 'evidence/state.json', json.dumps(dict(status='complete' if status == 'success' else 'failed')))
        if workspace:
            write(run / 'workspace/compiled/module.pyc', b'x' * 1000)
            write(run / 'workspace/python-job.json', b'{}')
            write(run / 'workspace/python-result.json', b'{}')
        settle(run, NOW - dt.timedelta(days=2))
        return run

    def decisions(self):
        return {d['run']: d for d in rr.plan(self.root, NOW)}

    def snapshot(self):
        return {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}


class SuccessfulRetentionTests(RetentionFixture):
    def test_latest_three_successful_runs_per_target_are_kept_with_wotmod_and_evidence(self):
        names = [stamp(10 - i, '%08x' % i) for i in range(5)]  # oldest first
        for name in names:
            self.make_run(name, target='ct996')
        found = self.decisions()
        for name in names[2:]:
            self.assertEqual(found[name]['action'], 'trim', name)
        for name in names[:2]:
            self.assertEqual(found[name]['action'], 'remove', name)

    def test_retention_is_independent_between_targets(self):
        na = [stamp(5 - i, 'b%07x' % i) for i in range(2)]
        ct = [stamp(9 - i, 'c%07x' % i) for i in range(4)]
        for name in na:
            self.make_run(name, target='na999')
        for name in ct:
            self.make_run(name, target='ct996')
        found = self.decisions()
        self.assertEqual([found[n]['action'] for n in na], ['trim', 'trim'])
        self.assertEqual(found[ct[0]]['action'], 'remove')
        self.assertEqual(found[ct[1]]['action'], 'trim')

    def test_successful_run_workspace_is_removed_after_verification_and_wotmod_kept(self):
        name = stamp(1, 'd0000001')
        run = self.make_run(name, target='na999')
        rr.execute(self.root, rr.plan(self.root, NOW), NOW)
        self.assertFalse((run / 'workspace').exists())
        self.assertEqual((run / 'output/driftkings.wotmod').read_bytes(), WOTMOD)
        self.assertTrue((run / 'evidence/build-report.json').is_file())


class FailedRetentionTests(RetentionFixture):
    def test_failed_run_age_boundaries(self):
        young = self.make_run(stamp(13, 'e0000001'), status='failed')
        edge = self.make_run(stamp(14, 'e0000002'), status='failed')
        old = self.make_run(stamp(15, 'e0000003'), status='failed')
        found = self.decisions()
        self.assertEqual(found[young.name]['action'], 'trim')
        self.assertEqual(found[edge.name]['action'], 'trim')
        self.assertEqual(found[old.name]['action'], 'remove')

    def test_failed_run_trim_keeps_only_job_and_result_files(self):
        run = self.make_run(stamp(2, 'e0000004'), status='failed')
        rr.execute(self.root, rr.plan(self.root, NOW), NOW)
        self.assertEqual(sorted(p.name for p in (run / 'workspace').iterdir()),
                         ['python-job.json', 'python-result.json'])
        self.assertTrue((run / 'evidence/build-report.json').is_file())


class ProtectionTests(RetentionFixture):
    def assertProtected(self, name, reason=None):
        decision = self.decisions()[name]
        self.assertEqual(decision['action'], 'protect', decision)
        if reason:
            self.assertIn(reason, decision['reason'])

    def test_active_or_incomplete_run_is_protected(self):
        name = stamp(1, 'f0000001')
        self.make_run(name, status='success')
        write(self.runs / name / 'evidence/state.json', json.dumps(dict(status='running')))
        self.assertProtected(name, 'active or incomplete')

    def test_release_run_is_protected(self):
        name = stamp(1, 'f0000002')
        self.make_run(name, mode='release', target='na999')
        self.assertProtected(name, 'release run')

    def test_validation_evidence_marker_protects_old_successful_run(self):
        names = [stamp(20 - i, 'f000001%d' % i) for i in range(5)]
        for name in names:
            self.make_run(name)
        write(self.runs / names[0] / 'evidence' / rr.RETAIN_MARKER, b'validation evidence')
        self.assertProtected(names[0], 'validation evidence')
        self.assertEqual(self.decisions()[names[1]]['action'], 'remove')

    def test_unknown_and_historical_directories_are_protected(self):
        for name in ('scratch', stamp(3, 'f0000003')):
            write(self.runs / name / 'compiled/unknown.bin', b'legacy')
            self.assertProtected(name)
        historical = stamp(4, 'f0000004')
        self.make_run(historical)
        write(self.runs / historical / 'build-report.json', b'{}')  # pre-unified root-level report
        self.assertProtected(historical, 'historical')

    def test_invalid_or_mismatched_metadata_is_protected(self):
        broken = self.make_run(stamp(1, 'f0000005'))
        write(broken / 'evidence/build-report.json', b'{not json')
        self.assertProtected(broken.name, 'unreadable run metadata')
        missing = self.make_run(stamp(1, 'f0000006'))
        (missing / 'evidence/build-report.json').unlink()
        self.assertProtected(missing.name, 'invalid run metadata')
        mismatched = self.make_run(stamp(1, 'f0000007'))
        write(mismatched / 'evidence/build-report.json', json.dumps(dict(schema=1, run_id='other', status='success',
                                                                        mode='dev', target='ct996')))
        self.assertProtected(mismatched.name, 'does not match its directory')

    def test_artifact_that_no_longer_matches_its_hash_is_protected(self):
        name = stamp(1, 'f0000008')
        run = self.make_run(name)
        write(run / 'output/driftkings.wotmod', b'tampered')
        self.assertProtected(name, 'recorded hash')

    def test_referenced_artifact_is_protected(self):
        name = stamp(1, 'f0000009')
        self.make_run(name, target='na999')
        write(self.root / 'build/releases/stable/0.1.8/driftkings.wotmod', WOTMOD)
        self.assertProtected(name, 'canonical release')


class CompletionAndRaceTests(RetentionFixture):
    def failed_with_state(self, days_ago, state):
        name = stamp(days_ago, '%08x' % days_ago)
        run = self.make_run(name, status='failed')
        write(run / 'evidence/state.json', json.dumps(state))
        settle(run, NOW - dt.timedelta(days=2))
        return name

    def test_trustworthy_completion_timestamp_governs_failed_run_age(self):
        recent = (NOW - dt.timedelta(days=2)).isoformat()
        name = self.failed_with_state(20, dict(status='failed', failure=dict(timestamp=recent)))
        self.assertEqual(self.decisions()[name]['action'], 'trim')

    def test_untrustworthy_completion_timestamp_falls_back_to_start_time(self):
        future = (NOW + dt.timedelta(days=1)).isoformat()
        name = self.failed_with_state(20, dict(status='failed', failure=dict(timestamp=future)))
        self.assertEqual(self.decisions()[name]['action'], 'remove')
        garbage = self.failed_with_state(21, dict(status='failed', failure=dict(timestamp='yesterday')))
        self.assertEqual(self.decisions()[garbage]['action'], 'remove')

    def test_recently_modified_run_is_protected_as_possible_active_build(self):
        name = stamp(1, 'ab000001')
        run = self.make_run(name)
        settle(run, NOW - dt.timedelta(minutes=5))
        self.assertEqual(self.decisions()[name]['action'], 'protect')
        self.assertIn('recently modified', self.decisions()[name]['reason'])

    def test_intermediates_named_by_preserved_evidence_are_kept(self):
        name = self.failed_with_state(3, dict(status='failed'))
        run = self.runs / name
        write(run / 'evidence/error.json', json.dumps(dict(message='see workspace/compiled/module.pyc')))
        settle(run, NOW - dt.timedelta(days=2))
        rr.execute(self.root, rr.plan(self.root, NOW), NOW)
        self.assertTrue((run / 'workspace/compiled/module.pyc').is_file())

    def test_directory_junction_is_protected_and_never_followed(self):
        if os.name != 'nt':
            self.skipTest('directory junctions are a Windows mechanism')
        outside = self.root / 'outside'
        write(outside / 'precious.bin', b'keep me')
        name = stamp(40, 'ac000001')
        run = self.make_run(name)
        junction = run / 'workspace' / 'junction'
        completed = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if completed.returncode != 0 or not junction.exists():
            self.skipTest('cannot create a directory junction on this host')
        decision = self.decisions()[name]
        self.assertEqual(decision['action'], 'protect')
        self.assertIn('links', decision['reason'])
        rr.execute(self.root, rr.plan(self.root, NOW), NOW)
        self.assertEqual((outside / 'precious.bin').read_bytes(), b'keep me')
        self.assertTrue(run.exists())


class PreviewAndApplyTests(RetentionFixture):
    def build_mixed_tree(self):
        old = [stamp(30 - i, 'a1000%03d' % i) for i in range(4)]
        for name in old:
            self.make_run(name)
        protected = stamp(31, 'a2000000')
        self.make_run(protected, mode='release')
        write(self.root / 'build/releases/stable/0.1.7/driftkings.wotmod', b'published')
        return old, protected

    def test_preview_does_not_mutate_the_filesystem(self):
        self.build_mixed_tree()
        before = self.snapshot()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rr.run_retention(self.root, apply=False, now=NOW)
        self.assertEqual(self.snapshot(), before)
        self.assertIn('PREVIEW', out.getvalue())
        self.assertIn('Estimated recoverable space', out.getvalue())

    def test_apply_removes_only_eligible_paths_and_keeps_protected_runs(self):
        old, protected = self.build_mixed_tree()
        with contextlib.redirect_stdout(io.StringIO()):
            rr.run_retention(self.root, apply=True, now=NOW)
        self.assertFalse((self.runs / old[0]).exists())
        self.assertTrue((self.runs / old[3]).exists())
        self.assertTrue((self.runs / protected / 'workspace').exists())
        self.assertEqual((self.root / 'build/releases/stable/0.1.7/driftkings.wotmod').read_bytes(), b'published')

    def test_path_containment_rejects_paths_outside_build_runs(self):
        runs = (self.root / 'build/runs').resolve()
        outside = self.root / 'build/releases/stable/0.1.7'
        with self.assertRaisesRegex(ValueError, 'escapes build/runs'):
            rr.require_inside(outside, runs)
        with self.assertRaisesRegex(ValueError, 'escapes build/runs'):
            rr.require_inside(runs / '..' / 'releases', runs)
        victim = self.make_run(stamp(1, 'a3000000'))
        forged = [dict(run=victim.name, action='remove', paths=[str(outside)], target=None, mode=None)]
        before = self.snapshot()
        with self.assertRaises(ValueError):
            rr.execute(self.root, forged, NOW)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(victim.exists())

    def test_symlinked_run_content_is_never_followed_or_deleted(self):
        outside = self.root / 'outside'
        write(outside / 'precious.bin', b'keep me')
        name = stamp(40, 'a4000000')
        run = self.make_run(name)
        try:
            os.symlink(str(outside), str(run / 'workspace' / 'link'), target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('symbolic links unavailable on this host')
        self.assertEqual(self.decisions()[name]['action'], 'protect')
        self.assertIn('links', self.decisions()[name]['reason'])
        rr.execute(self.root, rr.plan(self.root, NOW), NOW)
        self.assertEqual((outside / 'precious.bin').read_bytes(), b'keep me')
        self.assertTrue(run.exists())


if __name__ == '__main__':
    unittest.main()
