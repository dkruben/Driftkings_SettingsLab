import ast
from collections import namedtuple
from copy import deepcopy
from functools import partial
import math
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings._constants import AIMING_ANGLES, ARCADE_ZOOM, GLOBAL
from Driftkings.core.overlay import OverlayScene, Align, ElementType
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults


def load(path, namespace, constants=False):
    path = CLIENT / 'Driftkings' / path
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) or
                 constants and isinstance(node, ast.Assign) and
                 isinstance(node.targets[0], ast.Name) and node.targets[0].id.isupper()]
    for node in tree.body:
        if isinstance(node, ast.FunctionDef): node.decorator_list = []
    exec(compile(tree, str(path), 'exec'), namespace)
    return namespace


class AimingControllerTests(unittest.TestCase):
    def setUp(self):
        self.scene = OverlayScene()
        self.service = SettingsService(SettingsData())
        self.config = NS(ID=AIMING_ANGLES.ID, data=defaults(AIMING_ANGLES.ID))
        self.config.data.update(horizontal=2, vertical=3)
        self.pending = {}
        self.cancelled = []
        def schedule(delay, fn):
            token = len(self.pending) + len(self.cancelled) + 1
            self.pending[token] = fn
            return token
        def cancel(token):
            self.pending.pop(token, None)
            self.cancelled.append(token)
        self.ns = dict(overlays=self.scene, Align=Align, ElementType=ElementType,
            settings_service=self.service, AIMING_ANGLES=AIMING_ANGLES, GLOBAL=GLOBAL,
            ServicesLocator=NS(settingsCore=NS(getSetting=lambda _:0)),
            settings_constants=NS(SPGAim=NS(SPG_STRATEGIC_CAM_MODE='spgMode')),
            math=math, partial=partial, callback=schedule, cancelCallback=cancel,
            override=Mock(), getPlayer=lambda:NS(isObserver=lambda:False),
            BigWorld=NS(screenWidth=lambda:1920, screenHeight=lambda:1080, getAspectRatio=lambda:16./9,
                        projection=lambda:NS(fov=1), wg_calcGunPitchLimits=lambda *args:(-.2, .3)),
            CTRL_MODE_NAME=NS(ARCADE='arcade', SNIPER='sniper', DUAL_GUN='dual', STRATEGIC='strategic', ARTY='arty'))
        for name in ('AvatarInputHandler', 'MapCaseMode', 'PlayerAvatar', 'InterfaceScaleSetting', 'plugins',
                     'ArcadeCamera', 'SniperCamera', 'ArtyCamera', 'StrategicCamera', 'Vehicle', 'FovExtended'):
            self.ns[name] = type(name, (), {})
        load('views/battle/aiming_angles.py', self.ns)
        load('battle/aiming_angles.py', self.ns, constants=True)
        self.controller = self.ns['AimingAnglesController'](self.config)

    def vehicle(self, player=True):
        gun = NS(pitchLimits={'absolute':(-.2, .3), 'maxPitch':.3, 'minPitch':-.2},
                 staticTurretYaw=None, turretYawLimits=(-.4, .4), staticPitch=False)
        return NS(isPlayerVehicle=player, isAlive=True, gunAnglesPacked=32785,
                  typeDescriptor=NS(gun=gun, hull=NS(turretPitches=[0]), turret=NS(gunJointPitch=0)))

    def props(self, suffix):
        return self.scene.elements[self.config.ID + suffix][1]

    def test_rendering_reads_settings_without_storing_coordinates_in_config(self):
        before = deepcopy(self.config.data)
        self.controller.ON_ANGLES_AIMING()
        self.assertEqual(self.scene.elements, {})
        self.controller.createUI(); self.controller.createUI()
        self.assertEqual(len(self.scene.elements), 5)
        native = Mock(return_value='vehicle-ready')
        result = self.controller.Vehicle__onAppearanceReady(native, self.vehicle())
        self.assertEqual(result, 'vehicle-ready')
        self.assertEqual(self.props('.L')['image'], '../AimingAngles/2/Left.png')
        self.assertEqual(self.props('.lo')['image'], '../AimingAngles/3/Bottom.png')
        self.assertLess(self.props('.L')['x'], 0)
        self.assertGreater(self.props('.R')['x'], 0)
        self.assertEqual(self.config.data, before)
        self.assertFalse(hasattr(self.config, 'smoothingID'))
        self.service.apply(self.config, {'horizontal':4, 'vertical':0}, persist=False)
        self.controller.ON_ANGLES_AIMING()
        self.assertEqual(self.props('.L')['image'], '../AimingAngles/4/Left.png')
        self.assertEqual(self.props('.lo')['image'], '')
        self.service.apply(self.config, {'enabled':False}, persist=False)
        self.controller.ON_ANGLES_AIMING()
        self.assertTrue(all(self.props(suffix)['image'] == '' for suffix in ('.L', '.R', '.lo', '.hi')))
        self.controller.destroyUI(); self.controller.destroyUI()
        self.controller.ON_ANGLES_AIMING()
        self.assertEqual(self.scene.elements, {})

    def start_smoothing(self):
        self.controller.set_gunAnglesPacked(Mock(), self.vehicle())
        self.assertIsNotNone(self.controller.smoothingID)
        self.assertTrue(self.pending)

    def test_smoothing_cancelled_on_death_respawn_map_case_and_battle_exit(self):
        self.controller.createUI()
        for transition in ('death', 'respawn', 'mapCase', 'endBattle'):
            with self.subTest(transition=transition):
                self.controller.Vehicle__onAppearanceReady(Mock(), self.vehicle())
                self.start_smoothing()
                token = self.controller.smoothingID
                native = Mock(return_value='native')
                if transition == 'death':
                    self.controller.Vehicle__onVehicleDeath(native, self.vehicle())
                    self.assertFalse(self.controller.isAlive)
                elif transition == 'respawn':
                    self.controller.Vehicle__onAppearanceReady(native, self.vehicle())
                    self.assertTrue(self.controller.isAlive)
                    self.assertEqual(self.controller.old_gunAnglesPacked, 0)
                elif transition == 'mapCase':
                    self.controller.anglesAiming_activateMapCase(native, 42)
                    self.assertTrue(self.controller.isMapCase)
                else:
                    self.assertEqual(self.controller.onDestroyGUI(native, 42), 'native')
                    native.assert_called_once_with(42)
                    self.assertFalse(self.controller.isAlive)
                self.assertIn(token, self.cancelled)
                self.assertEqual(self.pending, {})
                self.assertIsNone(self.controller.smoothingID)
        self.controller.endBattle()
        self.assertEqual(self.props('.L')['x'], -20000)

    def test_enemy_death_does_not_cancel_own_animation_and_camera_hook_preserves_arguments(self):
        self.controller.Vehicle__onAppearanceReady(Mock(), self.vehicle())
        self.start_smoothing()
        self.controller.Vehicle__onVehicleDeath(Mock(), self.vehicle(player=False))
        self.assertTrue(self.pending)
        self.assertTrue(self.controller.isAlive)
        native = Mock(return_value=73)
        self.assertEqual(self.controller.onCameraEnabled(native, 'camera', position=42), 73)
        native.assert_called_once_with('camera', position=42)
        self.assertEqual(self.pending, {})
        handler = NS(_AvatarInputHandler__isArenaStarted=True)
        self.controller.AvatarInputHandler_onControlModeChanged(native, handler, 'sniper')
        self.assertEqual(self.controller.aimMode, 'sn')
        self.assertEqual(self.controller.y, 0)
        self.controller.AvatarInputHandler_onControlModeChanged(native, handler, 'arcade')
        self.assertEqual(self.controller.aimMode, 'arc')
        self.assertAlmostEqual(self.controller.y, -1080 * .0775)


