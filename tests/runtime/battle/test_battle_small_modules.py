# -*- coding: utf-8 -*-
"""Small battle modules: server turret sync, distance marker lifecycle and view entry points."""
from support import RuntimeTest, Settings, game_source, module, source

create_range = source('common/utils/wgutils.py', {'BigWorld': module()})['create_range']


class ServerTurretSyncTests(RuntimeTest):
    def setUp(self):
        super(ServerTurretSyncTests, self).setUp()
        self.data = {'enabled': True, 'serverTurret': True, 'activateMessage': True}
        self.scheduled = []
        self.api, self.hooks = game_source('battle/server_turret_sync.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'driftkings.core.callbacks': module(callback=lambda delay, function: self.scheduled.append(delay)),
        }, real=('driftkings._constants',))
        self.wrapper = self.hooks.get('VehicleGunRotator', 'setShotPosition')

    def rotate(self):
        calls = []
        rotator = module(_avatar=module(vehicle=module(getServerGunAngles=lambda: (0.4, -0.1))),
                         _VehicleGunRotator__turretYaw=0.0, _VehicleGunRotator__gunPitch=0.0)
        self.wrapper(lambda *args: calls.append(args), rotator, 1, 'pos', 'vec', 0.01)
        return rotator, calls[0]

    def test_shot_position_uses_the_server_gun_angles(self):
        rotator, call = self.rotate()
        self.assertEqual((rotator._VehicleGunRotator__turretYaw, rotator._VehicleGunRotator__gunPitch), (0.4, -0.1))
        self.assertIs(call[-1], True)

    def test_disabled_option_or_module_keeps_the_client_angles(self):
        for key in ('serverTurret', 'enabled'):
            self.data.update(enabled=True, serverTurret=True)
            self.data[key] = False
            rotator, call = self.rotate()
            self.assertEqual(rotator._VehicleGunRotator__turretYaw, 0.0)
            self.assertIs(call[-1], False)

    def test_client_angle_decoding_is_left_alone(self):
        # The client's decoders also draw its native server reticle; the mod must not replace them.
        self.assertNotIn('decodeAngleFromUint', self.api)
        self.assertNotIn('gun_rotation_shared', self.api)

    def test_activation_message_is_scheduled_at_battle_start(self):
        start = self.hooks.events['driftkings.common.utils.events.PlayerAvatar.startGUI.after'][0]
        start()
        self.data['activateMessage'] = False
        start()
        self.assertEqual(self.scheduled, [5.0])


class TargetDistanceTests(RuntimeTest):
    def setUp(self):
        super(TargetDistanceTests, self).setUp()
        self.data = {'enabled': True}
        self.created, self.moves = [], []
        test = self

        class Controller(object):
            def __init__(self, clazz):
                self.closed = False
                test.created.append(self)

            def close(self):
                self.closed = True

            @staticmethod
            def onMouseEvent(dx, dy):
                test.moves.append((dx, dy))

        self.api, self.hooks = game_source('battle/target_distance.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'driftkings.flash.battle.target_distance': module(DistanceMarkerController=Controller,
                                                              DistanceMarkerView=object, ALIAS='alias'),
        }, real=('driftkings._constants',))

    def test_marker_lives_between_plugin_start_and_stop(self):
        plugin = module(_clazz='markers')
        mouse = self.hooks.get('AvatarInputHandler', 'handleMouseEvent')
        mouse(lambda handler, event: None, 'handler', module(dx=1, dy=2))
        self.hooks.get('VehicleMarkerPlugin', 'start')(lambda plugin: None, plugin)
        mouse(lambda handler, event: None, 'handler', module(dx=3, dy=4))
        self.hooks.get('VehicleMarkerPlugin', 'start')(lambda plugin: None, plugin)
        self.assertEqual((len(self.created), self.moves), (1, [(3, 4)]))
        self.hooks.get('VehicleMarkerPlugin', 'stop')(lambda plugin: None, plugin)
        self.assertTrue(self.created[0].closed)
        self.assertIsNone(self.api['g_distanceMarker'])

    def test_disabled_module_creates_no_marker(self):
        self.data['enabled'] = False
        self.hooks.get('VehicleMarkerPlugin', 'start')(lambda plugin: None, module(_clazz='markers'))
        self.assertEqual(self.created, [])


