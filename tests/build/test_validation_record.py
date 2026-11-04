from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.validation_record import evaluate, IN_GAME, parse, render, stable_target

BETA, STABLE = '1.2.3-beta.4', '1.2.3'
COMMIT = 'a' * 40
PACKAGE = 'b' * 64


def approved(region='EU'):
    """A complete record for one region; the other regions stay NOT TESTED, as they would in practice."""
    lines = []
    for line in render(BETA, STABLE, COMMIT, '2.4.1.1', PACKAGE).splitlines():
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if cells[0] == region and 'NOT VALIDATED' in line:
            line = '| %s | VALIDATED | 2.4.1.5504 | 2026-11-01 | Tester | Windows 11 |' % region
        elif cells[0].startswith('auto.'):
            line = line.replace('NOT TESTED | -', 'PASS | run 1')
        elif len(cells) == 7 and cells[1] in ('YES', 'NO'):
            cells[3 + ('EU', 'NA', 'ASIA').index(region)] = 'PASS'
            line = '| ' + ' | '.join(cells) + ' |'
        elif cells[0] == 'Decisão':
            line = '| Decisão | APPROVED |'
        elif cells[0] == 'Aprovado por':
            line = '| Aprovado por | Maintainer |'
        elif cells[0] == 'Data':
            line = '| Data | 2026-11-02 |'
        elif cells[0] == 'Commit aprovado':
            line = '| Commit aprovado | %s |' % COMMIT
        elif cells[0] == 'Versão aprovada':
            line = '| Versão aprovada | %s |' % BETA
        lines.append(line)
    return '\n'.join(lines) + '\n'


def with_row(text, name, region, result, notes='-'):
    column = ('EU', 'NA', 'ASIA').index(region) + 3

    def change(match):
        cells = [cell.strip() for cell in match.group(0).strip('|').split('|')]
        cells[column], cells[6] = result, notes
        return '| ' + ' | '.join(cells) + ' |'

    return re.sub(r'^\| %s \|.*$' % re.escape(name), change, text, flags=re.MULTILINE)


def with_issue(text, row):
    return text.replace('| --- | --- | --- | --- | --- |\n\n## Aprovação', '| --- | --- | --- | --- | --- |\n%s\n\n## Aprovação' % row)


class TemplateTests(unittest.TestCase):
    def test_committed_template_matches_the_catalogue(self):
        path = ROOT / 'docs/releases/validation-template.md'
        self.assertEqual(path.read_bytes().decode('utf-8'), render())

    def test_a_new_record_claims_nothing(self):
        text = render(BETA, STABLE, COMMIT, '2.4.1.1', PACKAGE)
        self.assertNotIn('| PASS ', text)
        self.assertIn('| Decisão | PENDING |', text)
        with self.assertRaisesRegex(ValueError, 'Record decision is PENDING'):
            evaluate(text, BETA, STABLE)

    def test_committed_records_stay_readable_at_any_approval_state(self):
        paths = list((ROOT / 'docs/releases').glob('*-validation.md'))
        self.assertTrue(paths)
        for path in paths:
            identity = dict(parse(path.read_bytes().decode('utf-8'))['Identificação'])
            self.assertEqual(identity['Versão'] + '-validation.md', path.name)


