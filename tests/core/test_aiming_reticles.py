# -*- coding: utf-8 -*-
"""Aiming reticles: client globals are changed while enabled and always restored."""
import collections
import json
import os

from support import Event, RuntimeTest, Settings, game_source, module, stub

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
with open(os.path.join(ROOT, 'res', 'configs', 'driftkings', 'default', 'aiming_reticles.json'), 'rb') as stream:
    DEFAULTS = json.loads(stream.read().decode('utf-8-sig'))
MarkerInfo = collections.namedtuple('MarkerInfo', ('size', 'dualAccSize', 'position', 'direction', 'sizeOffset'))
MODES = module(ARCADE='arcade', STRATEGIC='strategic', SNIPER='sniper', ARTY='arty')


class AimingReticlesTests(RuntimeTest):
    def setUp(self):
        super(AimingReticlesTests, self).setUp()
        self.data = dict(DEFAULTS, gunMarkerMinimumSize=18, percentCorrection=50)
        self.synced, self.server = True, []
        self.cache = module(isSynced=lambda: self.synced, onSyncCompleted=Event())
        self.constants = stub('aih_constants', GUN_MARKER_MIN_SIZE=32, CTRL_MODE_NAME=MODES)
        self.factory = stub('gm_factory', _GUN_MARKER_LINKAGES={'native': 'linkage'})
        self.service = Settings(self.data)
        self.service.affects = lambda changes, *keys: any(key in changes for key in keys)
        self.api, self.hooks = game_source('battle/aiming_reticles.py', {
            'driftkings.settings.service': module(settings_service=self.service, affects=self.service.affects),
            'aih_constants': self.constants,
            'driftkings.flash.battle.aiming_reticles': module(
                CUSTOM_GUN_MARKER_LINKAGES={'server': 'custom'},
                get_linkages=lambda: self.factory._GUN_MARKER_LINKAGES,
                set_linkages=lambda value: setattr(self.factory, '_GUN_MARKER_LINKAGES', value),
                set_state=lambda state: None),
            'gui.Scaleform.daapi.view.battle.shared.crosshair': stub('crosshair', gm_factory=self.factory),
            'helpers': module(dependency=module(instance=lambda interface: self.cache)),
        }, real=('driftkings._constants',))
        self.api['enableServerAiming'] = lambda: self.server.append('enabled')
        self.reticle = self.api['reticle']
        self.reticle.start()
        self.addCleanup(self.reticle.stop)

    def test_start_applies_size_and_correction_then_stop_restores_them(self):
        self.assertEqual(self.constants.GUN_MARKER_MIN_SIZE, 18)
        self.assertAlmostEqual(self.reticle.reticleScaleFactor, 1.355)
        self.reticle.stop()
        self.assertEqual(self.constants.GUN_MARKER_MIN_SIZE, 32)
        self.assertEqual((self.reticle.reticleScaleFactor, self.reticle.showClientAndServerReticle), (1, False))
        self.assertEqual(self.factory._GUN_MARKER_LINKAGES, {'native': 'linkage'})

    def test_disabling_the_module_restores_native_values(self):
        self.data['enabled'] = False
        self.reticle.onModSettingsChanged('aiming_reticles', {'enabled': False})
        self.assertEqual((self.constants.GUN_MARKER_MIN_SIZE, self.reticle.reticleScaleFactor), (32, 1))

    def test_a_change_only_updates_its_own_option(self):
        self.data.update(gunMarkerMinimumSize=24, percentCorrection=0)
        self.reticle.onModSettingsChanged('aiming_reticles', {'gunMarkerMinimumSize': 24})
        self.assertEqual(self.constants.GUN_MARKER_MIN_SIZE, 24)
        self.assertAlmostEqual(self.reticle.reticleScaleFactor, 1.355)

    def test_server_reticle_adds_linkages_and_waits_for_synced_settings(self):
        self.data['showClientAndServerReticleBeta'] = True
        self.reticle.onModSettingsChanged('aiming_reticles', {'showClientAndServerReticleBeta': True})
        self.assertIn('native', self.factory._GUN_MARKER_LINKAGES)
        self.assertGreater(len(self.factory._GUN_MARKER_LINKAGES), 1)
        self.synced = False
        self.reticle.ensureServerAiming()
        self.assertEqual(self.server, [])
        self.cache.onSyncCompleted()
        self.assertEqual(self.server, ['enabled'])
        self.assertEqual(self.cache.onSyncCompleted.handlers, [])
        self.data['showClientAndServerReticleBeta'] = False
        self.reticle.onModSettingsChanged('aiming_reticles', {'showClientAndServerReticleBeta': False})
        self.assertEqual(self.factory._GUN_MARKER_LINKAGES, {'native': 'linkage'})

    def test_marker_size_is_corrected_only_in_the_aiming_modes(self):
        original = MarkerInfo(271.0, 135.5, (1, 2, 3), (0, 0, 1), 7)
        for name in ('updateClientGunMarker', 'updateServerGunMarker', 'updateDualAccGunMarker'):
            received = []
            native = lambda handler, info, support, relax: received.append((info, support, relax))
            update = self.hooks.get('AvatarInputHandler', name)
            for mode in ('arcade', 'strategic', 'arty', 'sniper', 'postmortem'):
                update(native, module(ctrlModeName=mode), original, 'support', 0.1)
                info, support, relax = received[-1]
                expected = 271.0 if mode == 'postmortem' else 200.0
                self.assertAlmostEqual(info.size, expected)
                self.assertAlmostEqual(info.dualAccSize, expected / 2)
                self.assertEqual((info.position, info.direction, info.sizeOffset), (original.position, original.direction, 7))
                self.assertEqual((support, relax), ('support', 0.1))

    def test_spg_cone_matches_corrected_diameter_and_keeps_native_side_effects(self):
        calls, angles = [], []
        controller = module(_gunRotator=module(dispersionAngle=0.1355),
                            _dataProvider=module(setupConicDispersion=angles.append))
        self.api['BattleReplay'] = module(g_replayCtrl=module(isPlaying=False))
        update = self.hooks.get('_SPGGunMarkerController', '_updateDispersionData')
        native = lambda instance: calls.append('native') or 'result'
        self.assertEqual(update(native, controller), 'result')
        self.assertEqual(calls, ['native'])
        self.assertAlmostEqual(angles[-1], 0.1)
        self.reticle.reticleScaleFactor = 1
        update(native, controller)
        self.assertEqual(len(angles), 1)
        self.assertEqual(len(calls), 2)

    def test_spg_cone_uses_replay_angle_and_falls_back_for_missing_recording(self):
        angles = []
        controller = module(_gunRotator=module(dispersionAngle=0.1355),
                            _dataProvider=module(setupConicDispersion=angles.append))
        recorded = [0.271, 0.0]
        self.api['BattleReplay'] = module(g_replayCtrl=module(
            isPlaying=True, isClientReady=True, getSPGGunMarkerParams=lambda: recorded))
        update = self.hooks.get('_SPGGunMarkerController', '_updateDispersionData')
        update(lambda instance: None, controller)
        self.assertAlmostEqual(angles[-1], 0.2)
        recorded[:] = [-1.0, -1.0]
        update(lambda instance: None, controller)
        self.assertAlmostEqual(angles[-1], 0.1)
