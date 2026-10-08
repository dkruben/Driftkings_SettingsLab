import ast
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from settings_support import settings_globals
from Driftkings.core.keyboard import KeyboardService
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults


def load(name, ns):
    path = ROOT / ('source/scripts/client/Driftkings/battle/' + name + '.py')
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) or
                 isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.isupper()]
    for node in tree.body:
        if isinstance(node, ast.FunctionDef): node.decorator_list = []
    settings_globals(ns, 'battle.' + name)
    ns['settings_service'] = SettingsService(SettingsData())
    exec(compile(tree, str(path), 'exec'), ns)
    return ns


class Event:
    def __init__(self): self.handlers = []
    def __iadd__(self, handler): self.handlers.append(handler); return self
    def __isub__(self, handler): self.handlers.remove(handler); return self


class ZoomControllerTests(unittest.TestCase):
    def setUp(self):
        self.config = NS(ID='ZoomExtended', data=defaults('ZoomExtended'))
        self.config.data['disableCamAfterShot'] = True
        self.events = NS(onAvatarReady=Event(), onAvatarBecomeNonPlayer=Event())
        self.manager = Mock()
        self.pending = {}; self.sequence = 0; self.delays = []
        def schedule(delay, fn):
            self.sequence += 1
            self.pending[self.sequence] = fn; self.delays.append(delay)
            return self.sequence
        self.avatar = self.new_avatar()
        self.ns = load('zoom', dict(config=self.config, g_playerEvents=self.events,
            TriggersManager=NS(ITriggerListener=object, TRIGGER_TYPE=NS(PLAYER_DISCRETE_SHOOT=17), g_manager=self.manager),
            getPlayer=lambda:self.avatar, CTRL_MODE_NAME=NS(SNIPER='sniper', ARCADE='arcade'),
            callback=schedule, cancelCallback=lambda token:self.pending.pop(token, None), isReplay=lambda:False))
        self.controller = self.ns['ZoomController'](self.config)
        self.addCleanup(self.controller.dispose)

    def new_avatar(self):
        aiming = NS(getDesiredShotPoint=lambda:'point', turretYaw=1, gunPitch=2)
        handler = NS(ctrlModeName='sniper', onControlModeChanged=Mock(),
                     ctrl=NS(camera=NS(aimingSystem=aiming), _aimingMode='aim'))
        desc = NS(shot=NS(shell=NS(caliber=105)), gun=NS(tags=set()))
        return NS(inputHandler=handler, getVehicleDescriptor=lambda:desc, playerVehicleID=42)

    def test_start_finish_and_disposal_do_not_duplicate_listeners_or_write_preferences(self):
        before = deepcopy(self.config.data)
        self.controller.updateSettings(); self.controller.onStart(); self.controller.onStart()
        self.assertEqual(len(self.events.onAvatarReady.handlers), 1)
        self.manager.addListener.assert_called_once_with(self.controller)
        self.controller.onTriggerActivated({'type':17}); self.controller.onTriggerActivated({'type':17})
        self.assertEqual(len(self.pending), 2)
        self.controller.onFinish(); self.controller.onFinish()
        self.assertEqual(self.pending, {})
        self.assertEqual(self.controller._pending, set())
        self.manager.delListener.assert_called_once_with(self.controller)
        self.assertEqual(self.config.data, before)
        self.assertFalse(hasattr(self.config, 'settingsCache'))
        self.controller.dispose(); self.controller.dispose()
        self.assertEqual(self.events.onAvatarReady.handlers, [])
        self.assertEqual(self.events.onAvatarBecomeNonPlayer.handlers, [])

    def test_delayed_shot_keeps_native_camera_arguments_and_cannot_cross_battles(self):
        self.controller.onStart(); self.controller.onTriggerActivated({'type':17})
        self.assertEqual(self.delays, [.5])
        self.pending.pop(1)()
        self.avatar.inputHandler.onControlModeChanged.assert_called_once_with('arcade', prevModeName='sniper',
            preferredPos='point', turretYaw=1, gunPitch=2, aimingMode='aim', closesDist=False, curVehicleID=42)
        self.assertEqual(self.controller._pending, set())
        self.controller.onTriggerActivated({'type':17})
        stale = self.pending[2]
        self.controller.onFinish()
        self.avatar = self.new_avatar(); self.controller.onStart()
        stale()
        self.avatar.inputHandler.onControlModeChanged.assert_not_called()

    def test_camera_filters_small_caliber_clip_and_non_sniper_modes(self):
        self.controller.onStart()
        desc = self.avatar.getVehicleDescriptor()
        desc.shot.shell.caliber = 60; self.controller.changeControlMode()
        desc.shot.shell.caliber = 105; desc.gun.tags.add('clip'); self.controller.changeControlMode()
        desc.gun.tags.clear(); self.avatar.inputHandler.ctrlModeName = 'arcade'; self.controller.changeControlMode()
        self.avatar.inputHandler.onControlModeChanged.assert_not_called()
        self.controller.onTriggerActivated({'type':99})
        self.assertEqual(self.pending, {})
        self.ns['settings_service'].apply(self.config, {'enabled':False}, persist=False)
        self.controller.updateSettings()
        self.controller.onStart(); self.controller.onTriggerActivated({'type':17})
        self.assertEqual(self.pending, {})
        self.assertFalse(self.controller.subscribed)

    def test_sniper_steps_preserve_config_and_replay_native_values(self):
        data = self.config.data
        data['zoomSteps']['steps'] = [12, 1, 4, 2, 8]
        data['noSniperDynamic'] = True
        before = deepcopy(data)
        camera = NS(_baseCfg={}, _userCfg={}, _cfg={}, isCameraDynamic=lambda:True,
                    enableDynamicCamera=Mock(), _SniperCamera__dynamicCfg={'zoomExposure':[.1]})
        def native(cam, section):
            for cfg in (cam._baseCfg, cam._userCfg, cam._cfg): cfg['zooms'] = [2, 4, 8]
        self.ns['new__readConfigs'](native, camera, None)
        self.assertEqual(camera._cfg['zooms'], [2, 4, 8, 12])
        self.assertEqual(len(camera._SniperCamera__dynamicCfg['zoomExposure']), 4)
        camera.enableDynamicCamera.assert_called_once_with(False)
        self.assertEqual(data, before)
        self.ns['isReplay'] = lambda:True
        self.ns['new__readConfigs'](native, camera, None)
        self.assertEqual(camera._cfg['zooms'], [2, 4, 8])
        self.assertNotIn('increasedZoom', camera._cfg)
        camera.enableDynamicCamera.assert_called_once()

    def test_effect_options_only_modify_player_vehicle_and_binocular_hook_returns_native(self):
        self.config.data.update(noFlashBang=True, noShockWave=True, noBinoculars=True)
        native = Mock(return_value=42)
        self.ns['new__effectsListPlayer'](native, 'effect', isPlayerVehicle=True, showFlashBang=True, showShockWave=True)
        native.assert_called_once_with('effect', isPlayerVehicle=True, showFlashBang=False, showShockWave=False)
        native.reset_mock()
        self.ns['new__effectsListPlayer'](native, 'effect', isPlayerVehicle=False, showFlashBang=True)
        native.assert_called_once_with('effect', isPlayerVehicle=False, showFlashBang=True)
        mode = NS(_binoculars=Mock())
        self.assertEqual(self.ns['new__setupBinoculars'](native, mode, 'devices'), 42)
        mode._binoculars.resetTextures.assert_called_once()


