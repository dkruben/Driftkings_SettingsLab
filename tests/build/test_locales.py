import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.validate_locales import english_prose, validate_catalogs


class LocaleTests(unittest.TestCase):
    def test_catalogs_are_complete_and_keep_no_english_prose(self):
        self.assertEqual(validate_catalogs(ROOT)['status'], 'passed')
        # New English strings must be translated in every catalog in the same change.
        self.assertEqual(english_prose(ROOT), [])


if __name__ == '__main__':
    unittest.main()
