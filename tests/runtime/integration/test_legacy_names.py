# -*- coding: utf-8 -*-
"""Renaming project symbols must not break existing profiles or integrations."""
from support import RuntimeTest, module


class LegacyNamingTests(RuntimeTest):
    def test_old_and_current_panel_macros_share_values_and_dependencies(self):
        macros = self.load('core.panel_macros').Macros
        issues = self.load('settings.panel_validation').macro_issues
        for available, expected in ((True, 'yes'), (False, 'no')):
            dependencies = set()
            parser = macros({'stat-available': available}, dependencies=dependencies)
            for name in ('stat-available', 'xvm-stat'):
                template = '{{' + name + '?yes|no}}'
                self.assertEqual(parser.render(template), expected)
                self.assertEqual(issues(template, {}), [])
            self.assertEqual(dependencies, set(('stat-available',)))

    def test_old_marker_templates_remain_valid_with_compound_conditions(self):
        validate = self.load('core.vehicle_markers.fields').template
        for name in ('stat-available', 'xvm-stat'):
            validate('{{' + name + '&&hp>0?{{r}}|--}}')

    def test_external_mod_detection_keeps_provider_module_identifiers(self):
        api = self.load('core.mod_compatibility')
        modules = {'xvm_battle': module(owg_module_loaded=lambda: True),
                   'xvm_main.config': module(get=lambda path, default: True)}
        manager = api.CompatibilityManager(modules)
        self.assertEqual(manager.conflict_status('team_panels', 'ExternalMarkers'), api.CONFIRMED_CONFLICT)
        self.assertEqual(manager.warnings_for('team_panels')[0]['integration'], 'ExternalMarkers')
