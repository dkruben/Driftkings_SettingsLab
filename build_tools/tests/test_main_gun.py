from settings_support import settings_globals
import ast
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/scripts/client'))
from Driftkings.settings.settings_data import defaults
from Driftkings.settings.service import SettingsService, SettingsChanges
from Driftkings.settings.settings_data import SettingsData
from Driftkings._constants import MAIN_GUN, MINIMAP_PLUGINS
from Driftkings.core.overlay import OverlayScene, ElementType, Align

class Event:
    def __init__(self): self.handlers = []
    def __iadd__(self, fn): self.handlers.append(fn); return self
    def __isub__(self, fn): self.handlers.remove(fn); return self

class MainGunLifecycleTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((ROOT / 'source/scripts/client/Driftkings/battle/main_gun.py').read_text(encoding='utf-8'))
        tree.body = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in ('SysClass', 'MainGun')]
        self.arena = NS(guiType=1, bonusType=1, onVehicleAdded=Event(), onVehicleUpdated=Event())
        self.player = NS(arena=self.arena, playerVehicleID=1, onVehicleEnterWorld=Event(), guiSessionProvider=Mock())
        self.player.guiSessionProvider.getArenaDP.return_value.getEnemyTeams.return_value = [2]
        self.ns = dict(getPlayer=lambda: self.player, battleEvents=Mock(), g_flash=Mock(),
                       config=NS(data={'enabled': True}), ARENA_GUI_TYPE=NS(RANDOM=1, EPIC_RANDOM=2),
                       ARENA_BONUS_TYPE=NS(REGULAR=1))
        settings_globals(self.ns, 'battle.main_gun', 'views.battle.main_gun')
        self.ns['settings_service'] = SettingsService(SettingsData())
        exec(compile(tree, 'MainGun', 'exec'), self.ns)
        self.ns['mainGuns'] = self.ns['MainGun']()
        self.ns['mainGuns'].battleLoading = Mock()
        self.scl = self.ns['SysClass']()
        self.ns['scl'] = self.scl
        self.scl.tanklistsCreate = Mock()

    def test_cleanup_uses_original_arena_even_when_disabled_and_player_gone(self):
        self.scl.battleLoading()
        self.ns['config'].data['enabled'] = False
        self.ns['getPlayer'] = lambda: None
        self.scl.destroyBattle(); self.scl.destroyBattle()
        self.assertEqual(self.arena.onVehicleAdded.handlers, [])
        self.assertEqual(self.arena.onVehicleUpdated.handlers, [])
        self.assertEqual(self.player.onVehicleEnterWorld.handlers, [])
        self.assertFalse(self.scl.inBattle)
        self.ns['g_flash'].hide.assert_called()

    def test_repeated_battles_reset_damage_and_do_not_duplicate_subscriptions(self):
        for _ in range(2):
            self.scl.battleLoading()
            self.assertEqual(len(self.arena.onVehicleAdded.handlers), 1)
            self.ns['mainGuns'].players_damage[2] = [900, False]
            self.scl.vehicles[2] = [100, 100, 2, 'heavyTank']
        self.scl.destroyBattle()
        self.assertEqual(self.ns['mainGuns'].players_damage, {})
        self.assertEqual(self.scl.vehicles, {})

    def test_component_lifecycle_is_idempotent(self):
        self.scl.start(); self.scl.start()
        self.scl.stop(); self.scl.stop()
        hub = self.ns['battleEvents']
        hub.acquire.assert_called_once_with(self.scl)
        hub.release.assert_called_once_with(self.scl)
        hub.started.connect.assert_called_once_with(self.scl.battleLoading)
        hub.started.disconnect.assert_called_once_with(self.scl.battleLoading)
        hub.loaded.connect.assert_called_once_with(self.scl.onRosterReady)
        hub.loaded.disconnect.assert_called_once_with(self.scl.onRosterReady)

    def test_settings_only_refresh_content_and_disconnect_when_stopped(self):
        self.scl.refresh = Mock()
        self.scl.start(); self.scl.start()
        signal = self.ns['settings_service'].onModSettingsChanged
        signal.emit(MINIMAP_PLUGINS.NAME, {'enabled':False})
        for changes in ({'textLock':True}, {'textPosition':{'x':12}},
                        SettingsChanges({'background':{'alpha':50}}, [('background','alpha')]),
                        {'backGroundEnabled':True}):
            signal.emit(MAIN_GUN.NAME, changes)
        self.scl.refresh.assert_not_called()
        signal.emit(MAIN_GUN.NAME, {'enabled':False})
        self.scl.refresh.assert_called_once()
        self.scl.stop()
        signal.emit(MAIN_GUN.NAME, {'enabled':True})
        self.scl.refresh.assert_called_once()
        self.assertFalse(signal._listeners)

    def test_refresh_hides_disabled_display_and_updates_after_reenable(self):
        gun = self.ns['mainGuns']
        gun.updateMainGun = Mock()
        self.scl.inBattle = True
        self.ns['config'].data['enabled'] = False
        self.scl.refresh()
        gun.updateMainGun.assert_not_called()
        self.ns['g_flash'].hide.assert_called_once()
        self.ns['config'].data['enabled'] = True
        self.scl.refresh()
        gun.updateMainGun.assert_called_once()
        self.ns['g_flash'] = None
        self.scl.destroyBattle()

    def prepare_live_roster(self):
        self.ns['config'].data=defaults('MainGun')
        self.ns.update(math=math, ARENA_BONUS_TYPE=NS(REGULAR=1))
        del self.ns['mainGuns'].battleLoading
        del self.scl.tanklistsCreate
        self.player.team=1
        self.roster=[]
        self.ns['vos_collections']=NS(VehiclesInfoCollection=lambda:NS(iterator=lambda dp:self.roster))
        self.dp=self.player.guiSessionProvider.getArenaDP.return_value

    def enemy(self,ident=2,hp=6000):
        return NS(vehicleID=ident,team=2,vehicleType=NS(maxHealth=hp,classTag='heavyTank'),isAlive=lambda:True)

    def test_empty_teams_at_start_recovers_when_vehicle_arrives(self):
        self.prepare_live_roster()
        self.dp.getEnemyTeams.return_value=[]
        self.scl.battleLoading()
        self.assertTrue(self.scl.inBattle)
        self.assertEqual(len(self.arena.onVehicleAdded.handlers),1)
        self.ns['g_flash'].addText.assert_not_called()
        self.dp.getVehicleInfo.return_value=self.enemy()
        self.scl._onVehicleUpdate(2)
        self.assertEqual(self.scl.enemyTeam,2)
        self.assertEqual(self.ns['mainGuns'].totals[0],1200)
        self.assertIn('1 200',self.ns['g_flash'].addText.call_args[0][0])

    def test_loaded_roster_updates_threshold_without_resetting_damage(self):
        self.prepare_live_roster()
        self.scl.battleLoading()
        gun=self.ns['mainGuns']; gun.totals[4]=300
        self.roster.append(self.enemy())
        self.scl.onRosterReady(); self.scl.onRosterReady()
        self.assertEqual(gun.totals[0],1200)
        self.assertEqual(gun.totals[4],300)
        self.assertEqual(self.scl.health[2],[6000,6000])
        self.assertIn('900',self.ns['g_flash'].addText.call_args[0][0])
        self.ns['config'].data['mainGun']['enabled']=False
        self.scl.refresh()
        self.ns['g_flash'].hide.assert_called()

    def test_unsupported_battle_does_not_display_medal(self):
        self.prepare_live_roster()
        self.roster.append(self.enemy())
        self.arena.bonusType=99
        self.scl.battleLoading()
        self.ns['g_flash'].addText.assert_not_called()
        self.assertFalse(self.scl.inBattle)
        self.assertFalse(self.arena.onVehicleAdded.handlers)
        self.assertFalse(self.arena.onVehicleUpdated.handlers)
        self.assertFalse(self.player.onVehicleEnterWorld.handlers)

    def test_regular_to_other_mode_hides_and_does_not_restart_on_loaded(self):
        self.prepare_live_roster()
        self.roster.append(self.enemy())
        self.scl.battleLoading()
        self.assertTrue(self.scl.inBattle)
        self.ns['g_flash'].addText.assert_called()
        self.ns['g_flash'].reset_mock()
        self.arena.bonusType=2  # Training, despite sharing the random-battle UI.
        self.scl.battleLoading()
        self.scl.onRosterReady()
        self.assertFalse(self.scl.inBattle)
        self.ns['g_flash'].hide.assert_called()
        self.ns['g_flash'].addText.assert_not_called()
        self.assertEqual(self.scl.vehicles,{})
        self.assertFalse(self.arena.onVehicleAdded.handlers)
        self.assertFalse(self.player.onVehicleEnterWorld.handlers)


