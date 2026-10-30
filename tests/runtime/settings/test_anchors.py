# -*- coding: utf-8 -*-
"""Name, id and color validators must end with \\Z: '$' also accepts a trailing newline."""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PANEL = os.path.join(ROOT, 'mod', 'res', 'scripts', 'client', 'driftkings', 'settings', 'panel')
DOLLAR_ANCHOR = re.compile(r"""re\.(?:match|compile|search|fullmatch)\(\s*r?['"]\^[^'"]*\$['"]""")


class AnchorTests(unittest.TestCase):
    def test_python_dollar_accepts_trailing_newline(self):
        self.assertTrue(re.match(r'^[a-z]+$', 'abc\n'))
        self.assertFalse(re.match(r'^[a-z]+\Z', 'abc\n'))

    def test_panel_validators_use_end_of_string_anchor(self):
        offenders = []
        for path in sorted(glob.glob(os.path.join(PANEL, '*.py'))):
            with open(path, 'rb') as stream:
                for number, line in enumerate(stream.read().decode('utf-8').splitlines(), 1):
                    if DOLLAR_ANCHOR.search(line):
                        offenders.append('%s:%d' % (os.path.basename(path), number))
        self.assertEqual(offenders, [])


if __name__ == '__main__':
    unittest.main()
