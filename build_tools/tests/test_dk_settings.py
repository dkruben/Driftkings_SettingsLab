# -*- coding: utf-8 -*-
"""DK Mod Settings core: registry, persistence, session and presenter (Python 2.7 and 3)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

CLIENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'source', 'scripts', 'client')
if CLIENT not in sys.path:
    sys.path.insert(0, CLIENT)

from Driftkings.settings.panel.api import SettingsAPI  # noqa: E402
from Driftkings.settings.panel.controls import DefinitionError  # noqa: E402
from Driftkings.settings.panel.presenter import Presenter  # noqa: E402
from Driftkings.settings.panel.registry import DuplicateModError, STATUS_CONFIG_ERROR, STATUS_ERROR  # noqa: E402
from Driftkings.settings.panel.session import SaveError  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.api = SettingsAPI(self.root)

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, name, document, raw=None):
        with open(os.path.join(self.root, name + '.json'), 'wb') as stream:
            stream.write(raw if raw is not None else json.dumps(document).encode('utf-8'))

    def read(self, name, folder=None):
        path = os.path.join(self.root, folder, name + '.json') if folder else os.path.join(self.root, name + '.json')
        with open(path, 'rb') as stream:
            return json.loads(stream.read().decode('utf-8'))

    def demo(self, mod_id='dk.demo'):
        mod = self.api.register_mod(id=mod_id, name='Demo', version='1.0.0', author='DK')
        mod.add_switch(id='enabled', label='Enable', default=True)
        mod.add_dropdown(id='lang', label='Language', values=[('en', 'English'), ('pt', u'Português')], default='en',
                         depends_on={'enabled': True})
        mod.add_slider(id='volume', label='Volume', min_value=0, max_value=100, default=80)
        mod.add_text(id='name', label='Name', default=u'abc')
        mod.add_color(id='accent', label='Accent', default='#d98219')
        mod.add_password(id='apiKey', label='API key')
        return mod


class RegistryTests(Base):
    def test_defaults_without_file(self):
        mod = self.demo()
        self.assertEqual(mod.values, {'enabled': True, 'lang': 'en', 'volume': 80, 'name': u'abc',
                                      'accent': '#D98219', 'apiKey': u''})

    def test_load_existing_config_and_reject_invalid_values(self):
        self.write('demo', {'enabled': False, 'lang': 'pt', 'volume': 500, 'accent': 'nope', 'custom': [1, 2]})
        mod = self.demo()
        self.assertEqual(mod.get('enabled'), False)
        self.assertEqual(mod.get('lang'), 'pt')
        self.assertEqual(mod.get('volume'), 80)
        self.assertEqual(mod.get('accent'), '#D98219')

    def test_corrupt_config_uses_defaults_preserves_file_and_backs_it_up_on_save(self):
        self.write('demo', None, raw=b'{ broken')
        mod = self.demo()
        definition = self.api.registry.mods['dk.demo']
        self.assertEqual(definition.status, STATUS_CONFIG_ERROR)
        self.assertEqual(mod.get('enabled'), True)
        with open(os.path.join(self.root, 'demo.json'), 'rb') as stream:
            self.assertEqual(stream.read(), b'{ broken')
        self.api.registry.save('dk.demo')
        with open(os.path.join(self.root, 'demo.json.bak'), 'rb') as stream:
            self.assertEqual(stream.read(), b'{ broken')
        self.assertEqual(self.read('demo')['volume'], 80)
        self.assertNotEqual(definition.status, STATUS_CONFIG_ERROR)

    def test_save_keeps_unknown_keys_and_separates_secrets(self):
        self.write('demo', {'futureOption': {'x': 1}})
        self.demo()
        self.api.registry.apply_values('dk.demo', {'apiKey': u'top-secret', 'volume': 40})
        self.api.registry.save('dk.demo')
        public = self.read('demo')
        self.assertEqual(public['futureOption'], {'x': 1})
        self.assertEqual(public['volume'], 40)
        self.assertNotIn('apiKey', public)
        self.assertEqual(self.read('demo', 'secrets'), {'apiKey': u'top-secret'})
        reloaded = SettingsAPI(self.root)
        self.assertEqual(reloaded.register_mod('dk.demo').add_password('apiKey').get('apiKey'), u'top-secret')

    def test_backups_are_bounded(self):
        self.demo()
        for volume in range(1, 7):
            self.api.registry.apply_values('dk.demo', {'volume': volume})
            self.api.registry.save('dk.demo')
        backups = self.api.registry.store.backups('demo')
        self.assertEqual(len(backups), 3)
        with open(backups[0], 'rb') as stream:
            self.assertEqual(json.loads(stream.read().decode('utf-8'))['volume'], 5)

    def test_duplicate_mod_and_config_file(self):
        self.demo()
        self.assertRaises(DuplicateModError, self.api.register_mod, 'dk.demo')
        self.assertRaises(DuplicateModError, self.api.register_mod, 'other', config_file='demo')

    def test_invalid_declarations_are_reported_to_the_author(self):
        mod = self.api.register_mod('dk.bad')
        self.assertRaises(DefinitionError, mod.add_switch, id='1bad')
        self.assertRaises(DefinitionError, mod.add_switch, id='flag', default='yes')
        self.assertRaises(DefinitionError, mod.add_slider, id='s', min_value=10, max_value=1)
        self.assertRaises(DefinitionError, mod.add_switch, id='child', depends_on={'missing': True})
        self.assertRaises(DefinitionError, mod.add_switch, id='flag2', colour=True)
        mod.add_switch(id='flag')
        self.assertRaises(DefinitionError, mod.add_switch, id='flag')
        self.assertRaises(DefinitionError, self.api.register_mod, 'bad id!')

    def test_module_level_shortcuts(self):
        self.api.register_mod(mod_id='dk.autotranslator', name='Auto Translator')
        self.api.add_switch(mod_id='dk.autotranslator', setting_id='enabled', label='Enable mod', default=True)
        self.api.add_dropdown(mod_id='dk.autotranslator', setting_id='target_language', label='Target',
                              values=[('en', 'English'), ('pt', u'Português')], default='en')
        self.assertEqual(self.api.get('dk.autotranslator', 'target_language'), 'en')
        self.assertEqual(self.api.registry.mods['dk.autotranslator'].file_name, 'autotranslator')

    def test_colors_and_numbers_are_normalized(self):
        mod = self.api.register_mod('dk.c')
        mod.add_color(id='c', default='#abc')
        mod.add_slider(id='f', min_value=0.0, max_value=1.0, step=0.05, default=0.5)
        control = self.api.registry.mods['dk.c'].index
        self.assertEqual(mod.get('c'), '#AABBCC')
        self.assertEqual(control['c'].validate('0xff8800'), '#FF8800')
        self.assertRaises(ValueError, control['c'].validate, '#GG0000')
        self.assertRaises(ValueError, control['f'].validate, float('nan'))
        self.assertRaises(ValueError, control['f'].validate, True)

    def test_failing_listener_marks_mod_but_others_still_run(self):
        mod = self.demo()
        calls = []
        mod.on_change(lambda changes: 1 / 0)
        mod.on_change(lambda changes: calls.append(changes))
        self.api.registry.apply_values('dk.demo', {'volume': 10})
        self.assertEqual(calls, [{'volume': 10}])
        self.assertEqual(self.api.registry.mods['dk.demo'].status, STATUS_ERROR)


class SessionTests(Base):
    def setUp(self):
        Base.setUp(self)
        self.mod = self.demo()
        self.changes = []
        self.mod.on_change(self.changes.append)
        self.presenter = Presenter(self.api)
        self.session = self.presenter.session

    def test_apply_cancel_save(self):
        self.session.set('dk.demo', 'volume', 30)
        self.assertEqual(self.mod.get('volume'), 80)
        self.assertTrue(self.session.pending_apply())
        self.session.cancel()
        self.assertEqual(self.session.value('dk.demo', 'volume'), 80)
        self.session.set('dk.demo', 'volume', 30)
        self.session.apply()
        self.assertEqual(self.mod.get('volume'), 30)
        self.assertEqual(self.changes, [{'volume': 30}])
        self.assertTrue(self.session.unsaved())
        self.assertFalse(os.path.exists(os.path.join(self.root, 'demo.json')))
        self.session.save()
        self.assertFalse(self.session.unsaved())
        self.assertEqual(self.read('demo')['volume'], 30)

    def test_setting_back_to_applied_value_clears_the_draft(self):
        self.session.set('dk.demo', 'volume', 30)
        self.session.set('dk.demo', 'volume', 80)
        self.assertFalse(self.session.pending_apply())

    def test_discard_reverts_applied_values(self):
        self.session.set('dk.demo', 'volume', 30)
        self.session.apply()
        self.session.discard()
        self.assertEqual(self.mod.get('volume'), 80)
        self.assertEqual(self.changes, [{'volume': 30}, {'volume': 80}])

    def test_reset_restores_defaults_but_keeps_secrets(self):
        self.api.registry.apply_values('dk.demo', {'volume': 5, 'apiKey': u'k'})
        self.session.reset('dk.demo')
        self.assertEqual(self.session.value('dk.demo', 'volume'), 80)
        self.assertEqual(self.session.value('dk.demo', 'apiKey'), u'k')

    def test_dependencies_disable_and_block_changes(self):
        self.assertEqual(self.session.disabled('dk.demo'), [])
        self.session.set('dk.demo', 'enabled', False)
        self.assertEqual(self.session.disabled('dk.demo'), ['lang'])
        self.assertRaises(ValueError, self.session.set, 'dk.demo', 'lang', 'pt')

    def test_unknown_setting_and_invalid_value(self):
        self.assertRaises(ValueError, self.session.set, 'dk.demo', 'nope', 1)
        self.assertRaises(ValueError, self.session.set, 'dk.demo', 'lang', 'xx')
        self.assertRaises(ValueError, self.session.set, 'dk.demo', 'volume', 101)

    def test_save_failure_is_reported(self):
        self.session.set('dk.demo', 'volume', 1)
        def broken(*args, **kwargs):
            raise IOError('disk full')
        self.api.registry.store.write = broken
        self.assertRaises(SaveError, self.session.save)


class PresenterTests(Base):
    def setUp(self):
        Base.setUp(self)
        self.api.start('pt_BR')
        self.mod = self.demo()
        self.presenter = Presenter(self.api)

    def act(self, **data):
        return self.presenter.handle(data)

    def test_schema_lists_mods_and_controls_in_client_language(self):
        schema = self.presenter.schema()
        self.assertEqual(self.api.language, 'pt')
        ids = [mod['id'] for mod in schema['mods']]
        self.assertEqual(ids[0], 'dk.settings')
        self.assertNotIn('dk.autotranslator', ids)
        self.assertNotIn('dk.sounddemo', ids)
        demo = [mod for mod in schema['mods'] if mod['id'] == 'dk.demo'][0]
        self.assertEqual([c['type'] for c in demo['controls']],
                         ['switch', 'dropdown', 'slider', 'text', 'color', 'password'])
        self.assertEqual(schema['labels']['apply'], u'Aplicar')
        json.dumps(schema)

    def test_secrets_never_reach_the_view(self):
        self.act(action='set', mod='dk.demo', key='apiKey', value=u'super-secret')
        state = self.presenter.state()
        self.assertEqual(state['values']['dk.demo']['apiKey'], u'')
        self.assertEqual(state['secrets'], {'dk.demo': ['apiKey']})
        self.assertNotIn('super-secret', json.dumps([state, self.presenter.schema()]))

    def test_actions_and_close_confirmation(self):
        self.act(action='select', mod='dk.demo')
        self.assertEqual(self.presenter.state()['selected'], 'dk.demo')
        self.act(action='set', mod='dk.demo', key='volume', value=55)
        state = self.presenter.state()
        self.assertTrue(state['pending'])
        self.assertEqual(state['changed']['dk.demo'], ['volume'])
        self.assertEqual(self.act(action='close'), {'close': False})
        self.assertTrue(self.presenter.state()['confirm'])
        self.act(action='confirm', choice='stay')
        self.assertFalse(self.presenter.state()['confirm'])
        self.act(action='close')
        self.assertTrue(self.act(action='confirm', choice='discard')['close'])
        self.assertEqual(self.mod.get('volume'), 80)

    def test_save_and_apply_persists_and_closes(self):
        self.act(action='set', mod='dk.demo', key='name', value=u'Olá')
        self.assertTrue(self.act(action='save')['close'])
        self.assertEqual(self.read('demo')['name'], u'Olá')
        self.assertEqual(self.act(action='close'), {'close': True})

    def test_bad_requests_never_raise(self):
        for data in (None, [], {}, {'action': 'explode'}, {'action': 'set', 'mod': 'missing'},
                     {'action': 'set', 'mod': 'dk.demo', 'key': 'volume'},
                     {'action': 'set', 'mod': 'dk.demo', 'key': 'volume', 'value': 'loud'},
                     {'action': 'confirm', 'choice': 'maybe'}, {'action': '__init__'}):
            self.presenter.handle(data)
        self.assertEqual(self.mod.get('volume'), 80)

    def test_button_callback_message_and_failure(self):
        self.mod.add_button(id='ok', label='Ok', callback=lambda handle: u'done %d' % handle.get('volume'))
        self.mod.add_button(id='fail', label='Fail', callback=lambda handle: 1 / 0)
        self.act(action='button', mod='dk.demo', key='ok')
        self.assertEqual(self.presenter.state()['message']['text'], u'done 80')
        self.act(action='button', mod='dk.demo', key='fail')
        self.assertEqual(self.presenter.state()['message']['kind'], 'error')

    def test_language_and_accent_preview(self):
        self.act(action='set', mod='dk.settings', key='accent', value='#3d8fd9')
        self.assertEqual(self.presenter.state()['theme']['accent'], '#3D8FD9')
        self.act(action='set', mod='dk.settings', key='language', value='en')
        self.act(action='apply')
        self.assertEqual(self.presenter.schema()['labels']['apply'], u'Apply')

    def test_external_close_discards_unsaved_edits(self):
        self.act(action='set', mod='dk.demo', key='volume', value=1)
        self.act(action='apply')
        self.act(action='set', mod='dk.demo', key='volume', value=2)
        self.presenter.dispose()
        self.assertEqual(self.mod.get('volume'), 1)

    def test_example_pages_stay_disabled_with_previous_setting(self):
        self.write('dk_settings', {'examples': True})
        api = SettingsAPI(self.root)
        api.start('en')
        self.assertNotIn('dk.autotranslator', api.registry.mods)
        self.assertNotIn('dk.sounddemo', api.registry.mods)
        controls = api.mod('dk.settings')._mod.controls
        self.assertNotIn('examples', [control.id for control in controls])


if __name__ == '__main__':
    unittest.main()