class MainGunViewTests(unittest.TestCase):
    def setUp(self):
        tree=ast.parse((ROOT/'source/scripts/client/Driftkings/views/battle/main_gun.py').read_text(encoding='utf-8'))
        node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FlashController')
        scene=OverlayScene(); config=NS(data=defaults('MainGun'),ID='MainGun')
        ns=dict(overlays=scene,ElementType=ElementType,Align=Align,os=os,ResMgr=NS(openSection=lambda path:True),
                _component=lambda:NS(config=config),logError=Mock())
        settings_globals(ns, 'battle.main_gun', 'views.battle.main_gun')
        self.service = ns['settings_service'] = SettingsService(SettingsData())
        exec(compile(ast.Module(body=[node],type_ignores=[]),'MainGunView','exec'),ns)
        self.view=ns['FlashController']('MainGun')
        self.scene, self.config = scene, config
        self.addCleanup(self.view.destroy)

    def test_overlay_visibility_unicode_and_background_opacity(self):
        view, scene, config = self.view, self.scene, self.config
        self.assertFalse(scene.elements['MainGun'][1]['visible'])
        config.data['backGroundEnabled']=True
        view.addText('Dano necessário: 1 200')
        self.assertTrue(scene.elements['MainGun'][1]['visible'])
        self.assertEqual(scene.elements['MainGun.text'][1]['text'],'Dano necessário: 1 200')
        self.assertEqual(scene.elements['MainGun.image'][1]['alpha'],0.8)
        view.hide()
        self.assertFalse(scene.elements['MainGun'][1]['visible'])
        view.destroy()
        self.assertFalse(scene.elements)

    def test_live_visual_edits_preserve_text_and_keep_panel_border_hidden(self):
        view, scene, config = self.view, self.scene, self.config
        view.addText('1 200')
        self.assertFalse(scene.elements['MainGun'][1]['border'])
        for values in ({'textPosition':{'x':123}}, {'textLock':True},
                       {'backGroundEnabled':True}, {'background':{'alpha':35}}):
            self.service.apply(config, values, persist=False)
        self.assertEqual(scene.elements['MainGun'][1]['x'],123)
        self.assertFalse(scene.elements['MainGun'][1]['drag'])
        self.assertFalse(scene.elements['MainGun'][1]['border'])
        self.assertEqual(scene.elements['MainGun.text'][1]['text'],'1 200')
        self.assertEqual(scene.elements['MainGun.image'][1]['alpha'],0.35)
        self.assertTrue(scene.elements['MainGun'][1]['visible'])
        view.hide()
        self.service.apply(config, {'background':{'alpha':90}}, persist=False)
        self.assertFalse(scene.elements['MainGun'][1]['visible'])
        self.assertEqual(scene.elements['MainGun.image'][1]['alpha'],0.0)

    def test_destroy_disconnects_notifications_and_ignores_other_components(self):
        updates = Mock()
        self.scene.view = NS(update=updates, remove=Mock())
        self.service.onModSettingsChanged.emit(MINIMAP_PLUGINS.NAME, {'textLock':True})
        updates.assert_not_called()
        self.view.destroy(); self.view.destroy()
        self.service.onModSettingsChanged.emit(MAIN_GUN.NAME, {'textLock':True})
        updates.assert_not_called()
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        self.assertFalse(self.scene.updated.listeners)

if __name__ == '__main__': unittest.main()
