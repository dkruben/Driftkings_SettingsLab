# -*- coding: utf-8 -*-
"""Real control/session logic with narrow import adapters for the game facade."""
import copy
import os
import types
import unittest
try:
    import builtins
except ImportError:
    import __builtin__ as builtins


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIENT = os.path.join(ROOT, 'mod', 'res', 'scripts', 'client', 'driftkings')


def load_source(relative, dependencies):
    original_import = builtins.__import__
    dependencies = dict(dependencies)
    if 'driftkings.common.utils.compat' not in dependencies:
        compat_path = os.path.join(CLIENT, 'common', 'utils', 'compat.py')
        compat = {'__name__': '_compat_test'}
        with open(compat_path, 'rb') as stream:
            exec(compile(stream.read(), compat_path, 'exec'), compat)
        dependencies['driftkings.common.utils.compat'] = types.SimpleNamespace(**{k: v for k, v in compat.items() if not k.startswith('__')})
    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if name in dependencies:
            return dependencies[name]
        return original_import(name, globals, locals, fromlist, level)
    api = dict(vars(builtins))
    api['__import__'] = importing
    path = os.path.join(CLIENT, *relative.split('/'))
    namespace = {'__name__': '_settings_test', '__builtins__': api, '__file__': path}
    with open(path, 'rb') as stream:
        eval(compile(stream.read(), path, 'exec'), namespace)
    return namespace


keycodes = types.ModuleType('keycodes')
keycodes.valid_key_code = load_source('core/keycodes.py', {})['valid_key_code']
controls = load_source('settings/panel/controls.py', {'driftkings.core.keycodes': keycodes})
Control = controls['Control']
panel = types.ModuleType('panel')
panel.logger = types.ModuleType('logger')
panel.logger.warning = lambda *args: None
panel.logger.exception = lambda *args: None
EditSession = load_source('settings/panel/session.py', {'driftkings.settings.panel': panel})['EditSession']


def slider(default=5, minimum=0, maximum=10, step=1):
    control = Control('slider', 'value', default=default)
    control.minimum, control.maximum, control.step = minimum, maximum, step
    return control.finalize()


class ControlValuesTests(unittest.TestCase):
    def test_numeric_values_reject_wrong_types_nonfinite_and_out_of_range(self):
        control = slider()
        for value in (True, '5', None, float('nan'), float('inf'), -1, 11, 1.5):
            self.assertRaises(ValueError, control.validate, value)
        self.assertEqual(control.validate(0), 0)
        self.assertEqual(control.validate(10), 10)

    def test_fractional_slider_keeps_fractional_values(self):
        self.assertEqual(slider(0.5, 0.0, 1.0, 0.1).validate(0.7), 0.7)

    def test_checkbox_requires_a_real_boolean(self):
        control = Control('checkbox', 'enabled', default=True).finalize()
        for value in (0, 1, 'true', None):
            self.assertRaises(ValueError, control.validate, value)
        self.assertIs(control.validate(False), False)

    def test_dropdown_does_not_confuse_booleans_with_numbers(self):
        control = Control('dropdown', 'mode', default=1)
        control.options = [(1, 'One'), (2, 'Two')]
        control.finalize()
        for value in (True, '1', 3):
            self.assertRaises(ValueError, control.validate, value)

    def test_color_validation_normalizes_short_hex(self):
        control = Control('color', 'accent', default='#abc').finalize()
        self.assertEqual(control.default, '#AABBCC')
        self.assertEqual(control.validate('0xff8800'), '#FF8800')
        for value in ('red', '#12345', 0xABCDEF):
            self.assertRaises(ValueError, control.validate, value)

    def test_hotkey_rejects_unknown_codes_and_invalid_groups(self):
        control = Control('hotkey', 'key', default=[]).finalize()
        for value in ([[True]], [[0]], [[327]], [[]], [1], [[1, 2, 3, 4, 5]]):
            self.assertRaises(ValueError, control.validate, value)
        self.assertEqual(control.validate([[1, 2]]), [[1, 2]])

    def test_text_length_and_type_are_checked(self):
        control = Control('text', 'text', default='')
        control.max_length = 3
        control.finalize()
        self.assertEqual(control.validate('abc'), 'abc')
        self.assertRaises(ValueError, control.validate, 'abcd')
        self.assertRaises(ValueError, control.validate, 123)

    def test_multiselect_rejects_duplicates_and_unknown_values(self):
        control = Control('multiselect', 'choices', default=[])
        control.options = [('a', 'A'), ('b', 'B')]
        control.finalize()
        self.assertRaises(ValueError, control.validate, ['a', 'a'])
        self.assertRaises(ValueError, control.validate, ['other'])
        self.assertEqual(control.validate(['b', 'a']), ['b', 'a'])