class EvaluationTests(unittest.TestCase):
    def test_accepts_a_complete_approved_record(self):
        summary = evaluate(approved(), BETA, STABLE, COMMIT)
        self.assertEqual(summary['validatedRegions'], ['EU'])
        self.assertEqual(summary['notValidatedRegions'], ['NA', 'ASIA'])
        self.assertEqual((summary['commit'], summary['approvedBy']), (COMMIT, 'Maintainer'))

    def test_one_region_is_not_evidence_for_another(self):
        text = approved().replace('| NA | NOT VALIDATED | - | - | - | - |',
                                  '| NA | VALIDATED | 2.4.1.5504 | 2026-11-01 | Tester | Windows 11 |')
        with self.assertRaisesRegex(ValueError, 'not tested in validated region NA: install.clean'):
            evaluate(text, BETA, STABLE)

    def test_rejects_missing_or_invalid_approval(self):
        for old, new, reason in (
                ('| Decisão | APPROVED |', '| Decisão | PENDING |', 'decision is PENDING'),
                ('| Decisão | APPROVED |', '| Decisão | REJECTED |', 'decision is REJECTED'),
                ('| Decisão | APPROVED |', '| Decisão | OK |', 'Invalid decision'),
                ('| Aprovado por | Maintainer |', '| Aprovado por | <nome> |', 'no approver'),
                ('| Data | 2026-11-02 |', '| Data | 2026-13-40 |', 'no valid approval date'),
                ('| Data | 2026-11-02 |', '| Data | 2026-10-01 |', 'predates the tests'),
                ('| Commit aprovado | ' + COMMIT, '| Commit aprovado | ' + 'c' * 40, 'Approved commit differs'),
                ('| Versão aprovada | ' + BETA, '| Versão aprovada | 1.2.3-beta.3', 'Approved version differs')):
            with self.assertRaisesRegex(ValueError, reason):
                evaluate(approved().replace(old, new), BETA, STABLE)

    def test_rejects_another_commit_version_or_target(self):
        with self.assertRaisesRegex(ValueError, 'differs from'):
            evaluate(approved(), BETA, STABLE, 'd' * 40)
        with self.assertRaisesRegex(ValueError, 'Record identifies'):
            evaluate(approved(), '1.2.3-beta.5', STABLE)
        with self.assertRaisesRegex(ValueError, 'targets stable'):
            evaluate(approved(), BETA, '1.2.4')
        with self.assertRaisesRegex(ValueError, 'full lowercase SHA-1'):
            evaluate(approved().replace('| Commit | ' + COMMIT, '| Commit | abc1234'), BETA, STABLE)

    def test_blocking_failure_blocks_even_outside_validated_regions(self):
        with self.assertRaisesRegex(ValueError, r'Blocking check failed: battle.markers \(EU\)'):
            evaluate(with_row(approved(), 'battle.markers', 'EU', 'FAIL'), BETA, STABLE)
        with self.assertRaisesRegex(ValueError, r'Blocking check failed: battle.markers \(NA\)'):
            evaluate(with_row(approved(), 'battle.markers', 'NA', 'FAIL'), BETA, STABLE)

    def test_blocking_check_needs_a_reason_to_be_not_applicable(self):
        text = with_row(approved(), 'mode.random', 'EU', 'NOT APPLICABLE')
        with self.assertRaisesRegex(ValueError, 'NOT APPLICABLE in EU without a reason'):
            evaluate(text, BETA, STABLE)
        evaluate(with_row(approved(), 'mode.random', 'EU', 'NOT APPLICABLE', 'Mode closed on this server'), BETA, STABLE)

    def test_non_blocking_failure_requires_a_known_issue(self):
        failed = with_row(approved(), 'lobby.carousel', 'EU', 'FAIL')
        with self.assertRaisesRegex(ValueError, 'no known issue: lobby.carousel'):
            evaluate(failed, BETA, STABLE)
        text = with_issue(failed, '| I1 | MINOR | ACCEPTED | lobby.carousel | Wrong sort order |')
        self.assertEqual(evaluate(text, BETA, STABLE)['knownIssues'], ['I1'])

    def test_open_blocker_cannot_be_accepted(self):
        for state in ('OPEN', 'ACCEPTED'):
            text = with_issue(approved(), '| I1 | BLOCKER | %s | battle.markers | Crash |' % state)
            with self.assertRaisesRegex(ValueError, 'Blocking issue is not fixed: I1'):
                evaluate(text, BETA, STABLE)
        evaluate(with_issue(approved(), '| I1 | BLOCKER | FIXED | battle.markers | Crash |'), BETA, STABLE)

    def test_automatic_results_must_exist_and_carry_evidence(self):
        with self.assertRaisesRegex(ValueError, 'Automatic check was not run: auto.build'):
            evaluate(re.sub(r'(\| auto\.build \|.*?)PASS \| run 1', r'\1NOT TESTED | -', approved()), BETA, STABLE)
        with self.assertRaisesRegex(ValueError, 'Automatic check failed: auto.ci'):
            evaluate(re.sub(r'(\| auto\.ci \|.*?)PASS', r'\1FAIL', approved()), BETA, STABLE)
        with self.assertRaisesRegex(ValueError, 'auto.ci has no evidence'):
            evaluate(re.sub(r'(\| auto\.ci \|.*?)run 1', r'\1-', approved()), BETA, STABLE)

    def test_removing_or_relabelling_a_check_does_not_weaken_the_gate(self):
        name = next(item[0] for item in IN_GAME if item[1])
        removed = re.sub(r'^\| %s \|.*\n' % re.escape(name), '', approved(), flags=re.MULTILINE)
        with self.assertRaisesRegex(ValueError, 'Missing in-game check: ' + re.escape(name)):
            evaluate(removed, BETA, STABLE)
        relabelled = approved().replace('| %s | YES |' % name, '| %s | NO |' % name)
        with self.assertRaisesRegex(ValueError, 'differs from the catalogue'):
            evaluate(relabelled, BETA, STABLE)

    def test_rejects_unknown_results_and_layout_changes(self):
        with self.assertRaisesRegex(ValueError, 'Invalid result'):
            evaluate(with_row(approved(), 'battle.markers', 'EU', 'OK'), BETA, STABLE)
        with self.assertRaisesRegex(ValueError, 'Missing record section'):
            evaluate(approved().replace('## Regiões', '## Zonas'), BETA, STABLE)
        with self.assertRaisesRegex(ValueError, 'Unexpected table header'):
            evaluate(approved().replace('| Região | Decisão |', '| Região | Estado |'), BETA, STABLE)
        with self.assertRaisesRegex(ValueError, 'Not a validation record'):
            parse('# Notes\n')

    def test_html_comments_cannot_hide_or_add_rows(self):
        text = approved().replace('| Decisão | APPROVED |', '<!-- | Decisão | APPROVED | -->')
        with self.assertRaisesRegex(ValueError, 'Unexpected fields'):
            evaluate(text, BETA, STABLE)
        commented = approved().replace('## Aprovação final', '<!--\n| I9 | BLOCKER | OPEN | x | y |\n-->\n## Aprovação final')
        self.assertEqual(evaluate(commented, BETA, STABLE)['knownIssues'], [])
        hidden_row = approved().replace('| Data | 2026-11-02 |', '| Data | 2026-11-02 |\n<!-- | Data | 2026-11-03 | -->')
        evaluate(hidden_row, BETA, STABLE)

    def test_a_repeated_field_cannot_override_the_decision(self):
        text = approved().replace('| Decisão | APPROVED |', '| Decisão | PENDING |\n| Decisão | APPROVED |')
        with self.assertRaisesRegex(ValueError, 'Duplicate field'):
            evaluate(text, BETA, STABLE)

    def test_a_repeated_check_cannot_override_a_failure(self):
        row = re.search(r'^\| battle\.markers \|.*$', approved(), flags=re.MULTILINE).group(0)
        failed = with_row(row, 'battle.markers', 'EU', 'FAIL')
        with self.assertRaisesRegex(ValueError, 'Duplicate in-game check'):
            evaluate(approved().replace(row, failed + '\n' + row), BETA, STABLE)

    def test_every_region_must_stay_listed(self):
        text = approved().replace('| ASIA | NOT VALIDATED | - | - | - | - |\n', '')
        with self.assertRaisesRegex(ValueError, 'Every region must be listed'):
            evaluate(text, BETA, STABLE)

    def test_a_validated_region_needs_its_evidence(self):
        row = '| EU | VALIDATED | 2.4.1.5504 | 2026-11-01 | Tester | Windows 11 |'
        for broken, reason in (('| EU | VALIDATED | 2.4.1.5504 | 2026-11-01 | - | Windows 11 |', 'needs client build'),
                               ('| EU | VALIDATED | - | 2026-11-01 | Tester | Windows 11 |', 'needs client build'),
                               ('| EU | VALIDATED | 2.4.1.5504 | 2026-11-01 | Tester | <os> |', 'needs client build'),
                               ('| EU | VALIDATED | 2.4.1.5504 | ontem | Tester | Windows 11 |', 'no valid test date')):
            with self.assertRaisesRegex(ValueError, reason):
                evaluate(approved().replace(row, broken), BETA, STABLE)

    def test_the_package_digest_must_be_a_sha256(self):
        with self.assertRaisesRegex(ValueError, 'lowercase SHA-256'):
            evaluate(approved().replace(PACKAGE, 'abc'), BETA, STABLE)


class StableTargetTests(unittest.TestCase):
    def test_derives_the_stable_from_a_prerelease(self):
        self.assertEqual(stable_target('0.1.6-beta.1'), '0.1.6')
        self.assertEqual(stable_target('2.0.0-rc.3'), '2.0.0')

    def test_rejects_stable_and_unknown_versions(self):
        for value in ('0.1.5', '1.0.0-alpha.1', '1.0', 'v0.1.6-beta.1', '1.0.0-beta.1+build', '; rm -rf'):
            with self.assertRaises(ValueError):
                stable_target(value)


if __name__ == '__main__':
    unittest.main()
