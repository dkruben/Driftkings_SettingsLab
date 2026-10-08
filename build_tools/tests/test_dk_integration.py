import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.settings.panel.api import SettingsAPI
from Driftkings.settings.panel.compatibility import TemplateAdapter
from Driftkings.settings.panel.presenter import Presenter
from Driftkings.settings.panel.profiles import Profiles
from Driftkings.settings.panel.session import EditSession
from Driftkings.settings.panel.sound import SoundManager


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.api = SettingsAPI(self.temp.name)
        self.mod = self.api.register_mod('dk.test')
        self.mod.add_switch('enabled', default=True)
        self.mod.add_color('color', default='#FF0000')
        self.mod.add_hotkey('key', default=[[68]])
        self.mod.add_password('secret')
        self.session = EditSession(self.api.registry)

    def test_apply_persists_cancel_and_dispose_keep_last_apply(self):
        presenter = Presenter(self.api)
        presenter.handle({'action': 'set', 'mod': 'dk.test', 'key': 'enabled', 'value': False})
        presenter.handle({'action': 'apply'})
        saved = json.loads((Path(self.temp.name) / 'test.json').read_text())
        self.assertFalse(saved['enabled'])
        presenter.handle({'action': 'set', 'mod': 'dk.test', 'key': 'enabled', 'value': True})
        presenter.handle({'action': 'cancel'})
        presenter.dispose()
        self.assertFalse(self.mod.get('enabled'))

    def test_profile_roundtrip_excludes_secrets_and_validation_is_atomic(self):
        profiles = Profiles(self.api)
        self.session.set('dk.test', 'secret', 'synthetic-test-value')
        self.session.set('dk.test', 'enabled', False)
        profiles.save('Competitive', self.session)
        exported = profiles.export(self.session)
        self.assertNotIn('secret', exported['mods']['dk.test'])
        self.assertNotIn('synthetic-test-value', json.dumps(exported))
        self.session.cancel()
        profiles.load('Competitive', self.session)
        self.assertFalse(self.session.value('dk.test', 'enabled'))
        before = copy.deepcopy(self.session.drafts)
        exported['mods']['dk.test']['unknown'] = True
        with self.assertRaises(ValueError): profiles.stage(self.session, exported)
        self.assertEqual(self.session.drafts, before)
        profiles.rename('Competitive', 'Streaming')
        self.assertEqual(profiles.names(), ['Streaming'])
        profiles.delete('Streaming')
        self.assertEqual(profiles.names(), [])
        self.assertTrue((Path(self.temp.name) / 'profiles/Streaming.json.bak').is_file())
        for name in ('../escape', 'CON', 'LPT1', 'a/b'):
            with self.assertRaises(ValueError): profiles.save(name, self.session)

    def test_undo_and_hotkey_validation(self):
        self.session.set('dk.test', 'key', [[29, 157], [68]])
        self.session.undo()
        self.assertEqual(self.session.value('dk.test', 'key'), [[68]])
        for value in ([[]], [[0]], [[True]], 'F10'):
            with self.assertRaises(ValueError): self.session.set('dk.test', 'key', value)

    def test_legacy_changes_use_existing_writer_keep_colour_format_and_columns(self):
        legacy = Mock()
        config = Mock(ID='Example', i18n={'UI_description': 'Exemplo'})
        legacy.entries = {'Example': (config, None, {}, None)}
        legacy.describe.return_value = {'title': 'Example', 'values': {'color': 'AABBCC', 'key': [[68]]},
            'defaults': {'color': 'FFFFFF', 'key': [[68]]}, 'controls': [
                {'type': 'ColorChoice', 'varName': 'color', 'text': 'Cor', 'column': 0},
                {'type': 'HotKey', 'varName': 'key', 'text': 'Atalho', 'column': 1}]}
        adapter = TemplateAdapter(self.api, legacy)
        adapter.populate()
        mod = self.api.registry.mods['legacy.Example']
        self.assertEqual([c.column for c in mod.controls], [0, 1])
        session = EditSession(self.api.registry)
        color_id = mod.controls[0].id
        session.set(mod.id, color_id, '#123456')
        self.api.apply_session(session)
        legacy.apply.assert_called_once_with('Example', {'color': '123456', 'key': [[68]]})
        self.assertFalse(list(Path(self.temp.name).glob('*example*')))
        self.assertFalse(session.unsaved())
        legacy.apply.side_effect = IOError('synthetic failure')
        session.set(mod.id, color_id, '#654321')
        with self.assertRaises(IOError): self.api.apply_session(session)
        self.assertEqual(mod.values[color_id], '#123456')
        self.assertTrue(session.pending_apply())
        adapter.dispose()
        config.onPanelClosed.assert_called_once_with()
        self.assertFalse(legacy.isOpen)

    def test_sound_requires_registered_event_and_known_missing_bank_is_rejected(self):
        sound = Mock()
        factory = Mock(return_value=sound)
        manager = SoundManager(factory)
        manager.register('demo', 'demo.bnk', ['demo_event'], loaded=False)
        with self.assertRaises(ValueError): manager.play('demo_event')
        factory.assert_not_called()
        with self.assertRaises(ValueError): manager.play('missing')
        manager.register('demo', 'demo.bnk', ['demo_event'], loaded=True)
        manager.play('demo_event')
        sound.play.assert_called_once_with()
        manager.stop()
        sound.stop.assert_called_once_with()
        with self.assertRaises(ValueError): manager.set_volume('demo', 50)
        factory.return_value = None
        with self.assertRaises(ValueError): manager.play('demo_event')

    def test_missing_dependency_and_version_disable_controls(self):
        dependent = self.api.register_mod('dk.dependent', dependencies=[{'id': 'dk.provider', 'min_version': '2.0.0'}])
        dependent.add_switch('enabled', default=True)
        self.assertEqual(self.session.disabled(dependent.id), ['enabled'])
        with self.assertRaises(ValueError): self.session.set(dependent.id, 'enabled', False)
        provider = self.api.register_mod('dk.provider', version='1.9.0')
        self.assertEqual(self.session.disabled(dependent.id), ['enabled'])
        provider._mod.version = '2.0.0'
        self.assertEqual(self.session.disabled(dependent.id), [])

    def test_preview_button_receives_draft_without_applying(self):
        seen = []
        self.mod.add_button('preview', callback=lambda mod: seen.append(mod.get('color')))
        presenter = Presenter(self.api)
        presenter.handle({'action': 'set', 'mod': 'dk.test', 'key': 'color', 'value': '#123456'})
        presenter.handle({'action': 'button', 'mod': 'dk.test', 'key': 'preview'})
        self.assertEqual(seen, ['#123456'])
        self.assertEqual(self.mod.get('color'), '#FF0000')

    def test_theme_preview_cancel_and_portuguese(self):
        self.api.start('pt_PT')
        presenter = Presenter(self.api)
        self.assertEqual(presenter.schema()['labels']['apply'], 'Aplicar')
        original = presenter.theme()['background']
        presenter.handle({'action': 'set', 'mod': 'dk.settings', 'key': 'theme', 'value': 'custom'})
        presenter.handle({'action': 'set', 'mod': 'dk.settings', 'key': 'background', 'value': '#123456'})
        self.assertEqual(presenter.theme()['background'], '#123456')
        presenter.handle({'action': 'cancel'})
        self.assertEqual(presenter.theme()['background'], original)


if __name__ == '__main__': unittest.main()
