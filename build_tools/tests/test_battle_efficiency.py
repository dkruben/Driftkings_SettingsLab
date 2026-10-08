import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from settings_support import settings_globals

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings._constants import BATTLE_EFFICIENCY, MINIMAP_PLUGINS
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults
from Driftkings.core.overlay import OverlayScene
from Driftkings.views.battle import label, battle_efficiency


def replace_macros(text, macros):
    for key, value in macros.items():
        text = text.replace(key, value)
    return text


class EfficiencySettingsTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'source/scripts/client/Driftkings/components/battle_efficiency.py'
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body = [node for node in tree.body
                     if isinstance(node, ast.ClassDef) and node.name == 'BattleEfficiency'
                     or isinstance(node, ast.FunctionDef) and node.name == 'new_destroyGUI']
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                node.decorator_list = []
        self.config = NS(ID='BattleEfficiency', data=defaults('BattleEfficiency'))
        self.service = SettingsService(SettingsData())
        self.flash = Mock()
        self.calculator = Mock()
        self.player = NS(arena=NS(bonusType=1))
        self.results = {}
        self.ns = dict(config=self.config, getPlayer=lambda: self.player,
                       g_flash=self.flash, g_calculator=self.calculator,
                       getStatisticColor=lambda key, value, *args: '#123456',
                       replaceMacros=replace_macros, SUPPORTED_BONUS_TYPES={1},
                       _results_views=self.results, LOG=Mock())
        settings_globals(self.ns, 'components.battle_efficiency')
        self.ns['settings_service'] = self.service
        exec(compile(tree, str(path), 'exec'), self.ns)
        self.controller = self.ns['g_battleEfficiency'] = self.ns['BattleEfficiency']()
        self.controller.start()
        self.addCleanup(self.controller.stop)

    def test_content_settings_render_cached_values_without_recalculation(self):
        self.controller.stats['wn8'] = 1234
        self.service.apply(self.config, {'format': 'Rating: {wn8}'}, persist=False)
        self.flash.addText.assert_called_once_with('Rating: 1234')
        self.flash.setVisible.assert_called_once_with(True)
        self.calculator.calc.assert_not_called()
        self.flash.reset_mock()
        self.service.apply(self.config, {'colorRatting': 1}, persist=False)
        self.flash.addText.assert_called_once_with('Rating: 1234')
        self.assertEqual(self.controller.stats['wn8'], 1234)
        self.calculator.calc.assert_not_called()

    def test_scoped_notifications_refresh_results_only_for_relevant_settings(self):
        view = Mock(arenaUniqueID=42)
        child = Mock()
        self.results[view] = child
        signal = self.service.onModSettingsChanged
        self.controller.start()
        signal.emit(MINIMAP_PLUGINS.NAME, {'enabled': False})
        signal.emit(BATTLE_EFFICIENCY.NAME, {'position': {'x': 12}, 'textLock': True})
        self.flash.addText.assert_not_called()
        child.refresh.assert_not_called()
        signal.emit(BATTLE_EFFICIENCY.NAME, {'battleResultsFormat': 'new'})
        child.refresh.assert_called_once_with(42)
        self.flash.addText.assert_not_called()
        child.reset_mock()
        signal.emit(BATTLE_EFFICIENCY.NAME, {'colorRatting': 1})
        child.refresh.assert_called_once_with(42)
        self.flash.addText.assert_called_once()
        self.controller.stop()
        self.controller.stop()
        self.assertFalse(signal._listeners)
        self.calculator.stopBattle.assert_called_once()

    def test_one_broken_results_view_does_not_block_the_others(self):
        broken, good = Mock(), Mock()
        broken.refresh.side_effect = RuntimeError('disposed view')
        self.results[Mock(arenaUniqueID=1)] = broken
        self.results[Mock(arenaUniqueID=2)] = good
        self.service.onModSettingsChanged.emit(BATTLE_EFFICIENCY.NAME, {'battleResultsWindow': False})
        good.refresh.assert_called_once_with(2)
        self.ns['LOG'].exception.assert_called_once()

    def test_disabled_and_unsupported_contexts_hide_instead_of_rendering(self):
        for player, enabled in ((None, True), (NS(), True),
                                (NS(arena=NS(bonusType=7)), True), (self.player, False)):
            self.player = player
            self.config.data['enabled'] = enabled
            self.flash.reset_mock()
            self.controller.updateFormatString()
            self.flash.addText.assert_not_called()
            self.flash.setVisible.assert_called_once_with(False)

    def test_end_of_battle_clears_disabled_module_but_keeps_subscription(self):
        self.controller.stats['damage'] = 900
        self.config.data['enabled'] = False
        original = Mock()
        self.ns['new_destroyGUI'](original, 'avatar')
        original.assert_called_once_with('avatar')
        self.assertTrue(all(value == 0 for value in self.controller.stats.values()))
        self.flash.setVisible.assert_called_once_with(False)
        self.calculator.stopBattle.assert_called_once()
        self.assertEqual(len(self.service.onModSettingsChanged._listeners), 1)


