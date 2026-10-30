# -*- coding: utf-8 -*-
"""Every live settings declaration resolves against every bundled language."""
from support.localized_controls import LocalizedControlsFixture

class LocalizedControlTests(LocalizedControlsFixture):
    def test_color_captions_resolve_hash_values_without_duplicate_prefix(self):
        for code, groups in self.documents.items():
            labels = groups['aiming_countdown']
            for key in ('red', 'orange', 'yellow', 'green', 'blue', 'purple'):
                template = labels['UI_setting_' + key + '_text']
                declaration = {'varName': key, 'colorLabelKey': key, 'tooltip': template}
                result = self.schema.resolve(declaration, labels, {key: u'#123456'})
                for name in ('text', 'tooltip'):
                    self.assertNotIn('%(', result[name], (code, key, name))
                    self.assertNotIn('##', result[name], (code, key, name))
                    self.assertIn('#123456', result[name], (code, key, name))

    def test_all_current_controls_have_resolvable_localized_labels(self):
        for code, text in self.documents.items():
            self.text = text
            for definition in self.definitions:
                config = definition()
                for column in config.getControlColumns():
                    for declaration in column:
                        resolved = self.schema.resolve(declaration, config.i18n, config.data)
                        if declaration.get('type') != 'Empty':
                            self.assertTrue(resolved.get('text'), (code, config.NAME, declaration))

    def test_every_control_has_a_description_in_every_language(self):
        missing = []
        for code, text in self.documents.items():
            self.text = text
            if not text.get('common', {}).get('UI_native_enabled_tooltip'):
                missing.append((code, 'common', 'UI_native_enabled_tooltip'))
            for definition in self.definitions:
                config = definition()
                for column in config.getControlColumns():
                    for declaration in column:
                        if declaration.get('type') in ('Empty', 'Label'):
                            continue
                        resolved = self.schema.resolve(declaration, config.i18n, config.data)
                        path = declaration.get('path', [declaration.get('varName')])
                        if not (resolved.get('tooltip') or self.schema.nested_description(path, config.i18n)):
                            missing.append((code, config.NAME, declaration.get('varName')))
        self.assertEqual(missing, [])

    def test_nested_fields_share_descriptions_by_property(self):
        keys = self.schema.description_keys(['carousel', 'normal', 'fields', 'tankName', 'dx'])
        self.assertEqual(keys, ['UI_tooltip_tankName_dx', 'UI_tooltip_fields_dx', 'UI_tooltip_dx'])
        keys = self.schema.description_keys(['loading', 'vehicleIconOffsetXLeft'])
        self.assertEqual(keys[0], 'UI_tooltip_loading_vehicleIconOffsetXLeft')
        self.assertIn('UI_tooltip_vehicleIconOffsetX', keys)
        labels = {'UI_tooltip_extraFields_x': 'Field', 'UI_tooltip_x': 'Generic'}
        self.assertEqual(self.schema.nested_description(['carousel', 'normal', 'extraFields', 3, 'x'], labels), 'Field')
        self.assertEqual(self.schema.nested_description(['minimap', 'x'], labels), 'Generic')
        self.assertEqual(self.schema.nested_description(['unknown'], labels), '')

    def test_current_defaults_open_and_apply_through_every_settings_page(self):
        self.settings_registry()

    def test_carousel_numeric_defaults_and_personal_macros_share_a_valid_control(self):
        registry = self.settings_registry()
        config, defaults = registry.entries['vehicle_carousel']
        key = 'carousel.normal.extraFields.10.alpha'
        macro = '{{v.tfb?100|0}}'
        controls = self.load('settings.panel.controls')
        for saved, default in ((macro, 100), (100, macro)):
            config.data['carousel']['normal']['extraFields'][10]['alpha'] = saved
            defaults['carousel']['normal']['extraFields'][10]['alpha'] = default
            description = registry.describe('vehicle_carousel')
            declaration = next(item for item in description['controls'] if item.get('varName') == key)
            self.assertEqual(declaration['type'], 'TextInput')
            control = controls.Control('text', 'alpha', 'Alpha', default=description['defaults'][key])
            control.finalize()  # This failed with "invalid default (Expected text)" in EU.
            self.assertEqual(control.validate(description['values'][key]), str(saved))
            registry.apply('vehicle_carousel', description['values'])
            self.assertEqual(config.data['carousel']['normal']['extraFields'][10]['alpha'], str(saved))

    def test_distance_choices_and_team_tabs_use_each_selected_language(self):
        for code, text in self.documents.items():
            self.text = text
            for definition in self.definitions:
                if definition.NAME == 'target_distance':
                    config = definition()
                    for position, item in enumerate(config.getControlColumns()[0]):
                        for index, option in enumerate(item.get('options', [])):
                            internal = definition.COLUMNS[0][position]['options'][index]['label']
                            self.assertEqual(option['label'], config.i18n['UI_setting_' + item['varName'] + '_' + internal])
                elif definition.NAME == 'team_panels':
                    config = definition()
                    tabs = set(item.get('tab') for column in config.getControlColumns() for item in column)
                    for key in ('generalTab', 'loadingTab', 'templatesTab'):
                        self.assertIn(config.i18n['UI_panel_' + key], tabs, code)
