"""Passive compatibility and safe context infrastructure; no live game required."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/scripts/client'))
from Driftkings.core.mod_compatibility import CompatibilityManager, ABSENT, PRESENT, UNKNOWN, POSSIBLE_CONFLICT, CONFIRMED_CONFLICT
from Driftkings.core.battle_capabilities import BattleCapabilities
from Driftkings.settings.panel.api import SettingsAPI
from Driftkings.settings.panel.presenter import Presenter


class CompatibilityTests(unittest.TestCase):
    def test_absent_without_game_apis_and_unknown_name(self):
        manager = CompatibilityManager({})
        for name in ('XVM', 'BattleObserver', 'ModsListAPI', 'OpenWGGameface'):
            self.assertEqual(manager.status(name), ABSENT)
        self.assertEqual(manager.status('Other'), UNKNOWN)
        self.assertFalse(manager.is_installed('Other'))
        self.assertEqual(manager.warnings_for('PlayerPanelPro'), [])

    def test_concrete_loaded_modules_not_old_config_strings(self):
        manager = CompatibilityManager({'xvm_main.config': NS(config_data={'playersPanel': {'enabled': True}})})
        self.assertFalse(manager.is_installed('XVM'))
        manager.modules['xvm_main'] = NS()
        self.assertTrue(manager.is_installed('XVM'))
        self.assertFalse(manager.has_confirmed_conflict('PlayerPanelPro'))
        self.assertTrue(manager.has_possible_conflict('PlayerPanelPro'))

    def test_partial_failed_import_and_missing_api_are_unknown(self):
        manager = CompatibilityManager({'xvm_main': None, 'gui.modsListApi': NS(), 'openwg_gameface': NS()})
        for name in ('XVM', 'ModsListAPI', 'OpenWGGameface'):
            self.assertEqual(manager.status(name), UNKNOWN)
        self.assertEqual(manager.warnings_for('MinimapPlugins'), [])

    def test_present_apis_are_not_feature_conflicts(self):
        manager = CompatibilityManager({'gui.modsListApi': NS(g_modsListApi=object()),
            'openwg_gameface': NS(gf_mod_inject=lambda: None, res_id_by_key=lambda k: 42)})
        self.assertTrue(manager.is_installed('ModsListAPI'))
        self.assertTrue(manager.is_installed('OpenWGGameface'))
        self.assertFalse(manager.has_possible_conflict('PlayerPanelPro'))

    def xvm(self, enabled=True, loaded=True):
        return CompatibilityManager({'xvm_main': NS(),
            'xvm_main.config': NS(get=lambda path, default: enabled),
            'xvm_battle': NS(owg_module_loaded=lambda: loaded),
            'xvm_battle_minimap': NS(owg_module_loaded=lambda: loaded)})

    def test_initialized_and_active_xvm_feature_is_confirmed_overlap(self):
        manager = self.xvm()
        self.assertTrue(manager.has_confirmed_conflict('PlayerPanelPro'))
        warning = manager.warnings_for('MinimapPlugins')[0]
        self.assertEqual(warning['status'], CONFIRMED_CONFLICT)
        self.assertEqual(warning['level'], 'warning')
        self.assertTrue(manager.has_possible_conflict('MarksOnGunBattle'))
        self.assertFalse(manager.has_confirmed_conflict('MarksOnGunBattle'))

    def test_known_disabled_or_uninitialized_feature_is_not_conflict(self):
        for enabled, loaded in ((False, True), (True, False)):
            manager = self.xvm(enabled, loaded)
            self.assertEqual(manager.conflict_status('PlayerPanelPro', 'XVM'), PRESENT)
            self.assertEqual(manager.warnings_for('PlayerPanelPro'), [])

    def test_read_failure_is_possible_and_never_imports_external_mod(self):
        def broken(*args):
            raise ImportError('Incomplete mod')
        manager = self.xvm()
        manager.modules['xvm_main.config'].get = broken
        with patch('builtins.__import__', side_effect=AssertionError('Import forbidden')):
            self.assertEqual(manager.conflict_status('PlayerPanelPro', 'XVM'), POSSIBLE_CONFLICT)

    def test_battle_observer_only_warns_possibly_for_mapped_components(self):
        manager = CompatibilityManager({'gui.mods.mod_armagomen_battle_observer': NS()})
        for component in ('PlayerPanelPro', 'MinimapPlugins', 'MarksOnGunBattle'):
            self.assertEqual(manager.warnings_for(component)[0]['status'], POSSIBLE_CONFLICT)
        self.assertEqual(manager.warnings_for('CarouselStats'), [])

    def test_logs_do_not_repeat_per_query(self):
        manager = self.xvm()
        with patch('Driftkings.core.mod_compatibility.LOG') as log:
            for unused in range(100):
                manager.warnings_for('PlayerPanelPro')
            self.assertEqual(log.info.call_count, 3)

    def test_presenter_warnings_are_additive_localized_and_do_not_modify_session(self):
        with tempfile.TemporaryDirectory() as folder:
            api = SettingsAPI(folder)
            mod = api.register_mod('PlayerPanelPro', name='Panel')
            mod.add_checkbox('enabled', default=True)
            presenter = Presenter(api)
            with patch('Driftkings.core.mod_compatibility.compatibility', self.xvm()):
                state = presenter.state()
            self.assertEqual(state['compatibilityWarnings']['PlayerPanelPro'][0]['status'], CONFIRMED_CONFLICT)
            self.assertEqual(state['disabled']['PlayerPanelPro'], [])
            self.assertTrue(state['status']['PlayerPanelPro']['enabled'])
            self.assertEqual(presenter.session.history, [])
            self.assertEqual(presenter.session.drafts, {})
            self.assertEqual(api.registry.dependency_status(api.registry.mods['PlayerPanelPro']), [])
            self.assertFalse(list(Path(folder).rglob('*.json')))


class PlayerAccount(object):
    pass


BONUS = NS(UNKNOWN=0, REGULAR=1, COMP7=43, COMP7_LIGHT=49, EPIC_BATTLE=27,
           EVENT_BATTLES=9, TRAINING=2, RANDOM_RANGE=(1,), RANGE=(0,1,43,49,27,9,2))


class BattleCapabilitiesTests(unittest.TestCase):
    def context(self, bonus=1, player='battle', gui=None, spg=False):
        self.modules = {'constants': NS(ARENA_BONUS_TYPE=BONUS), 'Account': NS(PlayerAccount=PlayerAccount)}
        self.player = NS(arena=NS(bonusType=bonus)) if player == 'battle' else player
        self.session = NS(arenaVisitor=NS(getArenaBonusType=lambda: bonus, gui=gui or NS()),
            getArenaDP=lambda: NS(getVehicleInfo=lambda: NS(isSPG=lambda: spg)))
        return BattleCapabilities(player=lambda: self.player, session=lambda: self.session, modules=self.modules)

    def test_hangar_and_absent_player(self):
        cap = self.context(player=PlayerAccount())
        self.assertEqual(cap.current_mode(), 'hangar')
        self.assertFalse(cap.is_in_battle())
        self.player = None
        self.assertEqual(cap.current_mode(), 'unknown')
        for name in ('is_random','is_comp7','is_frontline','is_replay','is_event','is_white_tiger','is_special','is_spg','supports_gameface_overlay'):
            self.assertFalse(getattr(cap, name)())

    def test_random_comp7_frontline_and_event(self):
        for bonus, mode in ((1,'random'),(43,'comp7'),(49,'comp7'),(27,'frontline'),(9,'event'),(2,'special')):
            cap = self.context(bonus)
            self.assertEqual(cap.current_mode(), mode)
            self.assertEqual(cap.is_random(), mode == 'random')
            self.assertEqual(cap.is_special(), mode != 'random')

    def test_visitor_gui_methods_reused(self):
        cap = self.context(bonus=None, gui=NS(isEpicBattle=lambda: True))
        self.assertTrue(cap.is_frontline())
        self.assertEqual(cap.current_mode(), 'frontline')
        cap = self.context(bonus=None, gui=NS(isRandomBattle=lambda: True))
        self.assertTrue(cap.is_random())
        cap = self.context(bonus=None, gui=NS(isEventBattle=lambda: True))
        self.assertTrue(cap.is_event())

    def test_white_tiger_requires_explicit_signal_not_just_event(self):
        cap = self.context(9)
        self.assertFalse(cap.is_white_tiger())
        cap = self.context(9, gui=NS(isWhiteTigerBattle=lambda: True))
        self.assertTrue(cap.is_white_tiger())
        self.assertEqual(cap.current_mode(), 'white_tiger')
        self.assertTrue(cap.is_event())

    def test_replay_preserves_underlying_battle_mode(self):
        cap = self.context()
        self.modules['BattleReplay'] = NS(isPlaying=lambda: True, isLoading=lambda: False)
        self.assertTrue(cap.is_replay())
        self.assertEqual(cap.current_mode(), 'random')
        self.player = PlayerAccount()
        self.assertFalse(cap.is_replay())

    def test_spg_reuses_vehicle_info(self):
        cap = self.context(spg=True)
        self.assertTrue(cap.is_spg())
        self.session = None
        self.assertFalse(cap.is_spg())

    def test_partial_arena_shutdown_and_game_apis_missing(self):
        cap = self.context(player=NS(arena=None))
        self.assertEqual(cap.current_mode(), 'unknown')
        self.player = NS(arena=NS())
        self.session = None
        self.assertEqual(cap.current_mode(), 'unknown')
        cap = BattleCapabilities(modules={})
        self.assertEqual(cap.current_mode(), 'unknown')
        self.assertFalse(cap.is_spg())

    def test_raising_player_and_visitor_are_safe(self):
        def broken():
            raise RuntimeError('Shutdown')
        cap = BattleCapabilities(player=broken, session=broken, modules={})
        self.assertFalse(cap.is_in_battle())
        self.assertEqual(cap.current_mode(), 'unknown')
        cap = self.context()
        self.session.arenaVisitor.getArenaBonusType = broken
        self.assertTrue(cap.is_random(), 'arena fallback still available')

    def test_overlay_installation_does_not_imply_support(self):
        cap = self.context()
        self.modules['openwg_gameface'] = NS(gf_mod_inject=lambda:None,res_id_by_key=lambda key:42)
        self.assertFalse(cap.supports_gameface_overlay())
        self.assertFalse(cap.supports_gameface_overlay(NS(), 'key'))

    def test_overlay_requires_loaded_battle_wulf_type_and_matching_resource(self):
        class View(object):
            pass
        BattleView = type('BattleView',(View,),{'__module__':'gui.impl.battle.battle_page'})
        view = BattleView()
        view.proxy, view.viewStatus, view.layoutID = object(), 3, 42
        cap = self.context()
        self.modules['openwg_gameface'] = NS(gf_mod_inject=lambda:None,res_id_by_key=lambda key:42)
        with patch.dict(sys.modules, {'frameworks.wulf': NS(View=View,ViewStatus=NS(LOADED=3))}):
            self.assertTrue(cap.supports_gameface_overlay(view,'key'))
            view.viewStatus=5
            self.assertFalse(cap.supports_gameface_overlay(view,'key'))
            view.viewStatus=3;view.layoutID=43
            self.assertFalse(cap.supports_gameface_overlay(view,'key'))
            self.assertFalse(cap.supports_gameface_overlay(View(),'key'))

    def test_mode_log_only_on_transition(self):
        cap = self.context()
        with patch('Driftkings.core.battle_capabilities.LOG') as log:
            for unused in range(100):
                cap.current_mode()
            self.assertEqual(log.info.call_count,1)
            self.player=None
            cap.current_mode()
            self.assertEqual(log.info.call_count,2)
