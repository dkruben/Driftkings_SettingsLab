# -*- coding: utf-8 -*-
"""Retired settings must not survive load/apply or erase personal preferences."""
import copy
import json
import os

from support import ROOT, RuntimeTest, module, source


class RetiredDefaultsTests(RuntimeTest):
    def test_results_upgrade_only_shipped_template_and_preserve_custom_macros(self):
        defaults = self.defaults('battle_performance')
        api = source('settings/definitions/components/battle_performance.py', {
            'driftkings._constants': self.load('_constants'),
            'driftkings.settings.controls_schema': module(control=None, options=None),
            'driftkings.settings.definitions.base': module(SectionDefinition=object),
            'driftkings.settings.default_values': module(DEFAULTS={'battle_performance': defaults}),
        })
        definition = api['BattlePerformanceSettings']()
        legacy = "<textformat leading='-2' tabstops='[0, 300]'>\t<font color='#FFFFFF' size='15'>{mapName} - {battleType}    WN8:<font color='{c:wn8}'>{wn8}</font>|=|EFF:<font color='{c:eff}'>{eff}</font>|=|Xte:<font color='{c:xte}'>{xte}</font></font></textformat>"
        result = definition.normalize_loaded({'battleResultsFormat': legacy, 'enabled': False})
        self.assertEqual(result, {'battleResultsFormat': defaults['battleResultsFormat'], 'enabled': False})
        self.assertEqual(definition.normalize_loaded(copy.deepcopy(result)), result)
        custom = {'battleResultsFormat': "DIFF: {diff} / <font color='{c:xwn8}'>{xwn8}</font>"}
        self.assertEqual(definition.normalize_loaded(copy.deepcopy(custom)), custom)
        self.assertNotIn('size=', defaults['battleResultsFormat'])
        self.assertNotIn('{mapName}', defaults['battleResultsFormat'])

    def definition(self, relative, name, section):
        schema = source('settings/controls_schema.py', {})
        api = source(relative, {
            'driftkings._constants': self.load('_constants'),
            'driftkings.settings.controls_schema': module(control=schema['control'], slider=schema['slider']),
            'driftkings.settings.definitions.base': module(SectionDefinition=object),
        })
        return api[name]()

    def defaults(self, name):
        with open(os.path.join(ROOT, 'res/configs/driftkings/default', name + '.json'), 'rb') as stream:
            return json.load(stream)

    def test_hangar_drops_retired_and_moved_clock_options_but_keeps_unrelated_settings(self):
        definition = self.definition('settings/definitions/lobby/hangar_preferences.py',
                                     'HangarPreferencesSettings', 'HANGAR_PREFERENCES')
        active = {'enabled': False, 'accountManager': {'enabled': True}, 'personalOption': {'keep': [1, 2]}}
        # The clock moved to the main section; the loader carries these values there.
        legacy = dict(active, clockStyle=4, clockSeconds=True, clock24Hour=False,
                      customClockFormat=False, text='old', panel={'x': 999},
                      clock=True, clockBackground=True, clockScale=125, clockX=-456, clockY=123,
                      customClockText=u'<font>%I:%M %p — %A</font>')
        for normalize in (definition.normalize_loaded, lambda values: definition.normalize_changes(values, {})):
            values = normalize(copy.deepcopy(legacy))
            self.assertEqual(values, active)
            self.assertEqual(normalize(copy.deepcopy(values)), active)

    def test_native_target_box_preserves_enabled_and_removes_acquisition_options(self):
        definition = self.definition('settings/definitions/battle/autoaim_target_indicator.py',
                                     'AutoaimTargetIndicatorSettings', 'AUTOAIM_TARGET_INDICATOR')
        for enabled in (False, True):
            active = {'enabled': enabled, 'personalOption': 'keep'}
            legacy = dict(active, angle=1.3, catchHiddenTarget=True, disableArtyMode=True)
            self.assertEqual(definition.normalize_loaded(copy.deepcopy(legacy)), active)
            self.assertEqual(definition.normalize_changes(copy.deepcopy(legacy), {}), active)
            self.assertEqual(definition.getControlColumns()[0][0]['varName'], 'color')

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
