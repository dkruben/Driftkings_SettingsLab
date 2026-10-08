import importlib.util
from pathlib import Path
import types
import unittest

PATH = Path(__file__).resolve().parents[2] / 'source/scripts/client/Driftkings/settings/registry.py'
spec = importlib.util.spec_from_file_location('native_settings', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeSettingsTests(unittest.TestCase):
    def setUp(self):
        self.saved = []
        self.data = {'enabled': True, 'hpEnabled': True, 'mode': 0, 'toggleKey': [[56, 184]],
                     'textFields': {'custom': {'right': {'text': 'keep'}}}}
        self.config = types.SimpleNamespace(ID='PlayerPanelPro', data=self.data, i18n={},
                                            onApplySettings=self.apply)
        self.registry = module.SettingsRegistry()
        self.registry.register(self.config, {'enabled': 'bool', 'hpEnabled': 'bool', 'mode': 'mode', 'toggleKey': 'hotkey'})

    def apply(self, values):
        self.saved.append(values)
        self.data.update(values)

    def test_apply_preserves_visual_fields_and_defaults(self):
        values = self.registry.describe('PlayerPanelPro')['values']
        values['mode'] = 2
        values['hpEnabled'] = False
        result = self.registry.apply('PlayerPanelPro', values)
        self.assertEqual(result['values']['mode'], 2)
        self.assertEqual(result['defaults']['mode'], 0)
        self.assertEqual(self.data['textFields']['custom']['right']['text'], 'keep')

    def test_mouse_binding_is_accepted_by_legacy_templates(self):
        values = self.registry.describe('PlayerPanelPro')['values']
        values['toggleKey'] = [[29, 157], [259]]
        self.registry.apply('PlayerPanelPro', values)
        self.assertEqual(self.data['toggleKey'], [[29, 157], [259]])

    def test_cancelled_draft_does_not_mutate_settings(self):
        draft = self.registry.describe('PlayerPanelPro')
        draft['values']['toggleKey'][0][0] = 1
        draft['defaults']['mode'] = 2
        self.assertEqual(self.data['toggleKey'], [[56, 184]])
        self.assertEqual(self.registry.describe('PlayerPanelPro')['defaults']['mode'], 0)
        self.assertEqual(self.saved, [])

    def test_invalid_input_never_applies(self):
        for key, value in [('mode', True), ('mode', 3), ('enabled', 1), ('toggleKey', [None]),
                           ('toggleKey', [[0]]), ('toggleKey', [[999]])]:
            values = self.registry.describe('PlayerPanelPro')['values']
            values[key] = value
            with self.assertRaises(ValueError): self.registry.apply('PlayerPanelPro', values)
        with self.assertRaises(ValueError): self.registry.apply('PlayerPanelPro', {'enabled': False})
        self.assertEqual(self.saved, [])


class TemplateSettingsTests(unittest.TestCase):
    def test_template_controls_validation_and_preservation(self):
        data = {'enabled': True, 'count': 2, 'color': 'FF002A', 'choice': 0,
                'text': 'old', 'keys': [56], 'hidden': {'keep': 42}}
        controls = [{'type': 'Slider', 'varName': 'count', 'minimum': 1, 'maximum': 5},
                    {'type': 'ColorChoice', 'varName': 'color'},
                    {'type': 'Dropdown', 'varName': 'choice', 'options': [{'label': 'A'}, {'label': 'B'}]},
                    {'type': 'TextInput', 'varName': 'text'}, {'type': 'HotKey', 'varName': 'keys'}]
        config = types.SimpleNamespace(ID='OtherMod', data=data, i18n={},
            createTemplate=lambda: {'column1': controls}, onApplySettings=data.update)
        registry = module.SettingsRegistry()
        registry.register(config)
        values = registry.describe('OtherMod')['values']
        self.assertEqual(values['keys'], [[56]])
        values.update(count=4, text='new', keys=[[56, 184]])
        registry.apply('OtherMod', values)
        self.assertEqual(data['hidden'], {'keep': 42})
        self.assertEqual(data['text'], 'new')
        for key, value in [('count', 6), ('count', float('nan')), ('color', 'oops'), ('choice', 2)]:
            bad = dict(values, **{key: value})
            with self.assertRaises(ValueError): registry.apply('OtherMod', bad)

    def test_block_callbacks_and_catalog(self):
        blocks = {'a': {'enabled': True}, 'b': {'enabled': False}}
        calls = []
        config = types.SimpleNamespace(ID='Blocks', blockIDs=['a', 'b'], i18n={},
            getData=lambda block: blocks[block], createTemplate=lambda block: {'column1': []},
            onApplySettings=lambda values, blockID: calls.append((blockID, values)))
        registry = module.SettingsRegistry()
        registry.register(config)
        registry.apply('Blocks:b', {'enabled': True})
        self.assertEqual(calls, [('b', {'enabled': True})])
        self.assertEqual(len(registry.catalog()), 2)


class ColumnLayoutTests(unittest.TestCase):
    def test_template_columns_empty_rows_and_order_survive_description(self):
        left = [{'type': 'Empty'}, {'type': 'CheckBox', 'varName': 'a'}]
        right = [{'type': 'Label', 'text': 'Group'}, {'type': 'Dropdown', 'varName': 'b', 'options': [{'label': 'One'}, {'label': 'Two'}]}]
        template = {'column1': left, 'column2': right}
        config = types.SimpleNamespace(ID='Columns', data={'a': True, 'b': 1}, i18n={}, createTemplate=lambda: template)
        registry = module.SettingsRegistry(); registry.register(config)
        result = registry.describe('Columns')
        self.assertEqual([c['column'] for c in result['controls']], [0, 0, 1, 1])
        self.assertEqual([c['type'] for c in result['controls']], ['Empty', 'CheckBox', 'Label', 'Dropdown'])
        self.assertEqual(result['controls'][-1]['options'][1]['label'], 'Two')
        self.assertNotIn('column', left[0])
        self.assertEqual(result['values'], {'a': True, 'b': 1})
