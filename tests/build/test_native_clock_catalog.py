"""The native clock must be packaged and excluded from the legacy injector."""
import copy
import unittest
from unittest.mock import patch

from build_tools import generate_ui_catalog as catalog
from build_tools.validate_build_data import build_plan


class NativeClockCatalogTests(unittest.TestCase):
    def test_native_clock_assets_and_other_owners_are_in_the_correct_transport(self):
        data = catalog.read_catalog()
        generated = catalog.outputs()[catalog.BOOTSTRAP]
        block = generated.split(catalog.START, 1)[1].split(catalog.END, 1)[0]
        self.assertNotIn('DriftkingsHangarClock', block)
        legacy = [name for name, spec in data['GAMEFACE'].items()
                  if spec['owner'] is not None and name != 'DriftkingsHangarClock']
        self.assertEqual(len(legacy), 19)
        for name in legacy:
            self.assertIn(name, block)
        plan = build_plan(catalog.ROOT)
        targets = set(item['target'] for item in plan['assets'])
        self.assertIn('res/gui/gameface/mods/driftkings/main/clock_plugin.js', targets)
        self.assertEqual(len(plan['dependencies']), 2)

    def test_native_transport_cannot_be_enabled_for_another_feature(self):
        data = copy.deepcopy(catalog.read_catalog())
        data['GAMEFACE']['DriftkingsFooterLauncher']['transport'] = 'native_user_missions'
        data['GAMEFACE']['DriftkingsFooterLauncher']['plugin'] = data['GAMEFACE']['DriftkingsHangarClock']['plugin']
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'Native PoC is clock only'):
                catalog.validate()

    def test_unknown_transport_is_rejected(self):
        data = copy.deepcopy(catalog.read_catalog())
        data['GAMEFACE']['DriftkingsHangarClock']['transport'] = 'unknown'
        with patch.object(catalog, 'read_catalog', return_value=data):
            with self.assertRaisesRegex(ValueError, 'Unknown transport'):
                catalog.validate()
