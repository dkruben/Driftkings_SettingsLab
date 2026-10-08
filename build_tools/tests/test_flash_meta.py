"""Exercise DAAPI readiness, native ownership and contract failure detection."""
import ast
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace as NS

from meta_support import ROOT, meta_namespace

spec = importlib.util.spec_from_file_location('flash_contracts', ROOT / 'build_tools/check_flash_contracts.py')
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)


class FlashMetaTests(unittest.TestCase):
    def test_settings_callbacks_share_live_service_without_gameplay_imports(self):
        from Driftkings.settings.service import SettingsService
        from Driftkings.settings.settings_data import SettingsData
        from Driftkings._constants import ARMOR_CALCULATOR, DISPERSION_TIMER, FLIGHT_TIMER, OWN_HEALTH, SIXTH_SENSE
        data = SettingsData()
        namespace = meta_namespace()
        namespace['settings_service'] = SettingsService(data)
        for name, section in (('ArmorCalculatorMeta', ARMOR_CALCULATOR),
                              ('DispersionTimerMeta', DISPERSION_TIMER),
                              ('FlightTimeMeta', FLIGHT_TIMER),
                              ('OwnHealthMeta', OWN_HEALTH),
                              ('SixthSenseMeta', SIXTH_SENSE)):
            with self.subTest(component=section.ID):
                view = namespace[name](section.ID)
                config = NS(ID=section.ID, data={'enabled': False, 'x': 10})
                data.register(config)
                # Flash still needs the complete layout when the module is disabled.
                self.assertIs(view.getSettings(), config.data)
                config.data = {'enabled': True, 'x': 25}
                self.assertIs(view.getSettings(), config.data)
                replacement = NS(ID=section.ID, data={'enabled': True, 'x': 30})
                data.register(replacement)
                self.assertIs(view.getSettings(), replacement.data)

    def test_transports_guard_readiness_and_forward_arguments(self):
        namespace = meta_namespace()
        count = 0
        for path in (ROOT / 'source/scripts/client/Driftkings/meta/battle').glob('*.py'):
            for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
                if not isinstance(node, ast.ClassDef):
                    continue
                cls = namespace[node.name]
                for method in node.body:
                    if not isinstance(method, ast.FunctionDef):
                        continue
                    calls = contracts.flash_calls(method)
                    if not calls:
                        continue
                    with self.subTest(meta=node.name, method=method.name):
                        obj = cls('test') if issubclass(cls, namespace['BattleMeta']) else cls()
                        args = tuple(object() for _ in method.args.args[1:])
                        obj.ready, obj.flashObject = False, None
                        self.assertIsNone(getattr(obj, method.name)(*args))
                        obj.ready, obj.flashObject = True, Mock()
                        result = getattr(obj, method.name)(*args)
                        target = getattr(obj.flashObject, calls[0].func.attr)
                        target.assert_called_once_with(*args)
                        self.assertIs(result, target.return_value)
                        obj._dispose()
                        obj.flashObject = None
                        self.assertIsNone(getattr(obj, method.name)(*args))
                        count += 1
        self.assertGreater(count, 15)

    def test_hud_lifecycle_and_tab_independence(self):
        visibility = Mock()
        namespace = meta_namespace(visibility)
        hud = namespace['OverlayMeta']()
        hud.create()
        visibility.attach.assert_called_once_with(hud)
        hud._dispose()
        visibility.detach.assert_called_once_with(hud)
        self.assertEqual(hud.disposals, 1)
        visibility.reset_mock()
        tab = namespace['PlayersPanelMeta']()
        tab.create()
        tab._dispose()
        visibility.attach.assert_not_called()
        visibility.detach.assert_not_called()
        self.assertEqual(tab.disposals, 1)

    def test_actual_contracts(self):
        self.assertEqual(contracts.validate(), 9)

    def assert_bad_as(self, old, new, expected):
        original = Path.read_text
        def read(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            if path.name == 'DispersionTimerUI.as':
                self.assertIn(old, text)
                return text.replace(old, new)
            return text
        with patch.object(Path, 'read_text', read):
            with self.assertRaisesRegex(ValueError, expected):
                contracts.validate()

    def test_missing_as_method_is_rejected(self):
        self.assert_bad_as('function as_updateTimerText(', 'function renamedTimerText(', 'missing AS method as_updateTimerText')

    def test_wrong_argument_count_is_rejected(self):
        self.assert_bad_as('function as_updateTimerText(', 'function as_updateTimerText(required:Object, ', 'argument count differs')

    def test_missing_callback_is_rejected(self):
        original = Path.read_text
        def read(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            if path.name == 'DispersionTimerUI.as':
                text += '\npublic var missingCallback:Function;\n'
            return text
        with patch.object(Path, 'read_text', read):
            with self.assertRaisesRegex(ValueError, 'undeclared Flash callback missingCallback'):
                contracts.validate()
