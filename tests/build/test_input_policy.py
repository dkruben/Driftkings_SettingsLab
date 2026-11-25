# -*- coding: utf-8 -*-
"""Canonical input policy: every tracked file has an explicit line-ending or binary rule, textual sources are LF,
and the only CRLF exceptions are the Windows command launchers."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CRLF_EXCEPTIONS = {'build_tools/run_build.cmd', 'debug.cmd', 'release.cmd'}


def git(*args, stdin=None):
    return subprocess.run(['git'] + list(args), cwd=str(ROOT), capture_output=True, text=True, input=stdin)


@unittest.skipUnless((ROOT / '.git').exists(), 'requires a git checkout')
class CanonicalInputPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        listing = git('ls-files')
        cls.paths = [line for line in listing.stdout.splitlines() if line]
        attributes = git('check-attr', '-z', 'eol', 'binary', '--stdin', stdin='\0'.join(cls.paths) + '\0')
        fields = attributes.stdout.split('\0')
        cls.attributes = {}
        for index in range(0, len(fields) - 2, 3):
            cls.attributes.setdefault(fields[index], {})[fields[index + 1]] = fields[index + 2]

    def test_every_tracked_file_has_an_explicit_rule(self):
        missing = [p for p in self.paths
                   if self.attributes.get(p, {}).get('binary') != 'set'
                   and self.attributes.get(p, {}).get('eol') not in ('lf', 'crlf')]
        self.assertEqual(missing, [])

    def test_textual_sources_are_lf_and_only_launchers_are_crlf(self):
        crlf = sorted(p for p in self.paths if self.attributes.get(p, {}).get('eol') == 'crlf')
        self.assertEqual(set(crlf), CRLF_EXCEPTIONS)

    def test_no_text_file_is_stored_with_crlf(self):
        listing = git('ls-files', '--eol').stdout.splitlines()
        stored_crlf = [line.split('\t', 1)[1] for line in listing if line.split()[0] == 'i/crlf']
        self.assertEqual(stored_crlf, [])

    def test_binary_resources_have_the_binary_rule(self):
        for path in self.paths:
            if path.lower().endswith(('.png', '.swc', '.ttf', '.wav', '.dds', '.ico', '.bnk', '.primitives')):
                self.assertEqual(self.attributes.get(path, {}).get('binary'), 'set', path)


if __name__ == '__main__':
    unittest.main()
