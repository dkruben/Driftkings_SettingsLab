# -*- coding: utf-8 -*-
"""Gun traverse limits: server angle decoding, smoothing and the corner positions on screen."""
import math

from support import RuntimeTest, game_source, module

MODES = module(ARCADE='arcade', SNIPER='sniper', DUAL_GUN='dualGun', STRATEGIC='strategic', ARTY='arty', MAP_CASE='mapcase')


class GunTraverseSettingsTests(RuntimeTest):
    def setUp(self):
        super(GunTraverseSettingsTests, self).setUp()
        constants = self.load('_constants')
        from support import source
        api = source('settings/definitions/battle/gun_traverse_limits.py', {
            'driftkings._constants': constants,
            'driftkings.settings.controls_schema': self.load('settings.controls_schema'),
            'driftkings.settings.definitions.base': module(SectionDefinition=object)})
        self.settings = api['GunTraverseLimitsSettings']()

    def test_no_markers_forces_module_off_but_keeps_manual_disable(self):
        values = {'enabled': True, 'horizontal': 0, 'vertical': 0}
        self.assertFalse(self.settings.normalize_loaded(values)['enabled'])
        for horizontal, vertical in ((1, 0), (0, 6), (2, 3)):
            values = {'enabled': False, 'horizontal': horizontal, 'vertical': vertical}
            self.assertFalse(self.settings.normalize_changes(values, {'horizontal': horizontal})['enabled'])
            values['enabled'] = True
            self.assertTrue(self.settings.normalize_changes(values, {'enabled': True})['enabled'])


class GunTraverseLimitsTests(RuntimeTest):
    def setUp(self):
        super(GunTraverseLimitsTests, self).setUp()
        self.callbacks = []
        self.player = module(isObserver=lambda: False)
        world = module(screenWidth=lambda: 1920, screenHeight=lambda: 1000, getAspectRatio=lambda: 2.0,
                       projection=lambda: module(fov=1.0),
                       wg_calcGunPitchLimits=lambda yaw, lo, hi, turret, joint: (-0.3, 0.1))
        self.api, self.hooks = game_source('battle/gun_traverse_limits.py', {
            'BigWorld': world,
            'driftkings.game_constants': module(CTRL_MODE_NAME=MODES),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: self.player),
            'driftkings.core.callbacks': module(callback=lambda delay, function: self.callbacks.append(function) or len(self.callbacks),
                                                cancelCallback=lambda handle: None),
        })
        self.controller = self.api['controller']

    def vehicle(self, yaw_limits=(-0.5, 0.5), static_pitch=False, alive=True):
        gun = module(pitchLimits={'absolute': (-0.3, 0.33), 'maxPitch': (), 'minPitch': ()},
                     staticTurretYaw=None, turretYawLimits=yaw_limits, staticPitch=static_pitch)
        return module(isPlayerVehicle=True, isAlive=alive, gunAnglesPacked=0,
                      typeDescriptor=module(gun=gun, hull=module(turretPitches=[0.0]), turret=module(gunJointPitch=0.0)))

    def appear(self, vehicle):
        self.controller.Vehicle__onAppearanceReady(lambda vehicle: None, vehicle)

    def test_appearance_reads_the_gun_limits(self):
        vehicle = self.vehicle()
        self.appear(vehicle)
        controller = self.controller
        self.assertEqual((controller.leftLimits, controller.rightLimits), (-0.5, 0.5))
        self.assertAlmostEqual(controller.pitchStep, 0.01)
        self.assertTrue(controller.showCorners)
        # 1920 px over a 2 rad horizontal view: 960 px per radian.
        self.assertEqual(controller.dataHor, [-480, 480])
        self.appear(self.vehicle(yaw_limits=None, static_pitch=True))
        self.assertFalse(controller.showCorners)
        self.assertEqual(controller.coordinate(0.0, 0.0), ([-20000, 20000], [20000, -20000]))

    def test_corners_stick_to_the_screen_edge_once_reached(self):
        self.appear(self.vehicle())
        self.assertEqual(self.controller.coordinate(0.0, 0.0)[0], [-480, 480])
        # At the limit, the corner stays at the aim centre instead of crossing it.
        self.assertEqual(self.controller.coordinate(0.5, 0.0)[0], [-960, 0])
        self.assertEqual(self.controller.coordinate(-0.5, 0.0)[0], [0, 960])

    def test_server_angles_are_decoded_and_smoothed_in_three_steps(self):
        vehicle = self.vehicle()
        self.appear(vehicle)
        # Yaw code 768 of 1024 is +pi/2; pitch code 30 of 63 is -0.3 + 30 * 0.01.
        vehicle.gunAnglesPacked = 768 << 6 | 30
        self.controller.set_gunAnglesPacked(lambda vehicle: None, vehicle)
        self.assertAlmostEqual(self.controller.yaw, math.pi / 2)
        self.assertAlmostEqual(self.controller.pitch, 0.0)
        steps = 1
        while self.callbacks:
            self.callbacks.pop(0)()
            steps += 1
        self.assertEqual(steps, 3)
        self.assertEqual(self.controller.dataHor, self.controller.coordinate(math.pi / 2, 0.0)[0])
        # The same packed value is ignored.
        self.controller.set_gunAnglesPacked(lambda vehicle: None, vehicle)
        self.assertEqual(self.callbacks, [])

    def test_observers_and_map_case_hide_the_corners(self):
        vehicle = self.vehicle()
        self.appear(vehicle)
        self.player = module(isObserver=lambda: True)
        vehicle.gunAnglesPacked = 5
        self.controller.set_gunAnglesPacked(lambda vehicle: None, vehicle)
        self.assertEqual(self.controller.dataHor, [-20000, 20000])
        self.controller.anglesAiming_activateMapCase(lambda: None)
        self.assertTrue(self.controller.isMapCase)
        self.controller.updateCoordinates()
        self.assertEqual(self.controller.dataHor, [-20000, 20000])

    def test_dead_vehicle_reports_off_screen_corners(self):
        self.appear(self.vehicle())
        self.assertEqual(self.controller.anglesAiming_left(5), -475)
        self.controller.Vehicle__onVehicleDeath(lambda vehicle: None, self.vehicle())
        self.assertEqual((self.controller.anglesAiming_left(), self.controller.anglesAiming_right(),
                          self.controller.anglesAiming_bottom(), self.controller.anglesAiming_top()),
                         (-20000, 20000, 20000, -20000))

    def test_aim_mode_moves_the_corners_with_the_arcade_reticle(self):
        handler = module(_AvatarInputHandler__isArenaStarted=True)
        self.controller.AvatarInputHandler_onControlModeChanged(lambda handler, mode: None, handler, MODES.SNIPER)
        self.assertEqual((self.controller.aimMode, self.controller.y), ('sn', 0.0))
        self.controller.AvatarInputHandler_onControlModeChanged(lambda handler, mode: None, handler, MODES.ARCADE)
        self.assertEqual((self.controller.aimMode, self.controller.aim_y()), ('arc', -77))
        self.controller.AvatarInputHandler_onControlModeChanged(lambda handler, mode: None, handler, MODES.MAP_CASE)
        self.assertIsNone(self.controller.aimMode)
