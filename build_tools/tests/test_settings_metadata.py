"""Additive settings metadata without changing value or storage contracts."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/scripts/client'))
from Driftkings.settings.panel.api import SettingsAPI
from Driftkings.settings.panel.controls import Control, DefinitionError
from Driftkings.settings.panel.compatibility import TemplateAdapter, template_category
from Driftkings.settings.panel.presenter import Presenter
from Driftkings.settings.settings_data import application_timing


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.api = SettingsAPI(self.folder.name)

    def test_optional_metadata_does_not_change_legacy_description_or_validation(self):
        old = Control('color', 'accent', default='0xD98219').finalize()
        self.assertNotIn('metadata', old.describe('en'))
        self.assertEqual(old.validate('D98219'), '#D98219')
        metadata = {'sourceType': 'ColorChoice', 'applyTiming': 'view'}
        new = Control('color', 'accent', default='0xD98219', metadata=metadata).finalize()
        metadata['applyTiming'] = 'restart'
        described = new.describe('en')
        self.assertEqual(described.pop('metadata')['applyTiming'], 'view')
        self.assertEqual(described, old.describe('en'))

    def test_invalid_metadata_is_rejected_before_registration(self):
        for metadata in ([], {'applyTiming': 'instant'}, {'allowAlpha': 'yes'}, {'sourceType': 1}):
            with self.assertRaises(DefinitionError):
                Control('text', 'name', default='', metadata=metadata)

    def test_revision_changes_only_for_real_metadata_changes_and_not_values(self):
        mod = self.api.register_mod('demo', name='Demo')
        mod.add_slider('scale', min_value=80, max_value=140, default=100)
        presenter = Presenter(self.api)
        presenter.session.set('demo', 'scale', 110)
        drafts, history = copy.deepcopy(presenter.session.drafts), copy.deepcopy(presenter.session.history)
        revision = self.api.registry.revision
        changed = Mock()
        self.api.registry.subscribe(changed)
        mod.set_control_metadata('scale', {'applyTiming': 'battle'})
        self.assertEqual(self.api.registry.revision, revision + 1)
        mod.set_control_metadata('scale', {'applyTiming': 'battle'})
        changed.assert_called_once_with()
        self.assertEqual(presenter.session.drafts, drafts)
        self.assertEqual(presenter.session.history, history)
        self.assertEqual(mod.values['scale'], 100)
        self.assertFalse(list(Path(self.folder.name).rglob('*.json')))
        presenter.session.set('demo', 'scale', 120)
        self.assertEqual(self.api.registry.revision, revision + 1)
        mod.set_control_metadata('scale', {})
        self.assertNotIn('metadata', presenter.schema()['mods'][0]['controls'][0])

    def test_categories_notify_existing_registry_and_allow_custom_labels(self):
        mod = self.api.register_mod('demo', name='Demo')
        revision = self.api.registry.revision
        mod.set_category('battle').set_category('battle')
        self.assertEqual(self.api.registry.revision, revision + 1)
        mod.set_category({'en': 'Tools', 'pt': 'Ferramentas'})
        self.api.language = 'pt'
        self.assertEqual(Presenter(self.api).schema()['mods'][0]['category'], 'Ferramentas')
        mod.set_category(None)
        self.assertEqual(Presenter(self.api).schema()['mods'][0]['category'], '')

    def test_template_category_uses_origin_and_optional_override(self):
        for scope, expected in (('battle', 'battle'), ('lobby', 'hangar'), ('components', 'general')):
            config = type('Config', (), {'__module__': 'Driftkings.settings.templates.' + scope + '.example'})()
            self.assertEqual(template_category(config), expected)
            config.SETTINGS_CATEGORY = 'Custom'
            self.assertEqual(template_category(config), 'Custom')
        self.assertEqual(template_category(SimpleNamespace()), 'general')

    def test_adapter_adds_policy_metadata_and_preserves_original_color_format(self):
        config = type('Config', (), {'__module__': 'Driftkings.settings.templates.battle.example'})()
        config.ID, config.i18n = 'PlayerPanelPro', {'UI_description': 'Example'}
        config.onPanelOpened = Mock()
        values = {'accent': '0xD98219'}
        legacy = Mock(entries={'PlayerPanelPro': (config, None, None, None)})
        legacy.describe.side_effect = lambda key: {
            'title': 'Example', 'values': copy.deepcopy(values), 'defaults': {'accent': '0xD98219'},
            'controls': [{'type': 'ColorChoice', 'varName': 'accent', 'text': 'Accent'}]}
        adapter = TemplateAdapter(self.api, legacy)
        adapter.populate()
        mod = self.api.registry.mods['legacy.PlayerPanelPro']
        control = mod.controls[0]
        self.assertEqual(mod.category, 'battle')
        self.assertEqual(control.metadata, {'sourceType': 'ColorChoice',
                                           'applyTiming': application_timing(config.ID, 'accent')})
        adapter.apply('PlayerPanelPro', mod, adapter.mapping[mod.id][1], {control.id: '#123456'})
        self.assertEqual(legacy.apply.call_args[0][1]['accent'], '0x123456')
        self.api.restart_required.add('PlayerPanelPro')
        self.assertTrue(Presenter(self.api).state()['status'][mod.id]['restartRequired'])

    def test_dependencies_registered_while_open_invalidate_schema(self):
        notification = Mock()
        self.api.registry.subscribe(notification)
        self.api.register_mod('dependent', name='Dependent', dependencies=['missing'])
        self.assertEqual(Presenter(self.api).schema()['mods'][0]['dependencies'],
                         [{'id': 'missing', 'installed': False, 'minimum': None}])
        self.assertGreaterEqual(notification.call_count, 2)


class AlphaOperationTests(unittest.TestCase):
    setUp = MetadataTests.setUp
    def prepare(self):
        mod = self.api.register_mod('colors', name='Colors')
        mod.add_color('color', default='0xD98219', metadata={'allowAlpha': True, 'alphaScale': 'percent', 'alphaKey': 'opacity'})
        mod.add_number('opacity', default=50, min_value=0, max_value=100)
        return mod, Presenter(self.api)

    def test_color_and_alpha_use_one_existing_history_entry(self):
        mod, presenter = self.prepare()
        presenter._on_set({'mod': 'colors', 'key': 'color', 'value': '#123456', 'alpha': 85}, {})
        self.assertEqual(len(presenter.session.history), 1)
        self.assertEqual(presenter.session.values('colors'), {'color': '#123456', 'opacity': 85})
        presenter.session.undo()
        self.assertEqual(presenter.session.drafts, {})
        self.assertEqual(mod.values['opacity'], 50)

    def test_invalid_alpha_is_atomic_and_noop_has_no_history(self):
        mod, presenter = self.prepare()
        with self.assertRaises(ValueError):
            presenter._on_set({'mod': 'colors', 'key': 'color', 'value': '#123456', 'alpha': 101}, {})
        self.assertEqual(presenter.session.drafts, {})
        self.assertEqual(presenter.session.history, [])
        presenter._on_set({'mod': 'colors', 'key': 'color', 'value': '#D98219', 'alpha': 50}, {})
        self.assertEqual(presenter.session.history, [])

    def test_history_limit_retains_previous_operations(self):
        mod, presenter = self.prepare()
        for n in range(50):
            presenter.session.set('colors', 'opacity', n)
        previous = presenter.session.values('colors')
        presenter._on_set({'mod': 'colors', 'key': 'color', 'value': '#123456', 'alpha': 85}, {})
        self.assertEqual(len(presenter.session.history), 50)
        presenter.session.undo()
        self.assertEqual(presenter.session.values('colors'), previous)

    def test_alpha_disabled_target_leaves_color_unchanged(self):
        mod, presenter = self.prepare()
        self.api.registry.mods['colors'].index['opacity'].enabled = False
        with self.assertRaises(ValueError):
            presenter._on_set({'mod': 'colors', 'key': 'color', 'value': '#123456', 'alpha': 85}, {})
        self.assertEqual(presenter.session.drafts, {})


    def test_second_set_failure_rolls_back_using_existing_snapshot(self):
        from unittest.mock import patch
        mod, presenter = self.prepare()
        presenter.session.set('colors', 'opacity', 60)
        previous = copy.deepcopy(presenter.session.drafts)
        history = presenter.session.history[:]
        real_set = presenter.session.set
        def fail_second(mod_id, key, value):
            if key == 'opacity':
                raise ValueError('Rejected')
            return real_set(mod_id, key, value)
        with patch.object(presenter.session, 'set', side_effect=fail_second):
            with self.assertRaises(ValueError):
                presenter._on_set({'mod': 'colors', 'key': 'color', 'value': '#123456', 'alpha': 85}, {})
        self.assertEqual(presenter.session.drafts, previous)
        self.assertEqual(presenter.session.history, history)

    def test_template_resolves_alpha_and_applies_both_without_prefix_migration(self):
        config = type('Config', (), {'ID': 'Example', 'i18n': {}, 'onPanelOpened': Mock()})()
        values = {'accent': '0xD98219', 'opacity': 50}
        legacy = Mock(entries={'Example': (config, None, None, None)})
        legacy.describe.side_effect = lambda key: {'title': 'Example', 'values': copy.deepcopy(values),
            'defaults': copy.deepcopy(values), 'controls': [
                {'type': 'ColorChoice', 'varName': 'accent', 'metadata': {'allowAlpha': True, 'alphaScale': 'percent', 'alphaPath': 'opacity'}},
                {'type': 'NumericStepper', 'varName': 'opacity', 'minimum': 0, 'maximum': 100}]}
        adapter = TemplateAdapter(self.api, legacy)
        adapter.populate()
        mod = self.api.registry.mods['legacy.Example']
        color, alpha = mod.controls
        self.assertEqual(color.metadata['alphaKey'], alpha.id)
        presenter = Presenter(self.api)
        presenter._on_set({'mod': mod.id, 'key': color.id, 'value': '#123456', 'alpha': 85}, {})
        presenter.session.apply()
        self.assertEqual(legacy.apply.call_count, 1)
        self.assertEqual(legacy.apply.call_args[0][1], {'accent': '0x123456', 'opacity': 85})
