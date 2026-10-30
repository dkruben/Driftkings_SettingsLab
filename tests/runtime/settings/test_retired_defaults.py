# -*- coding: utf-8 -*-
"""Packaged defaults contain the current settings schema."""
import json
import os

from support import ROOT, RuntimeTest


class RetiredDefaultsTests(RuntimeTest):


    def defaults(self, name):
        with open(os.path.join(ROOT, 'res/configs/driftkings/default', name + '.json'), 'rb') as stream:
            return json.load(stream)


    def test_canonical_defaults_contain_current_options_only(self):
        hangar = self.defaults('hangar_preferences')
        self.assertFalse(set(hangar).intersection(('clockStyle', 'clockSeconds', 'clock24Hour', 'customClockFormat')))
        clock = ('clock', 'clockBackground', 'clockX', 'clockY', 'clockScale', 'customClockText')
        self.assertIn('accountManager', hangar)
        self.assertFalse(set(hangar).intersection(clock))
        main = self.defaults('main')
        self.assertFalse(set(main).intersection(clock[1:]))
        self.assertEqual(sorted(main['clock']), ['enabled', 'formats'])
        self.assertEqual(self.defaults('autoaim_target_indicator'), {'enabled': True, 'color': '#F98600'})
