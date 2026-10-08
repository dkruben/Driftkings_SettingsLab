import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/scripts/client'))
from Driftkings.settings.service import SettingsService, restore
from Driftkings.settings.settings_data import SettingsData
from Driftkings._constants import OWN_HEALTH, GLOBAL, BATTLE_ALIASES


class SettingsServiceTests(unittest.TestCase):
    def setUp(self):
        self.data = SettingsData()
        self.service = SettingsService(self.data)
        self.config = NS(ID=OWN_HEALTH.ID, data={'enabled': True, 'position': {'x': 1, 'y': 2}})
        self.config.onApplySettings = Mock(side_effect=lambda change: self.config.data.update(change))
        self.data.register(self.config)

    def test_live_reads_by_id_section_constant_and_alias(self):
        for name in (OWN_HEALTH, OWN_HEALTH.ID, OWN_HEALTH.NAME):
            self.assertIs(self.service.getComponentDict(name), self.config.data)
            self.assertEqual(self.service.getSetting(name, ('position', 'x')), 1)
        from Driftkings.views import BATTLE_COMPONENTS
        with patch.dict(BATTLE_COMPONENTS, {BATTLE_ALIASES.OWN_HEALTH: (object, self.config)}):
            self.assertIs(self.service.getSettingDictByAliasBattle(BATTLE_ALIASES.OWN_HEALTH), self.config.data)
        with self.assertRaises(KeyError): self.service.getSetting('missing')

    def test_only_changed_sections_are_saved_and_emitted_after_apply(self):
        observed = []
        self.service.onModSettingsChanged.connect(lambda name, changes: observed.append((name, changes, self.config.data['position']['x'])))
        self.service.apply(self.config, {'enabled': True, 'position': {'x': 9}})
        self.config.onApplySettings.assert_called_once_with({'position': {'x': 9, 'y': 2}})
        self.assertEqual(observed, [('own_health', {'position': {'x': 9, 'y': 2}}, 9)])
        self.service.apply(self.config, {'position': {'x': 9}})
        self.assertEqual(len(observed), 1)
        self.assertEqual(self.config.onApplySettings.call_count, 1)

    def test_failure_restores_live_values_and_never_notifies(self):
        nested = self.config.data['position']
        listener = Mock()
        self.service.onModSettingsChanged.connect(listener)
        def fail(changes):
            nested['x'] = 77
            raise IOError('save failed')
        self.config.onApplySettings.side_effect = fail
        with self.assertRaises(IOError): self.service.apply(self.config, {'position': {'x': 77}})
        self.assertIs(self.config.data['position'], nested)
        self.assertEqual(nested, {'x': 1, 'y': 2})
        listener.assert_not_called()

    def test_listener_failure_and_mutation_do_not_affect_other_listeners(self):
        received = []
        def broken(name, changes):
            changes.clear()
            raise RuntimeError('listener failed')
        self.service.onModSettingsChanged.connect(broken)
        self.service.onModSettingsChanged.connect(lambda name, changes: received.append(changes))
        with self.assertLogs('Driftkings.Settings', level='ERROR'):
            self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
        self.assertEqual(received, [{'enabled': False}])
        self.assertFalse(self.config.data['enabled'])

    def test_set_rejects_unknown_keys_and_invalid_types(self):
        with self.assertRaises(KeyError): self.service.setSetting(OWN_HEALTH, 'unknown', True)
        with self.assertRaises(ValueError): self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, 'yes')
        self.config.onApplySettings.assert_not_called()

    def test_recursive_application_fails_without_partial_values(self):
        self.config.onApplySettings.side_effect = lambda changes: self.service.apply(self.config, changes)
        with self.assertRaises(RuntimeError): self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
        self.assertTrue(self.config.data['enabled'])

    def test_refresh_runs_after_save_and_cannot_undo_success(self):
        listener = Mock()
        self.service.onModSettingsChanged.connect(listener)
        def refresh(component, changes):
            self.assertFalse(self.config.data['enabled'])
            self.assertEqual(changes, {'enabled': False})
            raise RuntimeError('Flash unavailable')
        self.config.onModSettingsChanged = Mock(side_effect=refresh)
        with self.assertLogs('Driftkings.Settings', level='ERROR'):
            self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
        self.assertFalse(self.config.data['enabled'])
        self.config.onModSettingsChanged.assert_called_once_with('own_health', {'enabled': False})
        listener.assert_called_once_with('own_health', {'enabled': False})

    def test_refresh_is_skipped_when_persistence_fails(self):
        self.config.onModSettingsChanged = Mock()
        self.config.onApplySettings.side_effect = IOError('disk unavailable')
        with self.assertRaises(IOError): self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
        self.config.onModSettingsChanged.assert_not_called()

    def test_listener_disposal_and_duplicate_subscription(self):
        listener = Mock()
        event = self.service.onModSettingsChanged
        event.connect(listener); event.connect(listener)
        self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
        listener.assert_called_once()
        event.disconnect(listener); event.disconnect(listener)
        self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, True)
        listener.assert_called_once()

    def test_scoped_listeners_receive_only_matching_components_and_keys(self):
        event = self.service.onModSettingsChanged
        enabled, position, unrelated = Mock(), Mock(), Mock()
        event.connect(enabled, OWN_HEALTH, (GLOBAL.ENABLED,))
        event.connect(position, OWN_HEALTH.ID, ('position',))
        event.connect(unrelated, 'InfoPanel')
        self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
        enabled.assert_called_once_with(OWN_HEALTH.NAME, {'enabled': False})
        position.assert_not_called()
        unrelated.assert_not_called()
        self.service.setSetting(OWN_HEALTH, ('position', 'x'), 7)
        position.assert_called_once_with(OWN_HEALTH.NAME, {'position': {'x': 7, 'y': 2}})
        enabled.assert_called_once()

    def test_replacing_config_detaches_previous_refresh_callback(self):
        old = Mock()
        self.config.onModSettingsChanged = old
        self.service.register(self.config)
        replacement = NS(ID=OWN_HEALTH.ID, data={'enabled': True},
                         onModSettingsChanged=Mock(), REFRESH_KEYS=(GLOBAL.ENABLED,))
        replacement.onApplySettings = lambda change: replacement.data.update(change)
        self.service.register(replacement)
        self.service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
        old.assert_not_called()
        replacement.onModSettingsChanged.assert_called_once_with(OWN_HEALTH.NAME, {'enabled': False})
        del replacement.onModSettingsChanged
        self.service.register(replacement)
        self.assertEqual(self.service.onModSettingsChanged._listeners, [])

    def test_runtime_changes_keep_live_references_without_writing_disk(self):
        nested = self.config.data['position']
        listener = Mock()
        self.service.onModSettingsChanged.connect(listener, OWN_HEALTH)
        self.service.apply(OWN_HEALTH, {'position': {'x': 4}}, persist=False)
        self.assertIs(self.config.data['position'], nested)
        self.assertEqual(nested, {'x': 4, 'y': 2})
        self.config.onApplySettings.assert_not_called()
        listener.assert_called_once_with(OWN_HEALTH.NAME, {'position': {'x': 4, 'y': 2}})
        self.service.setSetting(OWN_HEALTH, ('position', 'x'), 8)
        self.config.onApplySettings.assert_called_once_with({'position': {'x': 8, 'y': 2}})

    def test_notifications_keep_complete_sections_and_exact_independent_paths(self):
        from Driftkings.settings.service import affects
        observed = []
        self.service.onModSettingsChanged.connect(lambda component, changes: observed.append(changes))
        self.service.setSetting(OWN_HEALTH, ('position', 'x'), 9)
        changes = observed[0]
        self.assertEqual(changes, {'position': {'x': 9, 'y': 2}})
        self.assertEqual(changes.paths, frozenset([('position', 'x')]))
        self.assertTrue(affects(changes, 'position'))
        self.assertTrue(affects(changes, ('position', 'x')))
        self.assertFalse(affects(changes, ('position', 'y')))
        self.assertTrue(affects({'position': {}}, ('position', 'y')))

    def test_reload_publishes_external_edits_without_saving_and_ignores_noops(self):
        observed = Mock()
        self.service.onModSettingsChanged.connect(observed, OWN_HEALTH)
        self.config.readData = lambda quiet: self.config.data['position'].update(x=7)
        self.config.readCurrentSettings = Mock()
        self.service.reload(self.config)
        self.service.reload(self.config)
        observed.assert_called_once_with(OWN_HEALTH.NAME, {'position': {'x': 7, 'y': 2}})
        self.config.onApplySettings.assert_not_called()

    def test_reload_failure_restores_preferences_and_does_not_publish(self):
        observed = Mock()
        self.service.onModSettingsChanged.connect(observed)
        def broken(quiet):
            self.config.data['enabled'] = False
            raise ValueError('Invalid JSON option')
        self.config.readData = broken
        with self.assertRaises(ValueError): self.service.reload(self.config)
        self.assertTrue(self.config.data['enabled'])
        observed.assert_not_called()
