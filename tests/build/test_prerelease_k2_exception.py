# -*- coding: utf-8 -*-
"""Beta-only K2 prerelease exception: documented, beta-only, never used by stable promotion."""
import unittest
from pathlib import Path

from build_tools.publish_release import require_prerelease_exception_channel
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


if __name__ == '__main__':
    unittest.main()