class ArcadeCameraControllerTests(unittest.TestCase):
    def setUp(self):
        self.config = NS(ID=ARCADE_ZOOM.ID, data=defaults(ARCADE_ZOOM.ID))
        self.service = SettingsService(SettingsData())
        self.ns = dict(config=self.config, settings_service=self.service, ARCADE_ZOOM=ARCADE_ZOOM,
                       GLOBAL=GLOBAL, MinMax=namedtuple('MinMax', ('min', 'max')),
                       logError=Mock(), LOG_CURRENT_EXCEPTION=Mock())
        load('battle/arcade_zoom.py', self.ns)
        self.ns['camera_state'] = self.ns['CameraConfigState']()

    def camera(self, name):
        obj = type(name, (), {})()
        obj._baseCfg = {'base':1}; obj._userCfg = {'user':2}; obj._cfg = {'cfg':3}
        return obj

    def test_each_camera_type_is_prepared_once_without_mutating_preferences(self):
        before = deepcopy(self.config.data)
        for name in ('ArcadeCamera', 'StrategicCamera', 'ArtyCamera'):
            camera = self.camera(name)
            native = Mock(return_value=name)
            self.assertEqual(self.ns['new_read_configs'](native, camera, 'section'), name)
            native.assert_called_once_with(camera, 'section')
            self.assertEqual([camera._baseCfg, camera._userCfg, camera._cfg], [{}, {}, {}])
            camera._cfg['loaded'] = True
            self.ns['new_read_configs'](native, camera, 'section')
            self.assertEqual(camera._cfg, {'loaded':True})
        self.assertEqual(self.config.data, before)
        self.assertFalse(hasattr(self.config, 'camCache'))

    def test_failed_preparation_can_retry_and_still_calls_native(self):
        camera = self.camera('ArcadeCamera')
        del camera._userCfg
        native = Mock(return_value='native')
        self.assertEqual(self.ns['new_read_configs'](native, camera, 'data'), 'native')
        self.ns['logError'].assert_called_once()
        camera._userCfg = {'native':1}
        self.ns['new_read_configs'](native, camera, 'data')
        self.assertEqual(camera._userCfg, {})
        self.assertEqual(native.call_count, 2)

    def test_camera_options_and_postmortem_arguments_are_preserved(self):
        camera = self.camera('ArcadeCamera')
        self.service.apply(self.config, {'enabled':True, 'min':5., 'max':120.,
                                        'scrollSensitivity':3., 'startDeadDist':40.}, persist=False)
        self.ns['new_read_arcade_base_cfg'](Mock(), camera)
        self.assertEqual(camera._baseCfg['distRange'], (5., 120.))
        self.assertEqual(camera._baseCfg['scrollSensitivity'], 3.)
        native = Mock()
        avatar = NS(camera=NS(angles=(1, 2)))
        self.ns['new_enable_post_mortem'](native, avatar, postmortemParams='old', another=4)
        native.assert_called_once_with(avatar, postmortemParams=((1, 2), 40.), transitionDuration=1., another=4)
        self.service.apply(self.config, {'enabled':False}, persist=False)
        camera._baseCfg = {'native':5}
        self.ns['new_read_arcade_base_cfg'](Mock(), camera)
        self.assertEqual(camera._baseCfg, {'native':5})


if __name__ == '__main__':
    unittest.main()
