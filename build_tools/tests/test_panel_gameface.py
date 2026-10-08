from settings_support import settings_globals
"""Bridge performance without the game runtime: execute the production updater."""
import ast
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class GamefacePayloadTests(unittest.TestCase):
    def test_child_model_exposes_command_and_view_binds_its_handler(self):
        path = Path(__file__).resolve().parents[2] / 'source/scripts/client/Driftkings/views/battle/panel_gameface.py'
        cls = next(n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n, ast.ClassDef))
        init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        nested = [n for n in init.body if isinstance(n, ast.ClassDef)]
        class Model:
            def __init__(self, properties, commands):
                self.properties, self.commands = properties, commands
                self._initialize()
            def _initialize(self): pass
            def _addStringProperty(self, *args): pass
            def _addCommand(self, name): return SimpleNamespace(name=name)
        original_event = (object(), Mock())
        class View:
            def __init__(self, model): self.model = model
            def getViewModel(self): return self.model
            def _getEvents(self): return (original_event,)
        handler = Mock()
        namespace = dict(ViewModel=Model, ViewImpl=View,
                         attach_assets=Mock(), bridge=SimpleNamespace(reportPerformance=handler))
        settings_globals(namespace, 'views.battle.panel_gameface', 'views.battle.player_ratings')
        exec(compile(ast.Module(body=nested, type_ignores=[]), str(path), 'exec'), namespace)
        model = namespace['RatingModel']()
        self.assertEqual(model.commands, 1)
        self.assertEqual(model.onPerformance.name, 'onPerformance')
        events = namespace['RatingView'](model)._getEvents()
        self.assertEqual(events, (original_event, (model.onPerformance, handler)))
        events[1][1]({'calls': 2})
        handler.assert_called_once_with({'calls': 2})

    def test_performance_command_logs_only_valid_enabled_samples(self):
        path = Path(__file__).resolve().parents[2] / 'source/scripts/client/Driftkings/views/battle/panel_gameface.py'
        cls = next(n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n, ast.ClassDef))
        logger = Mock()
        namespace = {'math': math, 'logging': SimpleNamespace(getLogger=lambda name: logger)}
        settings_globals(namespace, 'views.battle.panel_gameface', 'views.battle.player_ratings')
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), 'exec'), namespace)
        bridge = namespace['GamefaceLoading'].__new__(namespace['GamefaceLoading'])
        bridge.owner = SimpleNamespace(active=True, config=SimpleNamespace(data={
            'enabled': True, 'performance': {'diagnostics': True}}))
        sample = dict(calls=10, totalMs=25.5, maxMs=4.5, windowMs=5001, rows=140, reason='interval')
        bridge.reportPerformance(sample)
        self.assertEqual(logger.info.call_count, 1)
        args = logger.info.call_args[0]
        self.assertIn('Performance Gameface: screen=tab', args[0])
        self.assertEqual(args[1:], (10, 2.55, 4.5, 5001, 140, 'interval', 0, 0, 0))
        for bad in (None, {}, dict(sample, calls=0), dict(sample, calls=1.5),
                    dict(sample, totalMs='nan'), dict(sample, maxMs=float('inf')),
                    dict(sample, rows=-1), dict(sample, windowMs='bad'),
                    dict(sample, maxMs=100), dict(sample, reason='arbitrary log message'),
                    dict(sample, rowsDrawn='nan'), dict(sample, searches=-1)):
            bridge.reportPerformance(bad)
        self.assertEqual(logger.info.call_count, 1)
        bridge.owner.config.data['performance']['diagnostics'] = False
        bridge.reportPerformance(sample)
        bridge.owner.config.data['performance']['diagnostics'] = True
        bridge.owner.config.data['enabled'] = False
        bridge.reportPerformance(sample)
        bridge.owner.config.data['enabled'] = True
        bridge.owner.active = False
        bridge.reportPerformance(sample)
        self.assertEqual(logger.info.call_count, 1)
        bridge.owner.active = True
        bridge.reportPerformance(dict(sample, reason='hidden', rowsDrawn=2, rowsReused=138, searches=1))
        self.assertEqual(logger.info.call_count, 2)
        self.assertEqual(logger.info.call_args[0][-3:], (2, 138, 1))

    def test_unchanged_rows_skip_serialization_but_updates_and_clear_publish(self):
        path = Path(__file__).resolve().parents[2] / 'source/scripts/client/Driftkings/views/battle/panel_gameface.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        dumps = Mock(wraps=json.dumps)
        namespace = {'json': SimpleNamespace(dumps=dumps)}
        settings_globals(namespace, 'views.battle.panel_gameface', 'views.battle.player_ratings')
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), 'exec'), namespace)
        bridge = namespace['GamefaceLoading'].__new__(namespace['GamefaceLoading'])
        bridge.owner=SimpleNamespace(config=SimpleNamespace(data={'performance':{}}))
        published = []

        class Model:
            def transaction(self): return self
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def _setString(self, index, value): published.append(json.loads(value))

        class View:
            pass

        view = View()
        allies = [SimpleNamespace(getVehicleId=lambda: 1)]
        view.viewModel = SimpleNamespace(playerList=SimpleNamespace(getAllies=lambda: allies, getEnemies=lambda: []))
        bridge.children = {view: {'screen': 'tab', 'child': SimpleNamespace(getViewModel=lambda: Model())}}
        row = {'id': 1, 'ally': True, 'aliases': ['Test'], 'tab': {'enabled': True, 'formatLeftNick': 'Test 1000'}}
        for _ in range(100): bridge.update(True, [row])
        self.assertEqual(dumps.call_count, 1)
        self.assertEqual(len(published), 1)
        updated = dict(row, tab={'enabled': True, 'formatLeftNick': 'Test 2000'})
        bridge.update(True, [updated])
        self.assertEqual(published[-1]['rows'][0]['cfg']['formatLeftNick'], 'Test 2000')
        allies[:] = []
        bridge.update(True, [updated])
        self.assertEqual(published[-1]['order']['left'], [])
        bridge.children[view]['visible']=False
        self.assertEqual(bridge.active_screens(),set())
        bridge.update(True,[updated])
        self.assertFalse(published[-1]['enabled'])
        hidden_count=dumps.call_count
        bridge.update(True,[row])
        self.assertEqual(dumps.call_count,hidden_count)
        bridge.clear()
        self.assertFalse(published[-1]['enabled'])
        self.assertEqual(published[-1]['rows'], [])
        self.assertEqual(dumps.call_count, 4)
        self.assertFalse(bridge.children)
