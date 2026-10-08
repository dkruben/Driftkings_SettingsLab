import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core.cache import CacheDirectories


class CacheDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = CacheDirectories(str(self.root))

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def test_all_disk_caches_share_one_root_and_preserve_legacy_data(self):
        sources = {
            'gun_marks_battle': ('MarksOnGunBattle/MarksOnGunBattle_stats.json', {'123': {'tank': [1, 2]}}),
            'gun_marks_hangar': ('MarksOnGunHangar/progress_123.json', {'vehicles': {'7': []}}),
            'stats': ('Stats/cache/wn8exp.json', {'data': [{'IDNum': 7}]}),
        }
        for module, (relative, data) in sources.items():
            original = self.write(relative, data)
            target = Path(self.cache.directory(module))
            self.assertEqual(target.parent, self.root / 'cache')
            self.assertEqual((target / original.name).read_bytes(), original.read_bytes())
            self.assertEqual(json.loads(original.read_text()), data)

    def test_existing_destinations_win_and_both_old_stats_locations_are_supported(self):
        self.write('Stats/cache/wn8exp.json', {'old': 1})
        self.write('DriftkingsStats/cache/wn8exp.json', {'older': 1})
        self.write('DriftkingsStats/cache/xte.json', {'fallback': 1})
        destination = self.write('cache/stats/wn8exp.json', {'current': 1})
        self.cache.directory('stats')
        self.assertEqual(json.loads(destination.read_text()), {'current': 1})
        self.assertEqual(json.loads((destination.parent / 'xte.json').read_text()), {'fallback': 1})

    def test_account_histories_remain_separate_and_settings_are_not_migrated(self):
        for account in (123, 456):
            self.write('MarksOnGunHangar/progress_%s.json' % account, {'account': account})
        self.write('MarksOnGunHangar/MarksOnGunHangar.json', {'enabled': True})
        self.write('MarksOnGunHangar/progress_bad.json', {'not': 'account history'})
        target = Path(self.cache.directory('gun_marks_hangar'))
        self.assertEqual(sorted(p.name for p in target.iterdir()), ['progress_123.json', 'progress_456.json'])
        self.assertEqual(json.loads((target / 'progress_123.json').read_text()), {'account': 123})
        self.assertEqual(json.loads((target / 'progress_456.json').read_text()), {'account': 456})

    def test_interrupted_migration_keeps_original_cleans_temporary_and_can_retry(self):
        original = self.write('Stats/cache/xtdb.json', {'safe': True})
        with patch('Driftkings.core.cache.os.rename', side_effect=OSError('simulated publication failure')):
            with self.assertLogs('Driftkings.Cache', level='ERROR'):
                target = Path(self.cache.directory('stats'))
        self.assertEqual(list(target.iterdir()), [])
        self.assertTrue(original.exists())
        self.cache.directory('stats')
        self.assertEqual((target / 'xtdb.json').read_bytes(), original.read_bytes())

    def test_unknown_or_traversal_module_cannot_create_directories(self):
        for module in ('../outside', '/absolute', 'unknown'):
            with self.assertRaises(KeyError):
                self.cache.directory(module)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
