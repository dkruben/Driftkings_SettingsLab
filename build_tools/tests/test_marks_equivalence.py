"""Frozen pre-extraction arithmetic versus the pure shared helpers."""
import ast
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core.marks_calculator import ceil_damage, ceil_damage_tens, combined_damage


# Verbatim arithmetic from Worker/MarksOnGunData before substitution. Keep the
# reference independent of the helper; do not replace it with wrapper calls.
def old_units(value):
    return int(math.ceil(value))


def old_tens(value):
    return int(math.ceil(math.ceil(value / 10.0)) * 10)


class MarksEquivalenceTests(unittest.TestCase):
    def test_rounding_equivalence_full_percent_range_and_near_boundaries(self):
        values = [n / 100.0 for n in range(10001)]
        values += [0, 64.99, 65, 84.99, 85, 94.99, 95, 99.99, 100]
        values += [n + offset for n in (0, 65, 85, 95, 100, 2840, 30000) for offset in (-.000001, 0, .000001)]
        for value in values:
            self.assertEqual(ceil_damage(value), old_units(value))
            self.assertEqual(ceil_damage_tens(value), old_tens(value))

    def test_combined_damage_matches_both_original_expressions(self):
        for damage in (0, 1, 2840, 123.5):
            for track, radio, stun in ((0,0,0), (100,50,20), (20,100,50), (20,50,100), (100,100,100)):
                self.assertEqual(combined_damage(damage, track, radio, stun), damage + max(track, radio, stun))
                self.assertEqual(int(combined_damage(damage, track, radio, stun)), int(damage + max(track, radio, stun)))

    def test_combined_preserves_numeric_type_and_tie_order(self):
        for assists in ((100,100.0,0),(100.0,100,0)):
            old=100+max(assists)
            new=combined_damage(100,*assists)
            self.assertEqual(new,old)
            self.assertIs(type(new),type(old))

    def test_helper_has_no_game_imports_or_state(self):
        tree = ast.parse((ROOT / 'source/scripts/client/Driftkings/core/marks_calculator.py').read_text())
        self.assertEqual([n.names[0].name for n in tree.body if isinstance(n, ast.Import)], ['math'])
        self.assertFalse(any(isinstance(n, (ast.ClassDef, ast.ImportFrom)) for n in tree.body))


