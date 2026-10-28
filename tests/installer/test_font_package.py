"""The native font package loads after its provider and ships compiled client code."""
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from build_tools.validate_build_data import build_plan

PACKAGE = ROOT / 'mod/res/mods/openwg_packages/driftkings_fonts'


class FontPackageTests(unittest.TestCase):
    def test_registration_is_ordered_and_idempotent(self):
        provider = ModuleType('openwg_fonts')
        calls = []
        provider.register_font = lambda path: calls.append(('font', path))
        provider.add_alias = lambda alias, face: calls.append(('alias', alias, face))
        with patch.dict(sys.modules, {'openwg_fonts': provider}):
            spec = importlib.util.spec_from_file_location('font_package', PACKAGE / '__init__.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertFalse(module.owg_module_loaded())
        self.assertEqual(calls, [])
        module.owg_module_init()
        module.owg_module_init()
        self.assertTrue(module.owg_module_loaded())
        self.assertEqual(len(calls), 12)
        self.assertTrue(all(call[0] == 'font' for call in calls[:5]))
        self.assertIn(('alias', 'xvm', 'DriftkingsFont'), calls)
        self.assertIn(('alias', 'dkm', 'DriftkingsFont'), calls)
        for _, name in calls[:5]:
            self.assertTrue((ROOT / 'mod/res' / name).is_file())
        module.owg_module_fini()
        self.assertFalse(module.owg_module_loaded())

    def test_native_dependency_and_compiled_package_are_in_build_plan(self):
        metadata = json.loads((PACKAGE / 'package.json').read_text())
        self.assertEqual(metadata['dependencies'], ['net.openwg.fonts'])
        plan = build_plan(ROOT)
        self.assertIn('res/mods/openwg_packages/driftkings_fonts/__init__.pyc',
                      [item['target'] for item in plan['python']])
        self.assertIn('res/mods/openwg_packages/driftkings_fonts/package.json',
                      [item['target'] for item in plan['assets']])
        self.assertIn('res/wotmods/net.openwg.common_2.8.5.0000.wotmod', plan['dependencies'])