class EntryPointTests(RuntimeTest):
    def test_view_modules_register_their_battle_view(self):
        for name, view in (('aiming_countdown', 'DispersionTimer'), ('shell_flight_time', None)):
            api, _ = game_source('battle/%s.py' % name, real=('driftkings._constants',))
            views = api['getBattleViews']()
            self.assertEqual(len(views), 1, name)
            alias, view_class, config = views[0]
            self.assertIs(config, api['config'], name)
            self.assertTrue(alias, name)


class BattlePerformanceWn8Tests(RuntimeTest):
    def test_wnx_live_assistance_and_results_use_the_same_formula_and_template(self):
        colors = self.load('common.utils.colorratting')
        wnx = self.load('core.wnx')
        expected = dict(damage=1000, frags=.8, spots=.9, assist=250)
        targets = [expected]
        settings = {'enabled': True, 'colorRatting': 3, 'format': '{wnx}:{c:wnx}',
                    'battleResultsFormat': '{wnx}:{c:wnx}'}
        player = module(arena=module(bonusType=None))
        api, _ = game_source('components/battle_performance.py', {
            'driftkings.common.utils.colorratting': colors,
            'driftkings.common.utils.formatting': self.load('common.utils.formatting'),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: player, create_range=create_range),
            'driftkings.core.wnx': module(calculate=wnx.calculate, get_expected=lambda ident: targets[0]),
            'driftkings.stats.vehinfo': module(getVehicleInfoData=lambda ident: {
                'level': 8, 'wn8expDamage': 1000, 'wn8expSpot': 1, 'wn8expFrag': 1,
                'wn8expDef': 1, 'wn8expWinRate': 52}, calculateRatingScale=lambda *args: 0,
                calculateXTE=lambda *args: 0),
            'driftkings.settings.service': Settings(settings).service(),
            'gui.battle_results.pbs_helpers.common': module(getArenaNameStr=lambda reusable: 'map'),
            'gui.battle_results.settings': module(PLAYER_TEAM_RESULT=module(WIN=1)),
        }, real=('driftkings._constants',))
        bonus = next(iter(api['SUPPORTED_BONUS_TYPES']))
        player.arena.bonusType = bonus
        displayed = []
        api['g_flash'] = module(addText=displayed.append, setVisible=lambda value: None)
        api['g_calculator'].registerVInfoData(1)
        battle = api['g_battleEfficiency']
        battle.stats.update(frags=1, spotted=1)
        kind = api['PERSONAL_EFFICIENCY_TYPE']
        api['_EfficiencyListener'].onTotalEfficiencyUpdated({kind.DAMAGE: 1000, kind.ASSIST_DAMAGE: 500, kind.STUN: 100})
        value = wnx.calculate(1000, 1, 1, 600, expected)
        self.assertAlmostEqual(battle.stats['wnx'], value)
        self.assertNotIn('{wnx}', displayed[-1])
        summary = module(vehicle=module(intCD=1), damageDealt=1000, kills=1, spotted=1,
                         damageAssisted=500, damageAssistedStun=100, droppedCapturePoints=0, capturePoints=0)
        reusable = module(common=module(arenaBonusType=bonus, arenaType=module(getGamePlayName=lambda: 'random')),
            vehicles=module(getVehicleSummarizeInfo=lambda *args: summary), getPlayerInfo=lambda: None,
            getPersonalTeamResult=lambda: 1)
        results = module(reusable=reusable, results={'vehicles': {}})
        self.assertEqual(api['make_results_payload'](results)['html'], displayed[-1])
        targets[0] = None
        battle.startBattle()
        self.assertEqual(displayed[-1], '--:#CCCCCC')
        self.assertEqual(api['make_results_payload'](results)['html'], displayed[-1])

    def test_diff_keeps_damage_difference_and_uses_same_ratio_colour_in_battle_and_results(self):
        colors = self.load('common.utils.colorratting')
        formatting = self.load('common.utils.formatting')
        expected = {'level': 8, 'wn8expDamage': 1000.0, 'wn8expSpot': 1, 'wn8expFrag': 1,
                    'wn8expDef': 1, 'wn8expWinRate': 52}
        settings = {'enabled': True, 'colorRatting': 0, 'format': '{diff}:{c:diff} {wn8effd}:{c:wn8effd}',
                    'battleResultsFormat': '{diff}:{c:diff} {wn8effd}:{c:wn8effd}'}
        player = module(arena=module(bonusType=None))
        api, _ = game_source('components/battle_performance.py', {
            'driftkings.common.utils.colorratting': colors,
            'driftkings.core.wnx': self.load('core.wnx'),
            'driftkings.common.utils.formatting': formatting,
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: player, create_range=create_range),
            'driftkings.stats.vehinfo': module(getVehicleInfoData=lambda cd: expected,
                calculateRatingScale=lambda name, value: 0, calculateXTE=lambda cd, damage, frags: 0),
            'driftkings.settings.service': Settings(settings).service(),
            'gui.battle_results.pbs_helpers.common': module(getArenaNameStr=lambda reusable: 'map'),
            'gui.battle_results.settings': module(PLAYER_TEAM_RESULT=module(WIN=1)),
        }, real=('driftkings._constants',))
        bonus = next(iter(api['SUPPORTED_BONUS_TYPES']))
        player.arena.bonusType = bonus
        displayed = []
        api['g_flash'] = module(addText=displayed.append, setVisible=lambda visible: None)
        api['g_calculator'].registerVInfoData(1)
        battle = api['g_battleEfficiency']
        battle.stats['damage'] = 1500
        battle.startBattle()
        colour = colors.getStatisticColor('relativePerformance', 1.5)
        self.assertEqual(displayed[-1], '500:' + colour + ' 1.50:' + colors.getStatisticColor('wn8effd', 1.5))
        summary = module(vehicle=module(intCD=1), damageDealt=1500, spotted=0, kills=0,
                         droppedCapturePoints=0, capturePoints=0)
        reusable = module(common=module(arenaBonusType=bonus, arenaType=module(getGamePlayName=lambda: 'random')),
            vehicles=module(getVehicleSummarizeInfo=lambda *args: summary), getPlayerInfo=lambda: None,
            getPersonalTeamResult=lambda: 1)
        result = api['make_results_payload'](module(reusable=reusable, results={'vehicles': {}}))
        self.assertEqual(result['html'], displayed[-1])
        expected['wn8expDamage'] = 0
        api['g_calculator'].registerVInfoData(1)
        battle.startBattle()
        no_data = '--:' + colors.getRatingPaletteColor('nocolor')
        self.assertTrue(displayed[-1].endswith(no_data))
        result = api['make_results_payload'](module(reusable=reusable, results={'vehicles': {}}))
        self.assertEqual(result['html'], displayed[-1])

    def test_damage_efficiency_is_a_ratio_and_rejects_invalid_expected_damage(self):
        api, _ = game_source('components/battle_performance.py', {
            'driftkings.common.utils.wgutils': module(create_range=create_range, getPlayer=lambda: None)}, real=('driftkings._constants',))
        calculator = api['EfficiencyCalculator']()
        self.assertIsNone(calculator.damage_efficiency(1000))
        calculator.vInfoOK = True
        calculator.expectedValues = {'wn8expDamage': 1000}
        self.assertEqual(calculator.damage_efficiency(1500), 1.5)
        self.assertEqual(calculator.damage_efficiency(0), 0)
        for damage in (None, -1, 'invalid', float('nan'), float('inf')):
            self.assertIsNone(calculator.damage_efficiency(damage))
        for expected in (0, -1, None, float('nan'), float('inf')):
            calculator.expectedValues['wn8expDamage'] = expected
            self.assertIsNone(calculator.damage_efficiency(1000))

    def test_expected_values_below_one_are_not_rounded_up(self):
        expected = {'level': 8, 'wn8expDamage': 1500.0, 'wn8expSpot': 1.2, 'wn8expFrag': 0.9, 'wn8expDef': 0.6, 'wn8expWinRate': 52.0}
        api, _ = game_source('components/battle_performance.py', {
            'driftkings.common.utils.wgutils': module(create_range=create_range, getPlayer=lambda: None),
            'driftkings.stats.vehinfo': module(getVehicleInfoData=lambda cd: expected, calculateRatingScale=lambda name, value: 0,
                                               calculateXTE=lambda cd, damage, frags: 0),
            'driftkings.settings.service': Settings({'enabled': True}).service(),
        }, real=('driftkings._constants',))
        calculator = api['EfficiencyCalculator']()
        calculator.registerVInfoData(1)
        ratios = calculator.calculate_ratios(1500, 1.2, 0.9, 0.6, False)
        self.assertEqual([round(value, 6) for value in ratios[:4]], [1.0, 1.0, 1.0, 1.0])
        expected['wn8expDef'] = 0
        calculator.registerVInfoData(1)
        self.assertEqual(calculator.calculate_ratios(1500, 1, 1, 1, True)[3], 0.0)
