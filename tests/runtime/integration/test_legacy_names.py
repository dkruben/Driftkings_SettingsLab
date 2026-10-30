# -*- coding: utf-8 -*-
"""Current macro names work; retired names are reported, and integrations keep provider identifiers."""
from support import RuntimeTest, module


class LegacyNamingTests(RuntimeTest):
    def test_panel_macro_uses_the_current_name_and_reports_the_retired_one(self):
        macros = self.load('core.panel_macros').Macros
        issues = self.load('settings.panel_validation').macro_issues
        for available, expected in ((True, 'yes'), (False, 'no')):
            dependencies = set()
            parser = macros({'stat-available': available}, dependencies=dependencies)
            self.assertEqual(parser.render('{{stat-available?yes|no}}'), expected)
            self.assertEqual(issues('{{stat-available?yes|no}}', {}), [])
            self.assertEqual(dependencies, set(('stat-available',)))
        self.assertEqual(issues('{{xvm-stat?yes|no}}', {}), ['Unknown macro: xvm-stat'])

    def test_marker_templates_accept_only_the_current_macro(self):
        validate = self.load('core.vehicle_markers.fields').template
        validate('{{stat-available&&hp>0?{{r}}|--}}')
        with self.assertRaises(ValueError):
            validate('{{xvm-stat&&hp>0?{{r}}|--}}')

    def test_external_mod_detection_keeps_provider_module_identifiers(self):
        api = self.load('core.mod_compatibility')
        modules = {'xvm_battle': module(owg_module_loaded=lambda: True),
                   'xvm_main.config': module(get=lambda path, default: True)}
        manager = api.CompatibilityManager(modules)
        self.assertEqual(manager.conflict_status('team_panels', 'ExternalMarkers'), api.CONFIRMED_CONFLICT)
        self.assertEqual(manager.warnings_for('team_panels')[0]['integration'], 'ExternalMarkers')