class EfficiencyViewTests(unittest.TestCase):
    def setUp(self):
        self.config = NS(ID='BattleEfficiency', data=defaults('BattleEfficiency'))
        self.service = SettingsService(SettingsData())
        self.scene = OverlayScene()
        for module in (label, battle_efficiency):
            for key, value in (('overlays', self.scene), ('settings_service', self.service)):
                patcher = patch.object(module, key, value)
                patcher.start()
                self.addCleanup(patcher.stop)
        patcher = patch.object(battle_efficiency, '_component', lambda: NS(config=self.config))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.view = battle_efficiency.Flash(self.config.ID)
        self.addCleanup(self.view.destroy)
        self.flash = Mock()
        self.scene.attach(self.flash)
        self.flash.reset_mock()

    def test_repeated_output_is_skipped_and_new_flash_restores_state(self):
        self.view.addText('WN8: 1234')
        self.view.setVisible(True)
        calls = self.flash.update.call_count
        for _ in range(4):
            self.view.addText('WN8: 1234')
            self.view.setVisible(True)
        self.assertEqual(self.flash.update.call_count, calls)
        self.config.data['textStyle']['size'] = 20
        self.view.addText('WN8: 1234')
        props = self.scene.elements[self.config.ID][1]
        self.assertIn("size='20'", props['text'])
        self.assertEqual(props['text'].count('WN8: 1234'), 1)
        replacement = Mock()
        self.scene.attach(replacement)
        restored = replacement.reset.call_args.args[0][0]['props']
        self.assertEqual(restored, props)

    def test_layout_preserves_hidden_state_and_destroy_disconnects(self):
        self.view.addText('WN8: 10')
        self.service.apply(self.config, {'position': {'x': 42}, 'textLock': True}, persist=False)
        props = self.scene.elements[self.config.ID][1]
        self.assertEqual(props['x'], 42)
        self.assertIn('WN8: 10', props['text'])
        self.assertFalse(props['visible'])
        self.assertFalse(props['drag'])
        self.assertFalse(props['border'])
        self.service.apply(self.config, {'textShadow': {'enabled': False}}, persist=False)
        self.assertFalse(props['shadow']['enabled'])
        self.assertFalse(props['visible'])
        self.assertIn('WN8: 10', props['text'])
        self.view.destroy()
        self.view.destroy()
        self.assertFalse(self.scene.updated.listeners)
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        self.assertFalse(self.scene.elements)
        self.flash.reset_mock()
        self.view.addText('after destroy')
        self.view.setVisible(True)
        self.flash.update.assert_not_called()

    def test_failed_scene_updates_are_retried(self):
        with patch.object(self.scene, 'update', return_value=False):
            self.view.addText('WN8: 10')
            self.view.setVisible(True)
        self.view.addText('WN8: 10')
        self.view.setVisible(True)
        props = self.scene.elements[self.config.ID][1]
        self.assertIn('WN8: 10', props['text'])
        self.assertTrue(props['visible'])


if __name__ == '__main__':
    unittest.main()