class SplashControllerTests(unittest.TestCase):
    def setUp(self):
        self.config = NS(ID='ArtySplash', data=defaults('ArtySplash'), i18n={
            'UI_artySplash_messageSplashOn':'on', 'UI_artySplash_messageSplashOff':'off',
            'UI_artySplash_messageDotOn':'on', 'UI_artySplash_messageDotOff':'off'})
        self.desc = NS(type=NS(tags='SPG'), shot=NS(shell=NS(kind='HIGH_EXPLOSIVE', type=NS(explosionRadius=8))))
        self.player = NS(getVehicleDescriptor=lambda:self.desc, vehicleTypeDescriptor=self.desc, spaceID=1,
                         gunRotator=NS(markerInfo=[(10, 20, 30)]), inputHandler=NS(ctrlModeName='strategic'))
        self.models = []; self.areas = []
        def marker(data, position):
            root = NS(attach=lambda area:setattr(area, 'attached', True), detach=lambda area:setattr(area, 'attached', False))
            model = NS(model=NS(scale=None, visible=True, root=root), clear=Mock())
            self.models.append(model)
            return model
        def area():
            item = NS(attached=False, setup=Mock(), enableAccurateCollision=Mock(), updateHeights=Mock())
            self.areas.append(item)
            return item
        self.keyboard = KeyboardService(blocked=lambda:False)
        self.ns = load('arty_splash', dict(BigWorld=NS(Model=type('Model', (), {'scale':None}),
            PyTerrainSelectedArea=area, player=lambda:self.player), Math=NS(Vector2=lambda *v:v),
            StaticWorldObjectMarker3D=marker, getPlayer=lambda:self.player, keyboard=self.keyboard,
            Vehicle=NS(getVehicleClassTag=lambda tags:tags), VEHICLE_CLASS_NAME=NS(SPG='SPG'),
            CTRL_MODE_NAME=NS(ARCADE='arcade', SNIPER='sniper', STRATEGIC='strategic', ARTY='arty'),
            checkKeys=lambda key:key == self.config.data['buttonShowSplash'], logException=lambda fn:fn, sendPanelMessage=Mock()))
        self.controller = self.ns['ArtySplashController'](self.config)
        self.addCleanup(self.controller.stopBattle)

    def test_models_created_once_and_removed_between_battles_without_changing_settings(self):
        before = deepcopy(self.config.data)
        self.controller.startBattle(); self.controller.startBattle(); self.controller.working()
        self.assertEqual(len(self.models), 2)
        self.assertEqual(len(self.keyboard.callbacks), 1)
        self.assertEqual(self.models[0].model.scale, (8, 8, 8))
        self.assertEqual(self.models[1].model.scale, (.5, .5, .5))
        self.assertEqual(self.models[0].model.position, (10, 20, 30))
        self.assertTrue(self.models[0].model.visible)
        self.controller.stopBattle(); self.controller.stopBattle()
        self.assertFalse(self.areas[0].attached)
        for model in self.models: model.clear.assert_called_once()
        self.assertEqual(self.keyboard.callbacks, [])
        self.assertEqual(self.config.data, before)
        self.assertFalse(hasattr(self.config, 'modelSplash'))
        self.controller.startBattle()
        self.assertEqual(len(self.models), 4)

    def test_shortcut_state_resets_and_disabled_module_ignores_input(self):
        self.controller.startBattle(); self.controller.working()
        self.controller.injectButton(NS(isKeyDown=lambda:True))
        self.assertFalse(self.controller.modelSplashVisible)
        self.controller.working()
        self.assertFalse(self.models[0].model.visible)
        self.controller.stopBattle(); self.controller.startBattle(); self.controller.working()
        self.assertTrue(self.controller.modelSplashVisible)
        self.ns['settings_service'].apply(self.config, {'enabled':False}, persist=False)
        self.controller.working(); self.controller.injectButton(NS(isKeyDown=lambda:True))
        self.assertFalse(self.controller.modelSplash.model.visible)
        self.ns['sendPanelMessage'].assert_called_once()
        self.controller.stopBattle(); self.controller.startBattle()
        self.assertEqual(self.keyboard.callbacks, [])
        self.assertIsNone(self.controller.modelSplash)

    def test_shell_vehicle_and_camera_filters_preserved(self):
        self.controller.startBattle(); self.controller.working()
        self.desc.shot.shell.kind = 'ARMOR_PIERCING'; self.controller.working()
        self.assertFalse(self.models[0].model.visible)
        self.desc.shot.shell.kind = 'HIGH_EXPLOSIVE'; self.desc.type.tags = 'heavyTank'; self.controller.working()
        self.assertFalse(self.models[0].model.visible)
        self.desc.type.tags = 'SPG'; self.player.inputHandler.ctrlModeName = 'arcade'; self.controller.working()
        self.assertFalse(self.models[0].model.visible)
        self.player.inputHandler.ctrlModeName = 'arty'; self.controller.working()
        self.assertTrue(self.models[0].model.visible)


if __name__ == '__main__': unittest.main()