class MarksPresentationTests(unittest.TestCase):
    def model(self, **changes):
        from Driftkings.views.marks_model import battle_model
        values = dict(current=86.35, estimated=86.43, damage=2500, assist=340, combined=2840,
                      target=3120, target_percent=95, earned_marks=2, targets=(1900,2600,3120))
        values.update(changes)
        return battle_model(**values)

    def test_marks_delta_and_targets(self):
        for marks in range(4):
            self.assertEqual(self.model(earned_marks=marks)['marks'].count('★'), marks)
        self.assertEqual(self.model()['delta']['text'], '▲ +0.08%')
        self.assertEqual(self.model(estimated=86.24)['delta']['text'], '▼ -0.11%')
        self.assertEqual(self.model(estimated=86.35)['delta']['text'], '— 0.00%')
        for damage, state in ((2840,'below'),(3120,'reached'),(3400,'above')):
            self.assertEqual(self.model(combined=damage)['targetState'], state)

    def test_missing_unknown_data_and_percent_boundaries(self):
        self.assertEqual(self.model(unknown=True)['percent'], '--')
        self.assertEqual(self.model(current=None, estimated=None, combined=None)['delta']['direction'], 'unknown')
        self.assertEqual(self.model(target=30000)['target'], '--')
        for percent in (0,64.99,65,84.99,85,94.99,95,99.99,100):
            self.assertEqual(self.model(estimated=percent)['progress'], percent/100)
            self.assertEqual(self.model(estimated=percent)['percent'], '%.2f%%' % percent)

    def test_hangar_goal_semantics_and_retained_awards(self):
        import ast
        namespace = {'math':math, 'THRESHOLDS':(65,85,95)}
        tree=ast.parse((ROOT/'source/scripts/client/Driftkings/lobby/gun_marks.py').read_text(encoding='utf-8'))
        tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('finite','goal')]
        exec(compile(tree,'goal','exec'),namespace)
        goal=namespace['goal']
        for percent, mark in ((0,1),(64.99,1),(65,2),(84.99,2),(85,3),(94.99,3),(95,3),(99.99,3),(100,3)):
            result=goal(percent,2846,8)
            self.assertEqual(result['mark'], mark)
            self.assertEqual(result['achieved'],percent>=95)
        self.assertEqual(goal(64.99,2846,8,earned_marks=3)['mark'],3)
        self.assertTrue(goal(64.99,2846,8,earned_marks=3)['achieved'])
        self.assertIsNone(goal(0,0,8)['estimate'])
        self.assertFalse(goal(95,2846,4)['eligible'])

    def test_modern_payload_does_not_modify_input_and_is_stable(self):
        self.assertEqual(self.model(),self.model())
        from Driftkings.settings.settings_data import defaults
        old = defaults('MarksOnGunBattle')
        self.assertEqual(old['displayMode'],0)
        self.assertIn('{currentMarkOfGun}',old['battleMessage'])
        tree=ast.parse((ROOT/'source/scripts/client/Driftkings/settings/templates/battle/gun_marks.py').read_text())
        preset_assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UIList' for t in n.targets))
        self.assertEqual(len(ast.literal_eval(preset_assignment.value)),12)

    def test_battle_adapter_deduplicates_modern_updates(self):
        from types import SimpleNamespace as NS
        from unittest.mock import Mock
        from Driftkings._constants import MARKS_ON_GUN_BATTLE
        namespace={'ElementType':NS(LABEL='label'),'MARKS_ON_GUN_BATTLE':MARKS_ON_GUN_BATTLE,
                   '_component':lambda:NS(config=NS()),'settings_service':NS(getComponentDict=lambda c:{'displayMode':2,'battleMessageSizeInPercent':100,'background':True})}
        tree=ast.parse((ROOT/'source/scripts/client/Driftkings/views/battle/gun_marks.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Flash')
        node.body=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='set_marks']
        tree.body=[node];exec(compile(tree,'Flash','exec'),namespace)
        adapter=namespace['Flash']();adapter._lastMarks=None;adapter.updateObject=Mock()
        adapter.set_marks(self.model());adapter.set_marks(self.model())
        self.assertEqual(adapter.updateObject.call_count,1)
        adapter.set_marks(self.model(combined=3000))
        self.assertEqual(adapter.updateObject.call_count,2)


    def test_hangar_model_updates_vehicle_without_touching_history_implementation(self):
        from types import SimpleNamespace as NS
        from unittest.mock import Mock
        from Driftkings._constants import MARKS_ON_GUN_HANGAR
        from Driftkings.views.marks_model import delta_model
        data={'vehicleName':'IS-3','tier':8,'damageRating':95.2,'movingAvgDamage':2846,'earnedMarks':3,
              'masteryValue':0,'wn8':0,'wn8Color':'#fff','winRateColor':'#fff','winRate':50,'battles':1}
        namespace={'math':math,'THRESHOLDS':(65,85,95),'unicode':str,'MARKS_ON_GUN_HANGAR':MARKS_ON_GUN_HANGAR,
          'config':NS(i18n={'UI_panel_chooseVehicle':'Tank','UI_panel_selectVehicle':'Choose','UI_panel_mastery0':'--'}),
          'get_view_config':lambda c:{'visible':True},'delta_model':delta_model,
          'g_currentVehicle':NS(isPresent=lambda:True),
          'settings_service':NS(getComponentDict=lambda c:{'goalSelection':0}),
          'g_history':NS(observe=Mock(return_value={'delta':.14,'battles':1}))}
        tree=ast.parse((ROOT/'source/scripts/client/Driftkings/lobby/gun_marks.py').read_text())
        tree.body=[n for n in tree.body if getattr(n,'name',None) in ('finite','goal','MarksOnGunData')]
        exec(compile(tree,'Hangar','exec'),namespace)
        instance=namespace['MarksOnGunData']();instance.collect=lambda:dict(data)
        first=instance.build_panel_model();second=instance.build_panel_model()
        self.assertEqual(first,second)
        self.assertTrue(first['thirdAchieved']);self.assertEqual(first['delta']['text'],'▲ +0.14%')
        data.update(vehicleName='T-34',damageRating=64.99,earnedMarks=0)
        switched=instance.build_panel_model();self.assertEqual(switched['vehicle'],'T-34')
        self.assertFalse(switched['thirdAchieved']);self.assertEqual(switched['displayMarks'],0)
