# -*- coding: utf-8 -*-
import copy
import json
import os
from collections import namedtuple

from support import ROOT, RuntimeTest, module, source


class CameraSettingsTests(RuntimeTest):
    def setUp(self):
        super(CameraSettingsTests, self).setUp()
        self.policy = self.load('core.camera_settings')
        with open(os.path.join(ROOT, 'res/configs/driftkings/default/third_person_zoom.json'), 'rb') as stream:
            self.values = json.load(stream)
        self.api = source('battle/third_person_zoom.py', {
            'AvatarInputHandler.DynamicCameras.ArcadeCamera': module(ArcadeCamera=object),
            'AvatarInputHandler.DynamicCameras.StrategicCamera': module(StrategicCamera=object),
            'AvatarInputHandler.DynamicCameras.ArtyCamera': module(ArtyCamera=object),
            'AvatarInputHandler.control_modes': module(PostMortemControlMode=object),
            'driftkings._constants': module(MinMax=namedtuple('MinMax', 'min max')),
            'driftkings.core.hooks': module(override=lambda *args: lambda fn: fn),
            'driftkings.settings.service': module(settings_service=module(getComponentDict=lambda cfg: self.values)),
            'driftkings.settings.definitions.battle.third_person_zoom': module(ThirdPersonZoomSettings=object),
        })


    def test_defaults_keep_arcade_and_native_artillery(self):
        self.policy.validate(self.values)
        self.assertEqual(self.policy.options(self.values, 'arcade')['max'], 400)
        self.assertEqual(self.policy.options(self.values, 'postmortem')['startDist'], 60)
        self.assertIsNone(self.policy.options(self.values, 'strategic'))
        self.assertIsNone(self.policy.options(self.values, 'arty'))

    def test_invalid_ranges_starts_and_nonfinite_values_are_rejected(self):
        for key, value in (('min', 401), ('startDist', 500), ('max', float('inf')),
                           ('min', float('nan')), ('scrollSensitivity', True)):
            values = copy.deepcopy(self.values)
            values['arcade'][key] = value
            with self.assertRaises(ValueError):
                self.policy.validate(values)

    def test_artillery_keeps_actual_native_values_not_hardcoded_reference_values(self):
        camera = module(_baseCfg={})
        def original(camera):
            camera._baseCfg.update(distRange=(66, 177), scrollSensitivity=7, other='keep')
            return 'native result'
        for method in ('new_read_strategic_base_cfg', 'new_read_arty_base_cfg'):
            self.assertEqual(self.api[method](original, camera), 'native result')
            self.assertEqual(camera._baseCfg, {'distRange': (66, 177), 'scrollSensitivity': 7, 'other': 'keep'})

    def test_artillery_overrides_are_independent_when_selected(self):
        self.values['strategic'].update(useClientDefaults=False, min=50, max=150, scrollSensitivity=6)
        camera = module(_baseCfg={'distRange': (66, 177), 'other': 'keep'})
        self.api['new_read_strategic_base_cfg'](lambda camera: None, camera)
        self.assertEqual(camera._baseCfg['distRange'], (50, 150))
        self.assertEqual(camera._baseCfg['other'], 'keep')
        self.assertEqual(self.values['arcade']['max'], 400)
        self.assertTrue(self.values['arty']['useClientDefaults'])

    def test_postmortem_and_arcade_have_independent_ranges(self):
        camera = module(_baseCfg={}, _ArcadeCamera__postmortemMode=True)
        self.values['postmortem'].update(min=20, max=200)
        self.api['new_read_arcade_base_cfg'](lambda camera: None, camera)
        self.assertEqual(tuple(camera._baseCfg['distRange']), (20, 200))
        camera._ArcadeCamera__postmortemMode = False
        self.api['new_read_arcade_base_cfg'](lambda camera: None, camera)
        self.assertEqual(tuple(camera._baseCfg['distRange']), (10, 400))

    def test_create_sets_mode_before_consuming_start_distance(self):
        self.values['postmortem']['startDist'] = 90
        updated = []
        camera = module(_cfg={}, _updateProperties=lambda: updated.append(True))
        def original(camera, callback, postmortem, smart):
            self.assertTrue(camera._ArcadeCamera__postmortemMode)
            self.assertEqual(camera._cfg['startDist'], 90)
            self.assertEqual(tuple(camera._distRange), (10, 400))
            return 123
        self.assertEqual(self.api['new_create_arcade'](original, camera, postmortemMode=True), 123)
        self.assertEqual(updated, [True])

    def test_disabling_preserves_native_camera_values(self):
        self.values['enabled'] = False
        camera = module(_baseCfg={'distRange': (2, 25)}, _cfg={'startDist': 12},
                        _updateProperties=lambda: self.fail('must not force a disabled profile'))
        self.api['new_read_arcade_base_cfg'](lambda camera: None, camera)
        self.api['new_create_arcade'](lambda *args: None, camera)
        self.assertEqual(camera._baseCfg['distRange'], (2, 25))
        self.assertEqual(camera._cfg, {'startDist': 12})
