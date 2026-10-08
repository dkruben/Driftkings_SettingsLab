from settings_support import settings_globals
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings._constants import BATTLE_STAT, MINIMAP_PLUGINS
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults
from Driftkings.core.overlay import OverlayScene, ElementType

class Delayer:
    def __init__(self): self.pending = []
    def clearCallbacks(self): self.pending[:] = []
    def delayCallback(self, delay, callback): self.pending.append(callback)

class BattleStatTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((ROOT / 'source/scripts/client/Driftkings/battle/battle_stat.py').read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in ('BattleStatDisplay', 'TanksStatistic')]
        self.stats = Mock(base={1: {'hp': 100, 'isAlive': True}}, allyChance=50, enemyChance=50)
        self.stats.reset.side_effect = self.stats.base.clear
        self.flash = Mock()
        self.config = SimpleNamespace(data={'enabled': True, 'format': '{header}'})
        self.arena = SimpleNamespace(bonusType=1, vehicles={})
        self.ns = dict(CallbackDelayer=Delayer, g_tanksStatistic=self.stats, g_flash=self.flash,
                       config=self.config, getPlayer=lambda: SimpleNamespace(arena=self.arena, team=1),
                       ARENA_BONUS_TYPE=SimpleNamespace(REGULAR=1), getComparisonColor=lambda *a: '#fff',
                       replaceMacros=lambda text, macros: text, battleEvents=Mock(), getEntity=lambda vid: SimpleNamespace(health=35))
        settings_globals(self.ns, 'battle.battle_stat')
        self.service = self.ns['settings_service'] = SettingsService(SettingsData())
        exec(compile(tree, 'BattleStat', 'exec'), self.ns)
        self.display = self.ns['BattleStatDisplay']()
        self.display.inBattle = True

    def test_exit_cancels_callbacks_and_next_battle_drops_old_vehicles(self):
        self.display.flash_text()
        self.assertEqual(len(self.display.pending), 1)
        self.display.onBattleEnded()
        self.assertFalse(self.display.inBattle)
        self.assertEqual(self.display.pending, [])
        self.assertEqual(self.stats.base, {})
        self.flash.setVisible.assert_called_with(False)
        self.stats.base[9] = {'hp': 1}
        self.display.onBattleStarted()
        self.assertEqual(self.stats.base, {})

    def test_health_appearance_and_death_update_only_in_battle(self):
        self.display.onAppeared(1)
        self.assertEqual(self.stats.base[1]['hp'], 35)
        self.display.onKilled(1)
        self.assertEqual(self.stats.base[1], {'hp': 0, 'isAlive': False})
        self.stats.update.assert_called_with(1, 1)
        self.display.inBattle = False
        self.display.onHealthChanged(1, 100)
        self.assertEqual(self.stats.base[1]['hp'], 0)

    def test_disable_reenable_and_missing_flash(self):
        self.display.refresh()
        self.config.data['enabled'] = False
        self.display.refresh()
        self.assertEqual(self.display.pending, [])
        self.flash.setVisible.assert_called_with(False)
        self.config.data['enabled'] = True
        self.display.refresh()
        self.display.refresh()
        self.assertEqual(len(self.display.pending), 1)
        self.ns['g_flash'] = None
        self.display.refresh()
        self.assertEqual(self.display.pending, [])

    def test_start_stop_are_idempotent_and_release_events(self):
        self.display.start(); self.display.start()
        self.ns['battleEvents'].acquire.assert_called_once_with(self.display)
        self.display.stop(); self.display.stop()
        self.ns['battleEvents'].release.assert_called_once_with(self.display)
        for signal, handler in self.display.subscriptions():
            signal.connect.assert_called_once_with(handler)
            signal.disconnect.assert_called_once_with(handler)

    def test_settings_notifications_are_scoped_and_do_not_restart_timer_for_layout(self):
        self.display.start()
        self.display.flash_text()
        pending = list(self.display.pending)
        self.display.refresh = Mock()
        signal = self.service.onModSettingsChanged
        signal.emit(MINIMAP_PLUGINS.NAME, {'enabled':False})
        signal.emit(BATTLE_STAT.NAME, {'textLock':True, 'textPosition':{'x':12}})
        self.display.refresh.assert_not_called()
        self.assertEqual(self.display.pending,pending)
        signal.emit(BATTLE_STAT.NAME, {'colorRating':1})
        self.display.refresh.assert_called_once()
        self.display.stop()
        self.assertFalse(signal._listeners)
        signal.emit(BATTLE_STAT.NAME, {'format':'new'})
        self.display.refresh.assert_called_once()

    def test_real_statistics_reset_clears_vehicle_cache(self):
        stats = self.ns['TanksStatistic']()
        stats.base[1] = {'hp': 100}
        stats.reset()
        self.assertEqual(stats.base, {})

    def vehicle_info(self):
        self.ns['vehicles'] = SimpleNamespace(VEHICLE_CLASS_TAGS={'mediumTank'})
        self.ns['SHELL_TYPES'] = SimpleNamespace(ARMOR_PIERCING_CR='APCR', HOLLOW_CHARGE='HC', HIGH_EXPLOSIVE='HE')
        self.ns['g_events'] = Mock()
        shell = SimpleNamespace(kind='AP', armorDamage=(100, 0))
        descriptor = SimpleNamespace(type=SimpleNamespace(compactDescr=1, shortUserString='Tank', tags={'mediumTank'}),
                                     level=5, maxHealth=100, gun=SimpleNamespace(reloadTime=5, clip=(1, 0),
                                                                             shots=[SimpleNamespace(shell=shell)]))
        return {'vehicleType': descriptor, 'accountDBID': 1, 'name': 'Player', 'team': 1, 'isAlive': True}

    def test_missing_vehicle_info_can_be_retried_without_incomplete_cache(self):
        stats = self.ns['TanksStatistic']()
        for missing in (None, {}, {'vehicleType': None}):
            self.assertFalse(stats.addVehicleInfo(2, missing))
            self.assertEqual(stats.base, {})
        info = self.vehicle_info()
        self.assertTrue(stats.addVehicleInfo(2, info))
        self.assertEqual(stats.base[2]['hp'], 100)
        stats.base[2]['hp'] = 35
        self.assertFalse(stats.addVehicleInfo(2, info))
        self.assertEqual(stats.base[2]['hp'], 35)

    def test_broken_descriptor_does_not_leave_partial_tank(self):
        stats = self.ns['TanksStatistic']()
        info = self.vehicle_info()
        del info['vehicleType'].gun
        with self.assertRaises(AttributeError):
            stats.addVehicleInfo(2, info)
        self.assertEqual(stats.base, {})
        self.assertTrue(stats.addVehicleInfo(2, self.vehicle_info()))

    def test_late_appearance_retries_data_and_uses_current_health(self):
        stats = self.ns['TanksStatistic']()
        self.ns['g_tanksStatistic'] = stats
        self.display.onAppeared(2)
        self.assertEqual(stats.base, {})
        self.arena.vehicles[2] = self.vehicle_info()
        self.display.onAppeared(2)
        self.assertEqual(stats.base[2]['hp'], 35)
        self.assertEqual(len(self.display.pending), 1)
        self.display.onKilled(2)
        self.assertEqual(stats.base[2]['hp'], 0)
        self.assertFalse(stats.base[2]['isAlive'])

    def test_destroyed_vehicle_added_with_zero_health(self):
        stats = self.ns['TanksStatistic']()
        info = self.vehicle_info()
        info['isAlive'] = False
        self.assertTrue(stats.addVehicleInfo(2, info))
        self.assertEqual(stats.base[2]['hp'], 0)

