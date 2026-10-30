import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.update_release import changelog_lines


class ReleaseNotesTests(unittest.TestCase):
    def test_preserves_unicode_and_markdown_as_text(self):
        self.assertEqual(changelog_lines('## Correções\r\n\r\n- Câmara corrigida\n'),
                         ['## Correções', '- Câmara corrigida'])

    def test_rejects_empty_or_oversized_notes_without_truncating(self):
        for body in (None, '', ' \n', 'a' * 501, '\n'.join(['x'] * 51),
                     '\n'.join(['é' * 500] * 17)):
            with self.assertRaises(ValueError):
                changelog_lines(body)

    def test_accepts_exact_line_and_character_limits(self):
        lines = changelog_lines('\n'.join(['a' * 300] * 50))
        self.assertEqual(len(lines), 50)
        self.assertEqual(changelog_lines('x' * 500), ['x' * 500])
