import ast
import json
import sys
import unittest
import weakref
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

from settings_support import settings_globals

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings._constants import HANGAR_OPTIONS, MINIMAP_PLUGINS
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults
from Driftkings.views.hangar.common import HangarController, publish_card


class Model:
    def __init__(self):
        self.values = []
        self.fail = False

    def transaction(self): return self
    def __enter__(self): return self
    def __exit__(self, *args):
        if self.fail: raise RuntimeError('failed transaction')
    def _setString(self, index, value): self.values.append(json.loads(value))


class ViewBase:
    def __init__(self, **kwargs): self.model = Model()
    def getViewModel(self): return self.model
    def _onLoading(self, *args, **kwargs): pass
    def _finalize(self): pass


class Parent:
    pass


class HangarOptionsSettingsTests(unittest.TestCase):
    def setUp(self):
        self.config = NS(ID='HangarOptions', data=defaults('HangarOptions'))
        self.config.data['enabled'] = self.config.data['clock'] = True
        self.service = SettingsService(SettingsData())
        self.battle_pass = Mock()
        self.battle_pass.isVisible.return_value = True
        self.missions = Mock()
        self.dependencies = Mock(side_effect=lambda key: self.battle_pass if key == 'pass' else self.missions)
        self.component = NS(config=self.config)
        self.ns = dict(config=self.config, dependency=NS(instance=self.dependencies),
                       IBattlePassService='pass', IUserMissionWidgetService='missions',
                       BattlePassPresenter=NS(GROUP='battle_pass'), logError=Mock(),
                       HangarController=HangarController, publish_card=publish_card,
                       weakref=weakref, ViewComponent=ViewBase, ClockModel=Mock(),
                       _component=lambda: self.component)
        settings_globals(self.ns, 'lobby.hangar_options', 'views.hangar.hangar_options')
        self.ns['settings_service'] = self.service
        names = {'HangarOptionsController', '_cfg', '_isSpecialBattleVehicle', 'new_isAmmoFull',
                 'ClockController', 'ClockView'}
        for relative in ('lobby/hangar_options.py', 'views/hangar/hangar_options.py'):
            path = ROOT / 'source/scripts/client/Driftkings' / relative
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            tree.body = [node for node in ast.walk(tree)
                         if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names]
            for node in tree.body: node.decorator_list = []
            exec(compile(tree, str(path), 'exec'), self.ns)
        self.options = self.ns['HangarOptionsController']()
        self.clock = self.component.g_clockController = self.ns['ClockController']()
        self.options.start()
        self.clock.start()
        self.addCleanup(self.options.stop)
        self.addCleanup(self.clock.stop)
        self.parent = Parent()
        self.clock.setVisible(self.parent, True)
        self.view = self.ns['ClockView'](self.parent, 1)
        self.view._onLoading()

    def apply(self, values):
        self.service.apply(self.config, values, persist=False)

    def test_clock_settings_do_not_touch_services_and_ignore_unrelated_changes(self):
        self.apply({'clockX': 123})
        self.assertEqual(self.view.model.values[-1]['config']['clockX'], 123)
        self.dependencies.assert_not_called()
        count = len(self.view.model.values)
        self.service.onModSettingsChanged.emit(MINIMAP_PLUGINS.NAME, {'enabled': False})
        self.apply({'lowAmmoPercentage': 77, 'showGeneralChatButton': False})
        self.assertEqual(len(self.view.model.values), count)
        self.dependencies.assert_not_called()

    def test_battle_pass_changes_only_refresh_widget_and_disabled_mod_restores_native_visibility(self):
        count = len(self.view.model.values)
        self.apply({'showBattlePassWidget': False})
        self.missions.setGroupVisibility.assert_called_with('battle_pass', False)
        self.assertEqual(len(self.view.model.values), count)
        self.apply({'enabled': False})
        self.missions.setGroupVisibility.assert_called_with('battle_pass', True)
        self.assertFalse(self.view.model.values[-1]['config']['visible'])

    def test_broken_widget_service_does_not_block_clock_notification(self):
        self.dependencies.side_effect = RuntimeError('service unavailable')
        with self.assertLogs('Driftkings.Settings', level='ERROR'):
            self.apply({'enabled': False})
        self.assertFalse(self.view.model.values[-1]['config']['visible'])

    def test_repeated_visibility_is_not_published_and_lifecycle_hides_then_restores(self):
        count = len(self.view.model.values)
        self.clock.setVisible(self.parent, True)
        self.clock.onApplySettings()
        self.options.start(); self.clock.start()
        self.assertEqual(len(self.view.model.values), count)
        self.assertEqual(len(self.service.onModSettingsChanged._listeners), 2)
        self.options.stop(); self.clock.stop()
        self.assertFalse(self.view.model.values[-1]['config']['visible'])
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        count = len(self.view.model.values)
        self.options.stop(); self.clock.stop()
        self.assertEqual(len(self.view.model.values), count)
        self.clock.start()
        self.assertTrue(self.view.model.values[-1]['config']['visible'])
        self.view._finalize()
        self.assertNotIn(self.parent, self.clock.views)
        self.assertNotIn(self.parent, self.clock.visible)
        count = len(self.view.model.values)
        self.view.refresh()
        self.assertEqual(len(self.view.model.values), count)

    def test_failed_clock_transaction_does_not_poison_cache(self):
        self.view.model.fail = True
        self.config.data['clockY'] = 432
        with self.assertRaises(RuntimeError): self.view.refresh()
        self.view.model.fail = False
        self.view.refresh()
        self.assertEqual(self.view.model.values[-1]['config']['clockY'], 432)
        self.assertTrue(self.view.model.values[-1]['config']['visible'])

    def test_recreated_clock_keeps_its_visibility_when_old_view_finalizes(self):
        replacement = self.ns['ClockView'](self.parent, 2)
        replacement._onLoading()
        self.view._finalize()
        self.assertIs(self.clock.views[self.parent], replacement)
        self.assertTrue(self.clock.visible[self.parent])
        self.assertTrue(replacement.model.values[-1]['config']['visible'])

    def test_ammunition_uses_current_setting_without_mutating_vehicle_class(self):
        vehicle = NS(isOnlyForEventBattles=False, isOnlyForBattleRoyaleBattles=False,
                     ammoMaxSize=100, shells=NS(installed=NS(getItems=lambda: [NS(count=30)])))
        original = Mock(return_value='native')
        hook = self.ns['new_isAmmoFull']
        self.apply({'lowAmmoPercentage': 20})
        self.assertTrue(hook(property(original), vehicle))
        self.apply({'lowAmmoPercentage': 50})
        self.assertFalse(hook(property(original), vehicle))
        vehicle.isOnlyForEventBattles = True
        self.assertTrue(hook(property(original), vehicle))
        original.assert_not_called()
        self.apply({'enabled': False})
        self.assertEqual(hook(property(original), vehicle), 'native')
        original.assert_called_once_with(vehicle)

    def test_ammunition_error_falls_back_to_original_property(self):
        original = Mock(return_value=True)
        self.assertTrue(self.ns['new_isAmmoFull'](property(original), NS()))
        original.assert_called_once()
        self.ns['logError'].assert_called_once()


if __name__ == '__main__':
    unittest.main()
