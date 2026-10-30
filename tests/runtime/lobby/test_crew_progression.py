# -*- coding: utf-8 -*-
import itertools

from support import RuntimeTest, module, source


class CrewProgressionTests(RuntimeTest):
    def setUp(self):
        super(CrewProgressionTests, self).setUp()
        self.arithmetic = self.load('core.crew_progression')
        self.collect = source('lobby/crew_progression.py', {
            'driftkings.core.crew_progression': self.arithmetic})['collect_tankman']
        self.presentation = source('views/crew_progression_model.py', {
            'driftkings.views.marks_model': module(number_locale=lambda lang: {'groupSeparator': ' '})})

    def test_remaining_xp_uses_current_skill_completion_not_total_or_one_percent(self):
        calls = []
        def current_skill_cost():
            calls.append('current_skill')
            return 818231
        def wrong_cost():
            self.fail('Total training XP or next-percent XP must not be used as remaining XP')
        tankman = module(invID=1, getFullUserNameWithSkin=lambda: 'Crew', roleUserName='Commander',
                         allSkillsLearned=lambda: False, getNextSkillXpCost=current_skill_cost,
                         getNextLevelXpCost=wrong_cost, descriptor=module(totalXP=wrong_cost),
                         isInTank=True, isMaxRoleLevel=True)
        items = module(getTankmanDossier=lambda identifier: module(getBattlesCount=lambda: 100,
                                                                  getAvgXP=lambda: 1000))
        row = self.collect(tankman, items)
        self.assertEqual(calls, ['current_skill'])
        self.assertEqual(row['remainingXP'], 818231)
        self.assertEqual(row['estimatedBattles'], 819)

    def test_free_xp_and_completed_skill_states(self):
        for completed, cost, expected in ((False, -50, 'ready'), (True, 100, 'complete')):
            tankman = module(invID=1, getFullUserNameWithSkin=lambda: 'Crew', roleUserName='Commander',
                             allSkillsLearned=lambda: completed, getNextSkillXpCost=lambda: cost,
                             isInTank=False, isMaxRoleLevel=True)
            row = self.collect(tankman, module())
            self.assertEqual(row['state'], expected)
            self.assertEqual(row['remainingXP'], 0)
            self.assertEqual(row['estimatedBattles'], 0)

    def test_line_colours_stay_aligned_for_every_visibility_and_state(self):
        strings = dict(('UI_crew_' + key, '{xp}' if key in ('xp', 'roleXP') else
                        '{battles}' if key == 'battles' else key)
                       for key in ('xp', 'roleXP', 'battles', 'noHistory', 'ready', 'complete', 'unavailable'))
        for state, xp, battles in itertools.product(
                ('empty', 'training', 'ready', 'complete', 'unavailable'), (True, False), (True, False)):
            for estimate in (None, 12):
                row = dict(state=state, roleTraining=False, remainingXP=12000, estimatedBattles=estimate)
                settings = dict(showRemainingXP=xp, showEstimatedBattles=battles)
                lines = self.presentation['progression_lines'](row, settings, 'pt', strings)
                kinds = self.presentation['progression_kinds'](row, settings)
                self.assertEqual(len(lines), len(kinds))
                if state == 'training':
                    expected = (['xp'] if xp else []) + (
                        ['battles' if estimate is not None else 'unavailable'] if battles else [])
                    self.assertEqual(kinds, expected)
