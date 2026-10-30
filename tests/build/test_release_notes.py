import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.update_release import changelog_lines, require_tagged_revision, tag_commit


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


class PublishedTagTests(unittest.TestCase):
    def test_resolves_lightweight_and_peeled_annotated_tags(self):
        self.assertEqual(tag_commit('abc\trefs/tags/v1.0\n', 'v1.0'), 'abc')
        self.assertEqual(tag_commit('tagobj\trefs/tags/v1.0\ncommit\trefs/tags/v1.0^{}\n', 'v1.0'), 'commit')

    def test_rejects_missing_tag(self):
        with self.assertRaises(ValueError):
            tag_commit('abc\trefs/tags/v1.0-beta.1\n', 'v1.0')

    def test_refuses_a_checkout_other_than_the_tagged_commit(self):
        require_tagged_revision('a' * 40, 'a' * 40, 'v1.0')
        with self.assertRaises(ValueError):
            require_tagged_revision('a' * 40, 'b' * 40, 'v1.0')
