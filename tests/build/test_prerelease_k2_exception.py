# -*- coding: utf-8 -*-
"""Beta-only K2 prerelease exception: documented, beta-only, never used by stable promotion."""
import unittest
from pathlib import Path

from build_tools.publish_release import PROVENANCE_ALLOWLIST, require_prerelease_exception_channel, require_publication_provenance
from build_tools.validation_record import (evaluate, k2_prerelease_exception_documented)

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / 'docs/releases/0.1.7-beta.2-validation.md'
K2_PROBLEM = 'Blocking issue is not fixed: K2'
GOOD = ('Exceção de prerelease K2 autorizada pelo proprietário. Motivo: updater só consulta releases publicadas. '
        'Data da autorização: 2026-11-25.')


def problems_of(text, version, **options):
    try:
        evaluate(text, version, **options)
        return []
    except ValueError as error:
        return [item.strip() for item in str(error).split(';') if item.strip()]


class PrereleaseK2ExceptionTests(unittest.TestCase):
    def test_exception_needs_marker_reason_and_authorization_date(self):
        self.assertTrue(k2_prerelease_exception_documented(GOOD))
        self.assertFalse(k2_prerelease_exception_documented('Exceção de prerelease K2 autorizada pelo proprietário.'))
        self.assertFalse(k2_prerelease_exception_documented('Motivo: updater. Data da autorização: 2026-11-25.'))
        self.assertFalse(k2_prerelease_exception_documented('Atualização ainda não executada.'))

    def test_only_the_prerelease_mode_accepts_the_documented_open_k2_row(self):
        text = RECORD.read_text(encoding='utf-8')
        # The record documents the exception, so only the prerelease mode may waive K2.
        self.assertIn(K2_PROBLEM, problems_of(text, '0.1.7-beta.2'))
        self.assertNotIn(K2_PROBLEM, problems_of(text, '0.1.7-beta.2', prerelease_k2=True))

    def test_undocumented_open_k2_is_never_waived(self):
        text = RECORD.read_text(encoding='utf-8')
        stripped = text.replace('Exceção de prerelease K2 autorizada pelo proprietário', 'Nota')
        self.assertIn(K2_PROBLEM, problems_of(stripped, '0.1.7-beta.2', prerelease_k2=True))

    def test_fixed_k2_needs_no_exception_and_stays_checked_by_the_default_evaluator(self):
        text = RECORD.read_text(encoding='utf-8')
        fixed = text.replace('| K2 | BLOCKER | OPEN |', '| K2 | BLOCKER | FIXED |')
        self.assertNotIn(K2_PROBLEM, problems_of(fixed, '0.1.7-beta.2'))

    def test_stable_promotion_never_uses_the_exception(self):
        # The default evaluator (used by promote_release.py) must keep rejecting the open K2 row.
        text = RECORD.read_text(encoding='utf-8')
        self.assertIn(K2_PROBLEM, problems_of(text, '0.1.7-beta.2'))
        with self.assertRaisesRegex(ValueError, 'only allowed for beta'):
            require_prerelease_exception_channel('stable', True)

    def test_flag_is_accepted_for_beta_and_absent_for_stable(self):
        require_prerelease_exception_channel('beta', True)
        require_prerelease_exception_channel('stable', False)
        require_prerelease_exception_channel('beta', False)
        with self.assertRaisesRegex(ValueError, 'only allowed for beta'):
            require_prerelease_exception_channel('stable', True)


class FakeGit(object):
    """Stands in for git: is-ancestor answers, and diff lists the given changed paths."""
    def __init__(self, ancestor=True, changed=()):
        self.ancestor, self.changed = ancestor, list(changed)

    def __call__(self, *args):
        class Result(object):
            pass
        result = Result()
        if args[0] == 'merge-base':
            result.returncode, result.stdout = (0 if self.ancestor else 1), ''
        else:
            result.returncode, result.stdout = 0, chr(10).join(self.changed)
        return result


BUILT, HEAD = '2e7ceb06d672995280d93a8528659ee52f45e3a8', 'ec3cf9480000000000000000000000000000abcd'


class ProvenanceExceptionTests(unittest.TestCase):
    def test_same_commit_and_allowlisted_descendant_pass(self):
        require_publication_provenance(FakeGit(), BUILT, BUILT, False)
        require_publication_provenance(FakeGit(changed=sorted(PROVENANCE_ALLOWLIST)), BUILT, HEAD, False)

    def test_packaging_runtime_resource_and_compile_changes_are_rejected(self):
        for path in ('mod/res/scripts/client/driftkings/__init__.py', 'build_data/release.json',
                     'build_tools/compiler.py', 'build_tools/publish_release.py', 'mod/res/gui/x.swf',
                     'build_data/build_config.json', 'requirements.txt'):
            changed = [path] if path not in PROVENANCE_ALLOWLIST else [path, 'mod/res/scripts/client/driftkings/__init__.py']
            with self.assertRaisesRegex(ValueError, 'outside the provenance allowlist'):
                require_publication_provenance(FakeGit(changed=changed), BUILT, HEAD, False)

    def test_built_commit_must_be_an_ancestor_and_checkout_must_be_clean(self):
        with self.assertRaisesRegex(ValueError, 'not an ancestor'):
            require_publication_provenance(FakeGit(ancestor=False, changed=sorted(PROVENANCE_ALLOWLIST)), BUILT, HEAD, False)
        with self.assertRaisesRegex(ValueError, 'uncommitted changes'):
            require_publication_provenance(FakeGit(changed=sorted(PROVENANCE_ALLOWLIST)), BUILT, HEAD, True)

    def test_the_allowlist_names_only_publication_and_validation_files(self):
        self.assertEqual(sorted(PROVENANCE_ALLOWLIST), sorted([
            'build_tools/publish_release.py', 'build_tools/validation_record.py',
            'tests/build/test_prerelease_k2_exception.py', 'docs/releases/0.1.7-beta.2-validation.md']))
        for path in PROVENANCE_ALLOWLIST:
            self.assertFalse(path.startswith(('mod/', 'res/', 'installer/')), path)
            self.assertFalse(path.endswith(('compiler.py', 'package_tools.py', 'build_config.json', 'release.json')), path)


if __name__ == '__main__':
    unittest.main()
