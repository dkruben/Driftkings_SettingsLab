import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('hud_visibility', ROOT / 'source/scripts/client/Driftkings/core/hud_visibility.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HudVisibilityTests(TestCase):
    def setUp(self):
        self.hud = module.HudVisibility()
        self.hud.active = True
        self.view = Mock()
        self.hud.attach(self.view)
        self.view.reset_mock()
        self.page = NS(_fullStatsAlias='fullStats')
        self.original = Mock(return_value='native result')

    def test_native_open_close_preserves_call_and_ignores_other_components(self):
        self.hud.nativeVisibility(self.original, self.page, ['minimap'], [])
        self.view.setBattleHudVisible.assert_not_called()
        result = self.hud.nativeVisibility(self.original, self.page, ['fullStats'], ['minimap'])
        self.assertEqual(result, 'native result')
        self.original.assert_called_with(self.page, ['fullStats'], ['minimap'])
        self.view.setBattleHudVisible.assert_called_once_with(False)
        self.hud.nativeVisibility(self.original, self.page, ['fullStats'], [])
        self.view.setBattleHudVisible.assert_called_once_with(False)
        self.hud.nativeVisibility(self.original, self.page, [], ['fullStats'])
        self.view.setBattleHudVisible.assert_called_with(True)

    def test_late_view_is_hidden_and_detached_view_is_not_updated(self):
        self.hud.block('native', True)
        late = Mock()
        self.hud.attach(late)
        late.setBattleHudVisible.assert_called_once_with(False)
        self.hud.detach(late)
        self.hud.reset()
        late.setBattleHudVisible.assert_called_once_with(False)
        self.view.setBattleHudVisible.assert_called_with(True)

    def test_gameface_keeps_hud_hidden_until_its_own_close(self):
        tab = object()
        self.hud.block('native', True)
        self.hud.gamefaceShown(self.original, tab)
        self.hud.block('native', False)
        self.assertFalse(self.hud.visible)
        self.hud.gamefaceHidden(self.original, tab)
        self.assertTrue(self.hud.visible)

    def test_gameface_finalize_clears_native_block_even_when_original_fails(self):
        tab = object()
        self.hud.block('native', True)
        self.hud.gamefaceShown(self.original, tab)
        self.original.side_effect = RuntimeError('dispose failed')
        with self.assertRaises(RuntimeError):
            self.hud.gamefaceHidden(self.original, tab)
        self.assertTrue(self.hud.visible)

    def test_unshown_gameface_disposal_does_not_reveal_native_tab(self):
        self.hud.block('native', True)
        self.hud.gamefaceHidden(self.original, object())
        self.assertFalse(self.hud.visible)

    def test_replay_end_clears_all_blockers_and_disabled_hooks_only_forward(self):
        self.hud.block('native', True)
        self.hud.block(object(), True)
        self.hud.reset()
        self.assertTrue(self.hud.visible)
        self.hud.active = False
        self.hud.nativeVisibility(self.original, self.page, ['fullStats'], [])
        self.hud.gamefaceShown(self.original, object())
        self.assertTrue(self.hud.visible)

    def test_start_stop_subscribes_once_and_restart_does_not_duplicate_hooks(self):
        hud = module.HudVisibility()
        hud.installHooks = Mock()
        events = Mock()
        with patch.dict(sys.modules, {'Driftkings.core.battle_events': NS(battleEvents=events)}):
            hud.start()
            hud.start()
            events.ended.connect.assert_called_once_with(hud.reset)
            hud.stop()
            hud.stop()
            events.ended.disconnect.assert_called_once_with(hud.reset)
            hud.start()
            hud.installHooks.assert_called_once_with()

    def test_service_installs_native_and_gameface_callbacks_directly(self):
        install = Mock()
        native, tab = object(), object()
        modules = {
            'Driftkings.common.utils.monkeypatch': NS(override=install),
            'gui.Scaleform.daapi.view.meta.BattlePageMeta': NS(BattlePageMeta=native),
            'gui.impl.battle.battle_page.tab_view': NS(TabView=tab),
        }
        with patch.dict(sys.modules, modules):
            self.hud.installHooks()
        self.assertEqual(install.call_count, 5)
        install.assert_any_call(native, 'as_setComponentsVisibilityS', self.hud.nativeVisibility)
        install.assert_any_call(native, 'as_setComponentsVisibilityWithFadeS', self.hud.nativeVisibility)
        install.assert_any_call(tab, '_onShown', self.hud.gamefaceShown)
        install.assert_any_call(tab, '_onHidden', self.hud.gamefaceHidden)
        install.assert_any_call(tab, '_finalize', self.hud.gamefaceHidden)
