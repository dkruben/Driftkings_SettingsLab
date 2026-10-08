from settings_support import settings_globals
import ast
import json
import queue
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))


def load_class(path, name, namespace):
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8-sig'))
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    settings_globals(namespace, 'core.player_ratings')
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


class RatingTests(unittest.TestCase):

    def test_api_rejection_is_reported_once_without_logging_request_parameters(self):
        warnings = []
        response = {'status': 'error', 'error': {'code': 407, 'message': 'INVALID_FIELDS'}}
        self.config.ID = 'PlayerPanelPro'
        self.config.data['performance']['requestTimeout'] = 5
        cls = load_class('source/scripts/client/Driftkings/core/player_ratings.py', 'Events', {
            'json': json, 'config': self.config,
            'urllib': types.SimpleNamespace(urlencode=lambda _: 'account_id=private'),
            'urllib2': types.SimpleNamespace(urlopen=lambda *a, **kw: types.SimpleNamespace(
                read=lambda: json.dumps(response).encode('utf-8'))),
            'logWarning': lambda *args: warnings.append(args)})
        self.assertIsNone(cls.request('eu', 'wot/account/info'))
        self.assertIsNone(cls.request('eu', 'wot/account/info'))
        self.assertEqual(len(warnings), 1)
        self.assertIn('INVALID_FIELDS', warnings[0])
        self.assertNotIn('private', repr(warnings))
        response.clear()
        response.update(status='ok', data={'sample': {'value': 1}})
        self.assertEqual(cls.request('eu', 'wot/account/info'), response['data'])





    def setUp(self):
        self.jobs, self.callbacks, self.hooks, self.applied = [], [], [], []
        self.now = 1000
        self.player = types.SimpleNamespace(arena=types.SimpleNamespace(vehicles={}), team=1)
        self.config = types.SimpleNamespace(data={'enabled': True, 'performance': {
            'cacheEnabled': True, 'cacheExpiry': 3600, 'minBattlesToShow': 10}})
        owner = self

        class Worker:
            def __init__(self, target, args): owner.jobs.append(args)
            def setDaemon(self, value): pass
            def start(self): pass

        ns = {'dependency': types.SimpleNamespace(descriptor=lambda _: None), 'IBattleSessionProvider': object,
              'json': json, 'Queue': queue.Queue, 'Empty': queue.Empty, 'ArenaDataProvider': object,
              'override': lambda *args: self.hooks.append(args), 'getPlayer': lambda: self.player,
              'config': self.config, 'time': types.SimpleNamespace(time=lambda: self.now),
              'threading': types.SimpleNamespace(Thread=Worker), 'logWarning': lambda *args: None,
              'BigWorld': types.SimpleNamespace(callback=lambda delay, fn: self.callbacks.append(fn) or len(self.callbacks),
                                                cancelCallback=lambda ident: None)}
        cls = load_class('source/scripts/client/Driftkings/core/player_ratings.py', 'Statistics', ns)
        self.namespace = ns
        self.stats = cls()
        self.stats.applyPlayerStats = lambda *args, **kw: self.applied.append((args, kw))

    def test_local_account_avoids_api_and_reapplies_after_respawn(self):
        self.stats._localAccount = '42'
        self.stats._localStats = {'info': {'local': True}, 'tanks': []}
        self.player.arena.vehicles = {1: {'accountDBID': 42}}
        self.stats.loadStats()
        self.stats.loadStats()
        self.assertEqual(self.jobs, [])
        self.assertEqual(len(self.applied), 1)
        self.player.arena.vehicles[2] = self.player.arena.vehicles.pop(1)
        self.stats.loadStats()
        self.assertEqual(len(self.applied), 2)
        self.stats.reset()
        self.stats.loadStats()
        self.assertEqual(len(self.applied), 3)
        self.assertEqual(self.jobs, [])

    def test_capture_local_dossier_and_fallback(self):
        values = {'getBattlesCount': 100, 'getWinsCount': 52, 'getDamageDealt': 100000,
                  'getFragsCount': 80, 'getSpottedEnemiesCount': 90,
                  'getCapturePoints': 5, 'getDroppedCapturePoints': 10}
        stats = types.SimpleNamespace(**{key: (lambda v=value: v) for key, value in values.items()})
        stats.getVehicles = lambda: {256: types.SimpleNamespace(battlesCount=100, wins=52)}
        stats.getMarkOfMasteryForVehicle = lambda tankID: 3
        items = types.SimpleNamespace(getAccountDossier=lambda: types.SimpleNamespace(getRandomStats=lambda: stats),
                                      stats=types.SimpleNamespace(globalRating=4000))
        self.namespace['ServicesLocator'] = types.SimpleNamespace(itemsCache=types.SimpleNamespace(
            isSynced=lambda: True, items=items))
        self.player.databaseID, self.player.arena = 42, None
        self.stats.captureOwnStats()
        self.assertEqual(self.stats._localStats['info']['statistics']['all']['wins'], 52)
        self.assertEqual(self.stats._localStats['tanks'][0]['mark_of_mastery'], 3)
        self.player.databaseID = 43
        items.getAccountDossier = lambda: None
        self.config.ID = 'test'
        self.stats.captureOwnStats()
        self.assertIsNone(self.stats._localStats)
        self.player.arena = types.SimpleNamespace(vehicles={1: {'accountDBID': 43}})
        self.stats.loadStats()
        self.assertEqual(self.jobs[0][0], ['43'])

    def test_batches_deduplication_and_unknown_accounts(self):
        self.player.arena.vehicles = {i: {'accountDBID': i} for i in range(1, 152)}
        self.player.arena.vehicles[200] = {'accountDBID': 0}
        self.player.arena.vehicles[201] = {'accountDBID': 1}
        self.stats.loadStats()
        self.stats.loadStats()
        self.assertEqual([len(args[0]) for args in self.jobs], [100, 51])
        self.assertEqual(len(self.callbacks), 1)

    def test_reset_drops_old_responses_without_installing_hooks_again(self):
        self.stats._responses.put((0, ['1'], {'1': {}}, {'1': []}))
        self.stats.reset()
        self.stats.pollStats()
        self.assertEqual(self.applied, [])
        self.assertEqual(len(self.hooks), 1)

    def test_valid_response_is_applied_on_poll(self):
        self.stats._pending.add('1')
        self.stats._responses.put((0, ['1'], {'1': {}}, {'1': []}))
        self.assertEqual(self.applied, [])
        self.stats.pollStats()
        self.assertEqual(len(self.applied), 1)
        self.assertFalse(self.stats._pending)

    def test_cache_expiry_is_not_extended_by_reuse(self):
        self.player.arena.vehicles = {1: {'accountDBID': 1}}
        self.stats.statsCache['1'] = {'info': {'x': 1}, 'tanks': []}
        self.stats.cacheTimestamp['1'] = 999
        self.stats.loadStats()
        self.assertFalse(self.jobs)
        self.assertEqual(self.applied[0][1], {'updateCache': False})
        self.now = 5000
        self.stats.loadStats()
        self.assertEqual(len(self.jobs), 1)

    def test_rows_hide_unknown_stats_and_escape_names(self):
        from xml.sax.saxutils import escape
        source = (ROOT / 'source/scripts/client/Driftkings/core/player_ratings.py').read_text(encoding='utf-8-sig')
        macro_tree = ast.parse('import re\nimport string\nfrom xml.sax.saxutils import escape\n' + source[source.index('MISSING ='):source.index('class Events')])
        macro_tree.body = [n for n in macro_tree.body if not isinstance(n, ast.ImportFrom) or not n.level]
        import math
        macros = {'getStatisticColor': lambda *args: '#00FF00', 'math': math}
        settings_globals(macros, 'core.player_ratings')
        exec(compile(macro_tree, 'rating_macros.py', 'exec'), macros)
        ns = {'BigWorld': types.SimpleNamespace(player=lambda: self.player), 'format_rating': macros['format_rating']}
        self.assertEqual(macros['format_rating']('{c:wn8} {wn8:.1f} {name}', {'wn8': 1234}, {'name': '<Nick>'}, True), '00FF00 1234.0 &lt;Nick&gt;')
        self.assertEqual(macros['format_rating']('{name} {wn8} {c:wn8}', {}, {'name': 'Bot'}, False), 'Bot \u2014 AAAAAA')
        self.assertEqual(macros['format_rating']('{c_wn8}', {'wn8': 1234}, {}, True), '00FF00')
        self.assertEqual(macros['tank_damage_ratio']({'battles': 10, 'damage_dealt': 15000}, 1000), 1.5)
        self.assertEqual(macros['tank_damage_ratio']({'battles': 10, 'damage_dealt': 0}, 1000), 0)
        self.assertEqual(macros['tank_damage_ratio']({'battles': 0, 'damage_dealt': 0}, 1000), '\u2014')
        fmt = macros['format_rating']
        self.assertEqual(fmt('{{c:kb}}', {'battles': 12000}, {}, True), '#00FF00')
        self.assertEqual(fmt('{{c:kb}}', {}, {}, False), '#AAAAAA')
        self.assertEqual(fmt('{{hp}}/{{hp-max}} {{hp-ratio:72}}', {'hp': 500, 'hp_max': 1000}, {}, False), '500/1000 36')
        self.assertEqual(fmt('{{hp-ratio:72}}', {'hp': 0, 'hp_max': 0}, {}, False), '0')
        self.assertEqual(fmt('{{hp-ratio:bad|--}}', {'hp': 50, 'hp_max': 100}, {}, False), '--')
        self.assertEqual(fmt('{{player?#FFDD33|{{c:system}}}}', {'player': True}, {}, False), '#FFDD33')
        self.assertEqual(fmt('{{player?#FFDD33|{{c:system}}}}', {'ally': True}, {}, False), '#96FF00')
        self.assertEqual(fmt('{{alive?{{ready?#FF|#80}}|#00}}', {'ready': False}, {'isAlive': True}, False), '#80')
        self.assertEqual(fmt('{{alive?{{ready?#FF|#80}}|#00}}', {}, {'isAlive': False}, False), '#00')
        self.assertEqual(fmt('{{r|{{r_size>2?----|--}}}}', {}, {}, False), '----')
        self.assertEqual(fmt('{{r|{{r_size>2?----|--}}}}', {'_rating': 'xwn8'}, {}, False), '--')
        self.assertEqual(fmt('{{name%.{{xvm-stat?10|15}}s~..}}', {}, {'name': 'abcdefghijklmnop'}, False), 'abcdefghijklmno..')
        self.assertEqual(fmt('{{name}}', {}, {'name': '<&{{r}}'}, False), '&lt;&amp;{{r}}')


if __name__ == '__main__':
    unittest.main()
