# -*- coding: utf-8 -*-
"""Engine-free constants and tuple contracts used by existing callers."""
import unittest
from support import RuntimeTest, module, source


class ConstantsTests(RuntimeTest):
    def test_constants_import_without_game_and_share_mark_limits(self):
        constants = self.load('_constants')
        marks = self.load('core.marks_calculator')
        colors = self.load('common.utils.color_rating_data')
        self.assertIs(marks.MARK_LEVELS, constants.MARK_LEVELS)
        self.assertIs(colors.MOE_LEVELS, constants.MARK_LEVELS)
        self.assertIs(marks.THRESHOLDS, constants.MARK_THRESHOLDS)
        self.assertEqual(constants.THIRD_PERSON_ZOOM.MODES, ('arcade', 'postmortem', 'strategic', 'arty'))

    def test_named_records_preserve_tuple_shape_and_are_immutable(self):
        constants = self.load('_constants')
        bounds = constants.ScreenBounds(1, 2, 3, 4)
        self.assertEqual(bounds, (1, 2, 3, 4))
        self.assertEqual(bounds.width, 3)
        with self.assertRaises(AttributeError):
            bounds.width = 10
        marks = self.load('core.marks_calculator')
        stats = marks.statistics(65, 100)
        self.assertIsInstance(stats, constants.MarksStatistics)
        self.assertEqual(len(stats), 9)
        self.assertEqual(stats.next_percent, stats[0])
        self.assertEqual(stats.damage95, stats[7])
        curve = marks.battle_curve([60, 90, 65, 100], 65, 100)
        self.assertIsInstance(curve, constants.BattleCurve)
        self.assertEqual(len(curve), 6)
        self.assertEqual(curve.target_damage, curve[3])
        self.assertEqual(curve.statistics, stats)

    def test_service_spec_preserves_defaults_and_normalizes_dependencies(self):
        api = source('core/__init__.py', {})
        spec = api['ServiceSpec']('test', object, ['common'])
        self.assertEqual(spec.requires, ('common',))
        self.assertEqual(spec.phase, 'foundation')
        self.assertEqual(api['ServiceSpec']('test', object).requires, ())
        with self.assertRaises(AttributeError):
            spec.phase = 'other'

    def test_panel_modes_and_roman_legacy_ranges_keep_their_values(self):
        constants = self.load('_constants')
        adapters = self.load('core.mode_adapters')
        panel = self.load('core.panel_model')
        data = self.load('settings.settings_data')
        self.assertIs(adapters.CLASSIC_PANEL_MODES, constants.TEAM_PANELS.MODES)
        self.assertIs(data.PROFILES, constants.TEAM_PANELS.MODES)
        self.assertEqual(data.PROFILES, ('none', 'short', 'medium', 'medium2', 'large'))
        self.assertEqual(panel.ROMAN, ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'))
        self.assertEqual(constants.ROMAN_NUMERALS[-1], 'XII')

    def test_native_enum_reexports_preserve_identity_and_feedback_groups(self):
        control, marker, shot, period = object(), object(), object(), object()
        events = module(RADIO_ASSIST=1, TRACK_ASSIST=2, STUN_ASSIST=3, DAMAGE=4, TANKING=5, RECEIVED_DAMAGE=6)
        api = source('game_constants.py', {
            'aih_constants': module(CTRL_MODE_NAME=control, GUN_MARKER_TYPE=marker, SHOT_RESULT=shot),
            'BattleFeedbackCommon': module(BATTLE_EVENT_TYPE=events),
            'constants': module(ARENA_PERIOD=period, SHELL_MECHANICS_TYPE=object(), SHELL_TYPES=object())})
        self.assertIs(api['CTRL_MODE_NAME'], control)
        self.assertIs(api['GUN_MARKER_TYPE'], marker)
        self.assertIs(api['SHOT_RESULT'], shot)
        self.assertIs(api['ARENA_PERIOD'], period)
        self.assertEqual(api['ASSIST_EVENTS'], (1, 2, 3))
        self.assertEqual(api['DAMAGE_EVENTS'], frozenset((1, 2, 3, 4, 5, 6)))


if __name__ == '__main__':
    unittest.main()
