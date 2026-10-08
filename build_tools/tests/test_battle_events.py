import importlib.util
import ast
import logging
from pathlib import Path
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Event:
    def __init__(self): self.callbacks = []
    def __iadd__(self, fn): self.callbacks.append(fn); return self
    def __isub__(self, fn): self.callbacks.remove(fn); return self


class BattleEventsTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((ROOT / 'source/scripts/client/Driftkings/core/battle_events.py').read_text())
        tree.body = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        self.hooks = []
        self.input = types.SimpleNamespace(onKeyDown=Event(), onKeyUp=Event())
        spec = importlib.util.spec_from_file_location('keyboard_test', ROOT / 'source/scripts/client/Driftkings/core/keyboard.py')
        keyboard_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(keyboard_module)
        self.keyboard = keyboard_module.KeyboardService(self.input, lambda: False)
        self.keyboard.start()
        ns = {'LOG': logging.getLogger('test.events'), 'PlayerAvatar': object, 'Vehicle': object, 'VehicleGunRotator': object,
              'ArenaVehiclesPlugin': object, 'override': lambda *args: self.hooks.append(args),
              'g_events': types.SimpleNamespace(onBattleLoaded=Event()),
              'keyboard': self.keyboard}
        exec(compile(tree, 'battle_events.py', 'exec'), ns)
        self.hub = ns['BattleEvents']()
        self.arena = types.SimpleNamespace(onVehicleKilled=Event())
        self.avatar = types.SimpleNamespace(arena=self.arena)

    def test_shared_hooks_and_keyboard_are_registered_once(self):
        self.hub.acquire('a'); self.hub.acquire('a'); self.hub.acquire('b')
        self.assertEqual(len(self.hooks), 6)
        self.assertEqual(len(self.input.onKeyDown.callbacks), 1)
        self.hub.release('a')
        self.assertEqual(len(self.input.onKeyDown.callbacks), 1)
        self.hub.release('b'); self.hub.release('b')
        self.assertEqual(self.keyboard.callbacks, [])
        self.assertEqual(len(self.input.onKeyDown.callbacks), 1)
        self.hub.acquire('c')
        self.assertEqual(len(self.hooks), 6)

    def test_arena_cleanup_and_original_results(self):
        calls = []
        self.hub.acquire('a')
        self.hub.ended.connect(lambda: calls.append('end'))
        for _ in range(2):
            self.assertEqual(self.hub.startGUI(lambda avatar: 42, self.avatar), 42)
            self.hub.startGUI(lambda avatar: None, self.avatar)
            self.assertEqual(len(self.arena.onVehicleKilled.callbacks), 1)
            self.assertEqual(self.hub.destroyGUI(lambda avatar: calls.append('original') or 7, self.avatar), 7)
            self.assertEqual(self.arena.onVehicleKilled.callbacks, [])
        self.assertEqual(calls, ['end', 'original', 'end', 'original'])

    def test_listener_failure_is_isolated(self):
        results = []
        def bad(*args): raise RuntimeError('test')
        self.hub.health.connect(bad)
        self.hub.health.connect(lambda *args: results.append(args))
        self.hub.acquire('a')
        with self.assertLogs('test.events', level='ERROR'):
            result = self.hub.healthChanged(lambda *args: 'original', types.SimpleNamespace(id=9), 100, 200, 0, 1)
        self.assertEqual(result, 'original')
        self.assertEqual(results, [(9, 100)])




    def test_dispersion_preserves_game_result_and_unsubscribes(self):
        received = []
        rotator = object()
        self.hub.acquire('timer')
        self.hub.dispersion.connect(received.append)
        result = self.hub.dispersionChanged(lambda *args, **kwargs: 73, rotator, 1, test=True)
        self.assertEqual(result, 73)
        self.assertEqual(received, [rotator])
        self.hub.dispersion.disconnect(received.append)
        self.hub.dispersionChanged(lambda *args: 73, rotator)
        self.assertEqual(received, [rotator])

    def test_info_panel_two_battles_and_component_shutdown(self):
        from unittest.mock import Mock
        from Driftkings._constants import INFO_PANEL
        from Driftkings.settings.service import SettingsService
        from Driftkings.settings.settings_data import SettingsData
        tree = ast.parse((ROOT / 'source/scripts/client/Driftkings/battle/info_panel.py').read_text(encoding='utf-8-sig'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'InfoPanel')
        cls.bases = []
        cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in
                    ('start', 'stop', 'onBattleStarted', 'onBattleEnded', 'onBattleKey')]
        flash = Mock()
        service = SettingsService(SettingsData())
        ns = {'battleEvents': self.hub, 'g_flash': flash, 'settings_service': service, 'INFO_PANEL': INFO_PANEL}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), 'info_panel', 'exec'), ns)
        owner = ns['InfoPanel']()
        owner._active = owner._inBattle = False
        owner.reset = Mock()
        owner.keyPressed = Mock()
        owner.onSettingsChanged = Mock()
        owner.start(); owner.start()
        owner.onBattleKey('hangar')
        owner.keyPressed.assert_not_called()
        for _ in range(2):
            self.hub.started.emit(); self.hub.started.emit()
            self.hub.key.emit('battle')
            self.hub.ended.emit()
            self.hub.key.emit('hangar')
        self.assertEqual(flash.startBattle.call_count, 2)
        self.assertEqual(flash.stopBattle.call_count, 2)
        self.assertEqual(owner.reset.call_count, 2)
        self.assertEqual(owner.keyPressed.call_count, 2)
        owner.stop(); owner.stop()
        self.assertFalse(self.hub.owners)
        self.assertFalse(service.onModSettingsChanged._listeners)
        self.assertEqual(self.hub.key.listeners, [])
        self.hub.started.emit()
        self.assertEqual(flash.startBattle.call_count, 2)

    def test_info_panel_cleanup_releases_flash_even_if_reset_fails(self):
        from unittest.mock import Mock
        tree = ast.parse((ROOT / 'source/scripts/client/Driftkings/battle/info_panel.py').read_text(encoding='utf-8-sig'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'InfoPanel')
        cls.bases = []
        cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'onBattleEnded']
        flash = Mock()
        ns = {'g_flash': flash}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), 'info_panel', 'exec'), ns)
        owner = ns['InfoPanel']()
        owner.reset = Mock(side_effect=RuntimeError('reset failed'))
        with self.assertRaises(RuntimeError): owner.onBattleEnded()
        flash.stopBattle.assert_called_once()
        self.assertFalse(owner._inBattle)

    def test_battle_keys_use_core_and_stop_after_last_owner(self):
        received = []
        self.hub.key.connect(received.append)
        self.hub.acquire('battle')
        self.keyboard.onKey('down')
        self.hub.release('battle')
        self.keyboard.onKey('after')
        self.assertEqual(received, ['down'])
        self.keyboard.stop()
        self.assertEqual(self.input.onKeyDown.callbacks, [])
