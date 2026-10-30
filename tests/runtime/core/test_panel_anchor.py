# -*- coding: utf-8 -*-
"""Dragged panels keep the anchor chosen by the renderer so resolution changes follow the screen edge."""
from support import RuntimeTest


class PanelAnchorTests(RuntimeTest):
    def setUp(self):
        super(PanelAnchorTests, self).setUp()
        self.moved = self.load('views.marks_model').moved_panel
        self.panel = {'alignX': 'left', 'alignY': 'bottom', 'alpha': 1.0, 'x': 230.0, 'y': -226.0}

    def test_anchor_and_clamped_offsets_are_applied_to_a_copy(self):
        result = self.moved(self.panel, {'x': -99999, 'y': 12, 'alignX': 'right', 'alignY': 'center'})
        self.assertEqual(result, {'alignX': 'right', 'alignY': 'center', 'alpha': 1.0, 'x': -7680, 'y': 12.0})
        self.assertEqual(self.panel['alignX'], 'left')

    def test_missing_or_unknown_anchor_keeps_the_current_one(self):
        result = self.moved(self.panel, {'x': 10, 'y': 20, 'alignX': 'middle'})
        self.assertEqual((result['alignX'], result['alignY']), ('left', 'bottom'))

    def test_invalid_offsets_are_ignored(self):
        for args in (None, [], {'x': 'bad', 'y': 1}, {'x': 1}):
            self.assertIsNone(self.moved(self.panel, args))