class Mod(object):
    def __init__(self):
        enabled = Control('checkbox', 'enabled', default=True).finalize()
        value = slider()
        value.depends_on = {'enabled': [True]}
        secret = Control('password', 'secret', default='').finalize()
        self.controls = [enabled, value, secret]
        self.index = dict((control.id, control) for control in self.controls)
        self.values = {'enabled': True, 'value': 5, 'secret': 'existing-secret'}
        self.saved = copy.deepcopy(self.values)

    def value_controls(self):
        return self.controls


class Registry(object):
    def __init__(self):
        self.mods = {'example': Mod()}
        self.missing = False
        self.saves = 0

    def dependency_status(self, mod):
        return [{'installed': False}] if self.missing else []

    def apply_values(self, mod_id, values):
        self.mods[mod_id].values.update(copy.deepcopy(values))
        return values

    def save(self, mod_id):
        self.mods[mod_id].saved = copy.deepcopy(self.mods[mod_id].values)
        self.saves += 1


class SessionValuesTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry()
        self.session = EditSession(self.registry)

    def test_rejected_edit_preserves_live_values_drafts_and_undo_history(self):
        self.session.set('example', 'value', 7)
        before = copy.deepcopy((self.registry.mods['example'].values, self.session.drafts, self.session.history))
        self.assertRaises(ValueError, self.session.set, 'example', 'value', 99)
        self.assertEqual((self.registry.mods['example'].values, self.session.drafts, self.session.history), before)

    def test_cancel_drops_only_changes_not_yet_applied(self):
        self.session.set('example', 'value', 7)
        self.session.apply()
        self.session.set('example', 'value', 8)
        self.session.cancel()
        self.assertEqual(self.session.value('example', 'value'), 7)
        self.assertFalse(self.session.pending_apply())

    def test_dependency_blocks_an_edit_without_changing_the_draft(self):
        self.session.set('example', 'enabled', False)
        before = copy.deepcopy(self.session.drafts)
        self.assertRaises(ValueError, self.session.set, 'example', 'value', 8)
        self.assertEqual(self.session.drafts, before)

    def test_missing_dependency_prevents_apply_and_preserves_pending_changes(self):
        self.session.set('example', 'value', 8)
        self.registry.missing = True
        self.assertRaises(ValueError, self.session.apply)
        self.assertTrue(self.session.pending_apply())
        self.assertEqual(self.registry.mods['example'].values['value'], 5)

    def test_undo_restores_the_previous_edit(self):
        self.session.set('example', 'value', 7)
        self.session.set('example', 'value', 8)
        self.session.undo()
        self.assertEqual(self.session.value('example', 'value'), 7)

    def test_reset_preserves_saved_secrets(self):
        self.session.set('example', 'value', 8)
        self.session.apply()
        self.session.reset('example')
        self.assertEqual(self.session.value('example', 'value'), 5)
        self.assertEqual(self.session.value('example', 'secret'), 'existing-secret')

    def test_save_applies_then_persists_changes(self):
        self.session.set('example', 'value', 8)
        self.session.save()
        self.assertEqual(self.registry.mods['example'].saved['value'], 8)
        self.assertFalse(self.session.unsaved())
        self.assertEqual(self.registry.saves, 1)


if __name__ == '__main__':
    unittest.main()
