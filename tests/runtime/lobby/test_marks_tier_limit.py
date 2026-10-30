# -*- coding: utf-8 -*-
"""Marks of excellence panels appear only from tier 5, in battle and in the hangar."""
from support import RuntimeTest, Settings, game_source, module


class Panel(object):
    def __init__(self):
        self.calls = []

    def setVisible(self, value):
        self.calls.append(('visible', value))

    def unavailable(self, vehicle_id):
        self.calls.append(('unavailable', vehicle_id))


class BattleMarksTierTests(RuntimeTest):
    def setUp(self):
        super(BattleMarksTierTests, self).setUp()
        self.panel = Panel()
        self.tier = 4
        self.api, _ = game_source('battle/battle_marks_of_excellence.py', {
            'driftkings.settings.service': Settings({'enabled': True}).service(),
            'driftkings.settings.sections': module(previous_name=lambda name: 'MarksOnGunBattle'),
            'driftkings.common.config.json_reader': module(loadJson=lambda *args, **kwargs: {}),
            'driftkings.gameface.battle.battle_marks_of_excellence': module(BattleMarksAdapter=lambda: self.panel),
            'driftkings.settings.definitions.battle.battle_marks_of_excellence': module(
                BattleMarksOfExcellenceSettings=lambda: module(NAME='battle_marks_of_excellence')),
            'driftkings.common.utils.wgutils': module(getPlayer=lambda: self.player()),
        }, real=('driftkings._constants', 'driftkings.common.utils.numbers', 'driftkings.core.marks_calculator',
                 'driftkings.common.utils.colorratting'))
        self.worker = self.api['worker']

    def player(self):
        descriptor = module(level=self.tier, name='ussr:R04_T-34', type=module(compactDescr=1))
        vehicle = module(typeDescriptor=descriptor, publicInfo={'marksOnGun': 0})
        return module(databaseID=7, getVehicleAttached=lambda: vehicle)

    def test_tiers_below_five_show_no_panel(self):
        for replay in (False, True):
            self.panel.calls[:] = []
            self.worker.replay = replay
            self.worker.treadStartBattle()
            self.assertFalse(self.worker.level)
            self.assertEqual(self.panel.calls, [('visible', False)], replay)

    def test_eligible_tiers_without_data_report_unavailable(self):
        self.tier = 5
        self.worker.movingAvgDamage = 0
        self.worker.treadStartBattle()
        self.assertTrue(self.worker.level)
        self.assertEqual(self.panel.calls, [('visible', False), ('unavailable', 1)])


class HangarMarksTierTests(RuntimeTest):
    def setUp(self):
        super(HangarMarksTierTests, self).setUp()
        self.current = module(isPresent=lambda: self.current.item is not None, item=None)
        self.api, _ = game_source('lobby/hangar_marks_of_excellence.py', {
            'driftkings.settings.service': Settings({'enabled': True}).service(),
            'CurrentVehicle': module(g_currentVehicle=self.current),
            'driftkings.common.utils.exceptions': module(log_exceptions=lambda function: function),
            'driftkings.interface_catalog': module(gameface_spec=lambda feature: {'resource': 'resource'}),
        }, real=('driftkings._constants', 'driftkings.common.utils.numbers', 'driftkings.core.marks_calculator',
                 'driftkings.common.utils.colorratting'))

    def test_card_needs_a_selected_vehicle_of_tier_five_or_above(self):
        has_tier = self.api['has_marks_tier']
        self.assertFalse(has_tier())
        for tier, expected in ((1, False), (4, False), (5, True), (10, True)):
            self.current.item = module(level=tier)
            self.assertEqual(has_tier(), expected, tier)
        self.assertTrue(has_tier(module(level=8)))

    def test_goal_is_eligible_from_tier_five(self):
        goal = self.api['goal']
        self.assertFalse(goal(70.0, 2000, 4)['eligible'])
        self.assertTrue(goal(70.0, 2000, 5)['eligible'])
