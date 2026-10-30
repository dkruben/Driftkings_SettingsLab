# -*- coding: utf-8 -*-
"""Pure layout tests; run on Python 2.7 and 3 without importing the game."""
import os
import runpy
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SOURCE = os.path.join(ROOT, 'mod', 'res', 'scripts', 'client', 'driftkings',
                      'settings', 'panel', 'layout.py')
namespace = runpy.run_path(SOURCE)
balance_columns = namespace['balance_columns']


class Control(object):
    def __init__(self, column=-1, preview=None, visible=True, kind='checkbox', tab=None):
        self.column = column
        self.preview = preview
        self.visible = visible
        self.type = kind
        self.tab = tab


class BalanceColumnsTests(unittest.TestCase):
    def columns(self, controls):
        balance_columns(controls)
        return [control.column for control in controls]

    def test_small_groups_use_one_column(self):
        for count in (1, 2, 3):
            self.assertEqual(self.columns([Control() for _ in range(count)]), [0] * count)

    def test_four_controls_still_split_evenly(self):
        self.assertEqual(self.columns([Control() for _ in range(4)]), [0, 0, 1, 1])

    def test_medium_groups_remain_balanced(self):
        self.assertEqual(self.columns([Control() for _ in range(6)]), [0, 0, 0, 1, 1, 1])

    def test_explicit_pairs_keep_their_columns_even_for_small_groups(self):
        self.assertEqual(self.columns([Control(0), Control(0), Control(1)]), [0, 0, 1])

    def test_preview_retains_weight_of_three(self):
        self.assertEqual(self.columns([Control(preview={'kind': 'image'}), Control()]), [0, 1])
        self.assertEqual(self.columns([Control(preview={'kind': 'audio'})]), [0])

    def test_sections_and_tabs_balance_independently(self):
        controls = ([Control() for _ in range(3)] + [Control(kind='section')] +
                    [Control(tab='first') for _ in range(3)] +
                    [Control(tab='second') for _ in range(3)])
        self.assertEqual(self.columns(controls), [0, 0, 0, -1, 0, 0, 0, 0, 0, 0])

    def test_hidden_controls_do_not_create_a_pair(self):
        self.assertEqual(self.columns([Control(0), Control(1, visible=False), Control()]), [0, 1, 0])

    def test_balancing_is_stable_when_called_again(self):
        controls = [Control() for _ in range(6)]
        first = self.columns(controls)
        self.assertEqual(self.columns(controls), first)


if __name__ == '__main__':
    unittest.main()
