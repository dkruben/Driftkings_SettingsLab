import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/scripts/client'))
from Driftkings.core.overlay import OverlayScene
from Driftkings.views.battle import label, battle_efficiency, battle_stat


class BattleLabelTests(unittest.TestCase):
    def test_independent_positions_formats_and_disposal(self):
        scene = OverlayScene()
        shadow = {'enabled': True, 'alpha': 1, 'color': 0}
        efficiency = SimpleNamespace(config=SimpleNamespace(ID='BattleEfficiency', data={
            'position': {'x': 10, 'y': 20}, 'textLock': True, 'textShadow': shadow,
            'textStyle': {'size': 12, 'font': 'Arial', 'color': '#FFFFFF', 'align': 'left'}},
            onApplySettings=Mock()))
        stats = SimpleNamespace(config=SimpleNamespace(ID='BattleStat', data={
            'textPosition': {'x': 30, 'y': 40}, 'textLock': False, 'textShadow': shadow},
            onApplySettings=Mock()))
        with patch.object(label, 'overlays', scene), patch.object(battle_efficiency, 'overlays', scene), \
                patch.object(battle_stat, 'overlays', scene), \
                patch.object(battle_efficiency, '_component', lambda: efficiency), \
                patch.object(battle_stat, '_component', lambda: stats):
            first = battle_efficiency.Flash('efficiency')
            second = battle_stat.Flash('stats', {'font': 'Arial', 'size': 13, 'color': '#FFFF00',
                                               'bold': True, 'italic': False})
            self.assertEqual(len(scene.updated.listeners), 2)
            self.assertFalse(scene.elements['efficiency'][1]['drag'])
            self.assertTrue(scene.elements['stats'][1]['drag'])
            scene.updated.emit('efficiency', {'x': 90})
            efficiency.config.onApplySettings.assert_called_once_with({'position': {'x': 90, 'y': 20}})
            stats.config.onApplySettings.assert_not_called()
            scene.updated.emit('stats', {'y': 80})
            stats.config.onApplySettings.assert_called_once_with({'textPosition': {'x': 30, 'y': 80}})
            first.addText('Dano: 100')
            second.HtmlText(second.getSimpleTextWithTags('WN8: 200'))
            self.assertIn('Dano: 100', scene.elements['efficiency'][1]['text'])
            self.assertIn('<b>WN8: 200</b>', scene.elements['stats'][1]['text'])
            stats.config.data['textLock'] = True
            second.onApplySettings()
            self.assertFalse(scene.elements['stats'][1]['drag'])
            first.destroy()
            self.assertNotIn('efficiency', scene.elements)
            self.assertIn('stats', scene.elements)
            self.assertEqual(len(scene.updated.listeners), 1)
            second.destroy()
            self.assertFalse(scene.elements)
            self.assertFalse(scene.updated.listeners)