class BattleStatViewTests(unittest.TestCase):
    def setUp(self):
        self.scene = OverlayScene()
        self.config = SimpleNamespace(ID='BattleStat', data=defaults('BattleStat'))
        self.service = SettingsService(SettingsData())
        ns = dict(overlays=self.scene, ElementType=ElementType, _component=lambda:SimpleNamespace(config=self.config))
        settings_globals(ns, 'views.battle.battle_stat')
        ns['settings_service'] = self.service
        for filename, classname in (('label', 'BattleLabel'), ('battle_stat', 'Flash')):
            path = ROOT / ('source/scripts/client/Driftkings/views/battle/' + filename + '.py')
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            tree.body = [node for node in tree.body if isinstance(node,ast.ClassDef) and node.name == classname]
            exec(compile(tree,str(path),'exec'),ns)
        self.view = ns['Flash']('BattleStat', self.config.data['textFormat'])
        self.addCleanup(self.view.destroy)
        self.flash = Mock()
        self.scene.attach(self.flash)
        self.flash.reset_mock()

    def test_identical_poll_output_is_sent_once_and_recreated_flash_receives_state(self):
        for _ in range(4):
            self.view.setVisible(True)
            self.view.HtmlText('Chances: 50 / 50')
        self.assertEqual(self.flash.update.call_count,2)
        self.view.HtmlText('Chances: 60 / 40')
        self.assertEqual(self.flash.update.call_count,3)
        new_flash = Mock()
        self.scene.attach(new_flash)
        payload = new_flash.reset.call_args.args[0]
        self.assertEqual(payload[0]['props']['text'],'Chances: 60 / 40')
        self.assertTrue(payload[0]['props']['visible'])
        self.view.HtmlText('Chances: 60 / 40')
        new_flash.update.assert_not_called()

    def test_position_lock_and_destroy_keep_content_and_disconnect(self):
        self.view.HtmlText('Chances')
        self.service.apply(self.config, {'textPosition':{'x':42}, 'textLock':True}, persist=False)
        props = self.scene.elements['BattleStat'][1]
        self.assertEqual(props['x'],42)
        self.assertEqual(props['text'],'Chances')
        self.assertFalse(props['drag'])
        self.assertFalse(props['border'])
        self.view.destroy(); self.view.destroy()
        self.assertFalse(self.scene.elements)
        self.assertFalse(self.scene.updated.listeners)
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        self.flash.reset_mock()
        self.view.HtmlText('after destroy')
        self.view.setVisible(True)
        self.flash.update.assert_not_called()

    def test_failed_overlay_update_can_be_retried(self):
        original = self.scene.update
        self.scene.update = Mock(return_value=False)
        self.view.HtmlText('Chances')
        self.view.setVisible(True)
        self.scene.update = original
        self.view.HtmlText('Chances')
        self.view.setVisible(True)
        self.assertEqual(self.flash.update.call_count,2)


if __name__ == '__main__': unittest.main()
