import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('keyboard', ROOT / 'source/scripts/client/Driftkings/core/keyboard.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Event:
    def __init__(self): self.callbacks = []
    def __iadd__(self, callback): self.callbacks.append(callback); return self
    def __isub__(self, callback): self.callbacks.remove(callback); return self

class KeyboardTests(unittest.TestCase):
    def setUp(self):
        self.handler = SimpleNamespace(onKeyDown=Event(), onKeyUp=Event())
        self.blocked = False
        self.service = module.KeyboardService(self.handler, lambda: self.blocked)

    def test_no_import_time_subscription_single_listener_and_shutdown(self):
        received = []
        self.service.subscribe(received.append); self.service.subscribe(received.append)
        self.assertEqual(self.handler.onKeyDown.callbacks, [])
        self.service.onKey('before')
        self.service.start(); self.service.start()
        self.assertEqual(len(self.handler.onKeyDown.callbacks), 1)
        self.assertEqual(len(self.handler.onKeyUp.callbacks), 1)
        self.service.onKey('down'); self.service.onKey('up')
        self.service.stop(); self.service.stop()
        self.service.onKey('after')
        self.assertEqual(received, ['down', 'up'])
        self.assertEqual(self.handler.onKeyDown.callbacks, [])
        self.assertEqual(self.handler.onKeyUp.callbacks, [])
        self.assertEqual(self.service.callbacks, [])

    def test_settings_window_blocks_hotkeys_and_failed_handler_is_isolated(self):
        received = []
        def fail(event): raise RuntimeError('test')
        self.service.subscribe(fail); self.service.subscribe(received.append)
        self.service.start(); self.blocked = True
        self.service.onKey('editing')
        self.assertEqual(received, [])
        self.blocked = False
        with self.assertLogs('Driftkings.Keyboard', level='ERROR'): self.service.onKey('battle')
        self.assertEqual(received, ['battle'])
        self.service.unsubscribe(fail)
        self.service.onKey('next')
        self.assertEqual(received, ['battle', 'next'])

    def test_opening_settings_blocks_same_event_but_capture_stays_active(self):
        gameplay, capture = [], []
        def open_window(event):
            self.blocked = True
        self.service.subscribe(gameplay.append)
        self.service.subscribe(open_window, interface=True)
        self.service.subscribe(capture.append, interface=True)
        self.service.start()
        self.service.onKey('F10')
        self.service.onKey('new shortcut')
        self.assertEqual(gameplay, [])
        self.assertEqual(capture, ['F10', 'new shortcut'])
        self.service.stop()
        self.assertEqual(self.service.interface_callbacks, [])

    def test_closing_settings_does_not_forward_close_key_to_gameplay(self):
        received = []
        self.blocked = True
        def close_window(event): self.blocked = False
        self.service.subscribe(close_window, interface=True)
        self.service.subscribe(received.append)
        self.service.start()
        self.service.onKey('Escape')
        self.assertEqual(received, [])
        self.service.onKey('next')
        self.assertEqual(received, ['next'])

if __name__ == '__main__': unittest.main()
