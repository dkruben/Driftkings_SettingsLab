# -*- coding: utf-8 -*-
"""Team statistics: shell choice, magazine reload, team totals and the win chance."""
from support import RuntimeTest, Settings, game_source, module

AP, APCR, HEAT, HE = 'ARMOR_PIERCING', 'ARMOR_PIERCING_CR', 'HOLLOW_CHARGE', 'HIGH_EXPLOSIVE'
CLASSES = frozenset(('lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG'))


def shot(kind, damage, armor=False):
    shell = module(kind=kind, armorDamage=(damage, damage)) if armor else module(kind=kind, damage=(damage, damage))
    return module(shell=shell)


def tank(team, tag='heavyTank', hp=1000, reload=10.0, shots=None, clip=(1, 0), alive=True, name='Tank'):
    vehicle_type = module(type=module(compactDescr=1, shortUserString=name, tags=frozenset((tag, 'premium'))),
                          level=8, maxHealth=hp,
                          gun=module(reloadTime=reload, clip=clip, shots=shots or [shot(AP, 300)]))
    return {'vehicleType': vehicle_type, 'accountDBID': 1, 'name': 'player', 'team': team, 'isAlive': alive}


class BattleStatisticsTests(RuntimeTest):
    def setUp(self):
        super(BattleStatisticsTests, self).setUp()
        self.data = {'enabled': True, 'format': '{allyChance}{compareSign}{enemyChance}', 'colorRating': 0}
        self.events = []
        self.vehicles = {}
        self.player = module(team=1, arena=module(vehicles=self.vehicles))
        record = lambda name: (lambda *args: self.events.append((name,) + args))
        self.api, self.hooks = game_source('battle/battle_statistics.py', {
            'driftkings.settings.service': Settings(self.data).service(),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: self.player, getEntity=lambda vehicleID: None),
            'driftkings.game_constants': module(SHELL_TYPES=module(ARMOR_PIERCING=AP, ARMOR_PIERCING_CR=APCR,
                                                                    HOLLOW_CHARGE=HEAT, HIGH_EXPLOSIVE=HE)),
            'items': module(vehicles=module(VEHICLE_CLASS_TAGS=CLASSES)),
            'driftkings.core.battle_policy': module(battle_policy=module(decision=lambda name: (True, ''))),
            'driftkings.ui': module(g_events=module(onVehiclesChanged=record('vehicles'), onCountChanged=record('count'),
                                                   onHealthChanged=record('health'), onChanceChanged=record('chance'))),
        }, real=('driftkings._constants', 'driftkings.common.utils.formatting', 'driftkings.common.utils.colorratting'))
        self.stats = self.api['g_tanksStatistic']
        self.display = self.api['g_mod']

    def add(self, vehicle_id, info):
        self.vehicles[vehicle_id] = info
        return self.stats.addVehicleInfo(vehicle_id, info)

    def test_best_regular_shell_and_its_dpm_are_used(self):
        self.add(1, tank(1, shots=[shot(APCR, 400), shot(AP, 300), shot(HE, 500)]))
        gun = self.stats.base[1]['gun']
        self.assertEqual(gun['currentShell'], 'AP')
        self.assertEqual((gun['currentDamage'], gun['currentDpm']), (300.0, 1800.0))
        # High explosive counts half its damage, but keeps the full value per minute.
        self.assertEqual((gun['shell']['HE']['damage'], gun['shell']['HE']['dpm']), (250.0, 3000.0))
        self.add(2, tank(2, shots=[shot(HEAT, 360, armor=True)]))
        self.assertEqual(self.stats.base[2]['gun']['currentShell'], 'HC')
        self.add(3, tank(2, tag='SPG', shots=[shot(AP, 300), shot(HE, 800)]))
        self.assertEqual(self.stats.base[3]['gun']['currentShell'], 'HE')
        self.assertEqual(self.stats.base[3]['gun']['currentDamage'], 400.0)

    def test_magazine_reload_is_spread_over_its_shells(self):
        self.add(1, tank(1, reload=20.0, clip=(4, 2.0), shots=[shot(AP, 210)]))
        gun = self.stats.base[1]['gun']
        self.assertEqual(gun['ammer'], {'reload': 20.0, 'capacity': 4, 'shellReload': 2.0})
        self.assertEqual(gun['reload'], 7.0)
        self.assertEqual(gun['currentDpm'], 1800.0)

    def test_incomplete_or_repeated_vehicles_are_not_added(self):
        self.assertFalse(self.stats.addVehicleInfo(1, None))
        self.assertFalse(self.stats.addVehicleInfo(1, {'vehicleType': None}))
        self.assertTrue(self.add(1, tank(1)))
        self.assertFalse(self.add(1, tank(1)))
        self.player = None
        self.assertFalse(self.stats.addVehicleInfo(2, tank(2)))

    def test_equal_teams_have_equal_chances_and_totals(self):
        self.add(1, tank(1))
        self.add(2, tank(2))
        self.assertEqual((self.stats.allyTanksCount, self.stats.enemyTanksCount), (1, 1))
        self.assertEqual((self.stats.allyTeamHP, self.stats.enemyTeamHP), (1000, 1000))
        self.assertAlmostEqual(self.stats.allyChance, 50.0)
        self.assertAlmostEqual(self.stats.enemyChance, 50.0)
        self.assertEqual(self.events[-1][0], 'chance')

    def test_battle_health_updates_move_the_chance(self):
        self.vehicles.update({1: tank(1), 2: tank(2), 3: tank(2, hp=500)})
        self.display.onBattleStarted()
        self.assertEqual(sorted(self.stats.base), [1, 2, 3])
        self.assertLess(self.stats.allyChance, self.stats.enemyChance)
        self.display.onHealthChanged(2, 400)
        self.assertEqual(self.stats.enemyTeamHP, 900)
        self.display.onKilled(2)
        self.display.onKilled(3)
        self.assertEqual((self.stats.enemyTanksCount, self.stats.enemyTeamHP), (0, 0))
        self.assertAlmostEqual(self.stats.allyChance, 100.0)
        # A vehicle first seen through its health is added before the update.
        self.vehicles[4] = tank(2)
        self.display.onHealthChanged(4, 700)
        self.assertEqual(self.stats.base[4]['hp'], 700)
        self.display.onBattleEnded()
        self.assertEqual(self.stats.base, {})
        self.display.onHealthChanged(1, 10)
        self.assertEqual(self.stats.base, {})

    def test_comparison_sign_and_text_macros(self):
        sign = self.display.compare_sign
        self.assertEqual((sign(1, 2), sign(2, 1), sign(1, 1)), ('&#x003C;', '&#x003E;', '&#x007C;'))
        self.assertEqual(self.display.formatText('A', 'B', 60, 40), 'A&#x003E;B')
