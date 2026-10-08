import ast
from copy import deepcopy
import datetime
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings._constants import MARKS_ON_GUN_BATTLE
from Driftkings.settings.settings_data import defaults


def load_class(path, name, namespace):
    tree = ast.parse((CLIENT / 'Driftkings' / path).read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
    exec(compile(tree, path, 'exec'), namespace)
    return namespace[name]


class MarksBattleCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'MarksOnGunBattle_stats.json'
        def load_json(component, name, values, directory, save=False, quiet=True):
            self.assertEqual(component, MARKS_ON_GUN_BATTLE.ID)
            self.assertEqual(Path(directory) / (name + '.json'), self.path)
            if save:
                self.path.write_text(json.dumps(values), encoding='utf-8')
            return json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else values
        self.io = Mock(side_effect=load_json)
        self.directory = Mock(return_value=self.tmp.name)
        self.ns = dict(loadJson=self.io, cache_directory=self.directory, datetime=datetime)
        cls = load_class('battle/gun_marks.py', 'MarksBattleCache', self.ns)
        self.cache = cls(MARKS_ON_GUN_BATTLE.ID)
        self.ns['marks_cache'] = self.cache

    def test_existing_records_keep_filename_and_survive_save_reload(self):
        original = {'123': {'tank': [64, 1500, 65, 1600, 739000, 739001]},
                    '456': {'another': [80, 2000, 81, 2100]}}
        self.path.write_text(json.dumps(original), encoding='utf-8')
        self.cache.load(quiet=False)
        self.directory.assert_called_once_with('gun_marks_battle')
        self.assertEqual(self.cache.values, original)
        self.cache.values['123']['tank'][3] = 1700
        self.cache.save()
        self.cache.load()
        self.assertEqual(self.cache.values['123']['tank'][3], 1700)
        self.assertEqual(self.cache.values['456'], original['456'])

    def test_worker_updates_old_record_and_new_vehicle_without_changing_preferences(self):
        config = NS(data=defaults(MARKS_ON_GUN_BATTLE.ID))
        before = deepcopy(config.data)
        self.ns['config'] = config
        cls = load_class('battle/gun_marks.py', 'Worker', self.ns)
        worker = cls.__new__(cls)
        worker.check_player_thread = lambda: '123'
        worker.name = 'tank'
        worker.battleDamage = worker.RADIO_ASSIST = worker.TRACK_ASSIST = worker.STUN_ASSIST = 0
        worker.movingAvgDamage = 1700
        worker.damageRating = 66
        self.cache.values = {'123': {'tank': [64, 1500, 65, 1600]}, '456': {'other': [1, 2, 3, 4]}}
        worker.requestCurData(66, 1700)
        self.assertEqual(self.cache.values['123']['tank'][:4], [65, 1600, 66, 1700])
        self.assertEqual(len(self.cache.values['123']['tank']), 6)
        worker.name = 'new'
        worker.requestNewData(50, 1200)
        self.assertEqual(self.cache.values['123']['new'][:4], [0, 0, 50, 1200])
        self.assertEqual(self.cache.values['456']['other'], [1, 2, 3, 4])
        self.assertEqual(config.data, before)
        self.io.assert_not_called()
        self.cache.save()
        self.assertEqual(json.loads(self.path.read_text(encoding='utf-8')), self.cache.values)

    def test_invalid_panel_value_does_not_reach_storage_or_cache(self):
        save = Mock()
        class Storage:
            def onApplySettings(self, values): save(values)
        ns = dict(ComponentSettings=Storage, MARKS_ON_GUN_BATTLE=MARKS_ON_GUN_BATTLE)
        cls = load_class('settings/templates/battle/gun_marks.py', 'MarksOnGunBattleSettings', ns)
        owner = cls()
        with self.assertRaises(ValueError):
            owner.onApplySettings({'panel': {'x': 'invalid'}})
        save.assert_not_called()
        owner.onApplySettings({'panel': {'x': '42', 'text': 'temporary'}})
        save.assert_called_once_with({'panel': {'x': 42.0}})
        self.io.assert_not_called()


if __name__ == '__main__':
    unittest.main()
