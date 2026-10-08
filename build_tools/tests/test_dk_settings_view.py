# -*- coding: utf-8 -*-
"""Game layer of DK Mod Settings with stand-ins for the client's Wulf classes."""
import contextlib
import importlib
import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[2]
CLIENT = str(ROOT / 'source/scripts/client')
if CLIENT not in sys.path:
    sys.path.insert(0, CLIENT)


class Command(object):
    def __iadd__(self, other):
        return self


class ViewModel(object):
    def __init__(self, properties=0, commands=0):
        self.props = []
        self._initialize()

    def _initialize(self):
        pass

    def _addStringProperty(self, name, value):
        self.props.append(value)

    def _addViewModelProperty(self, name, value):
        self.props.append(value)

    def _addCommand(self, name):
        return Command()

    def _setString(self, index, value):
        self.props[index] = value

    @contextlib.contextmanager
    def transaction(self):
        yield self


class ViewImpl(object):
    def __init__(self, settings):
        self.model = settings.model
        self.window = None

    def getViewModel(self):
        return self.model

    def getParentWindow(self):
        return self.window

    def _onLoading(self, *args, **kwargs):
        pass

    def _finalize(self):
        pass


class WindowImpl(object):
    def __init__(self, flags, content=None, layer=None):
        self.content = content
        content.window = self
        self.centered = 0
        self.destroyed = False

    def load(self):
        self.content._onLoading()
        self._onReady()

    def _onReady(self):
        pass

    def center(self):
        self.centered += 1

    def destroy(self):
        if not self.destroyed:
            self.destroyed = True
            self.content._finalize()
            self._finalize()

    def _finalize(self):
        pass


def game_modules(player):
    flags = types.SimpleNamespace(VIEW=1, WINDOW=1, WINDOW_MODAL=2, WINDOW_FULLSCREEN=1024)
    wulf = types.SimpleNamespace(ViewModel=ViewModel, ViewSettings=lambda layout: types.SimpleNamespace(layout=layout),
                                 ViewFlags=flags, WindowFlags=flags, WindowLayer=types.SimpleNamespace(TOP_WINDOW=5))
    return {
        'BigWorld': types.SimpleNamespace(player=lambda: player[0], keyToString=lambda code: 'KEY_' + str(code), isKeyDown=lambda code: False),
        'Keys': types.SimpleNamespace(KEY_ESCAPE=1, KEY_LCONTROL=29, KEY_RCONTROL=157, KEY_LSHIFT=42, KEY_RSHIFT=54, KEY_LALT=56, KEY_RALT=184),
        'frameworks': types.ModuleType('frameworks'), 'frameworks.wulf': wulf,
        'gui': types.ModuleType('gui'), 'gui.impl': types.ModuleType('gui.impl'),
        'gui.impl.pub': types.SimpleNamespace(ViewImpl=ViewImpl),
        'gui.impl.pub.window_impl': types.SimpleNamespace(WindowImpl=WindowImpl),
        'skeletons': types.ModuleType('skeletons'), 'skeletons.gui': types.ModuleType('skeletons.gui'),
        'skeletons.gui.app_loader': types.SimpleNamespace(GuiGlobalSpaceID=types.SimpleNamespace(LOBBY=6, LOGIN=2, BATTLE=5)),
        # The view only needs the resource lookup of the owned bridge.
        'Driftkings.ui': types.ModuleType('Driftkings.ui'),
        'Driftkings.ui.gameface': types.SimpleNamespace(resource_id=lambda key: 1234, attach_assets=lambda *a, **k: None),
    }


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.player = [types.SimpleNamespace(arena=None, databaseID=1)]
        self.patcher = patch.dict(sys.modules, game_modules(self.player))
        self.patcher.start()
        sys.modules.pop('Driftkings.views.hangar.settings_window', None)
        self.module = importlib.import_module('Driftkings.views.hangar.settings_window')
        from Driftkings.settings.panel.api import SettingsAPI
        self.api = SettingsAPI(self.root)
        self.api.start('en')
        demo = self.api.register_mod('dk.demo', name='Demo')
        demo.add_slider(id='volume', min_value=0, max_value=100, default=80)
        self.controller = self.module.SettingsController()
        self.controller.start(self.api)
        self.controller.onContextEntered(6)

    def tearDown(self):
        self.controller.stop()
        self.patcher.stop()
        sys.modules.pop('Driftkings.views.hangar.settings_window', None)
        shutil.rmtree(self.root)

    def send(self, **data):
        self.view.onAction({'data': json.dumps(data)})

    def open(self):
        self.assertTrue(self.controller.open())
        self.view = self.controller.window.content
        return self.view.model

    def test_updater_observation_patches_state_and_unsubscribes_on_close(self):
        from Driftkings.core.updater.state import State, AVAILABLE
        state = State()
        self.api.updater = types.SimpleNamespace(state=state)
        model = self.open()
        schema = model.props[0]
        self.assertEqual(len(state._listeners), 1)
        state.update(status=AVAILABLE, latestVersion='1.0.0', compatible=False,
                     changelog=['<b>Literal remote text</b>'])
        self.assertIs(model.props[0], schema)
        self.assertEqual(json.loads(model.props[1])['updater']['latestVersion'], '1.0.0')
        self.controller.close()
        self.assertEqual(state._listeners, [])
        state.update(status=AVAILABLE, latestVersion='2.0.0')

    def test_open_push_patch_and_close(self):
        model = self.open()
        self.assertTrue(self.api.window_open)
        schema = model.props[0]
        self.assertIn('dk.demo', [mod['id'] for mod in json.loads(schema)['mods']])
        self.assertFalse(self.controller.open(), 'a second window is never created')
        self.send(action='set', mod='dk.demo', key='volume', value=20)
        self.assertIs(model.props[0], schema, 'the schema is not resent for value changes')
        state = json.loads(model.props[1])
        self.assertEqual(state['values']['dk.demo']['volume'], 20)
        self.assertTrue(state['pending'])
        self.send(action='apply')
        self.send(action='save')
        self.assertIsNone(self.controller.window)
        self.assertFalse(self.api.window_open)
        self.assertEqual(json.loads((Path(self.root) / 'demo.json').read_text())['volume'], 20)

    def test_structure_changes_resend_the_schema(self):
        model = self.open()
        schema = model.props[0]
        self.api.register_mod('dk.late', name='Late').add_switch(id='enabled')
        self.assertIsNot(model.props[0], schema)
        self.assertIn('dk.late', model.props[0])

    def test_metadata_refresh_keeps_drafts_and_then_returns_to_state_only_updates(self):
        model = self.open()
        self.send(action='set', mod='dk.demo', key='volume', value=20)
        presenter = self.view.presenter
        history = list(presenter.session.history)
        old_schema = model.props[0]
        self.api.mod('dk.demo').set_control_metadata('volume', {'applyTiming': 'view'})
        self.assertNotEqual(model.props[0], old_schema)
        description = next(mod for mod in json.loads(model.props[0])['mods'] if mod['id'] == 'dk.demo')
        self.assertEqual(description['controls'][0]['metadata'], {'applyTiming': 'view'})
        self.assertIs(self.view.presenter, presenter)
        self.assertEqual(presenter.session.value('dk.demo', 'volume'), 20)
        self.assertEqual(presenter.session.history, history)
        schema = model.props[0]
        self.send(action='set', mod='dk.demo', key='volume', value=30)
        self.assertIs(model.props[0], schema)
        self.api.mod('dk.demo').set_category('battle')
        self.assertNotEqual(model.props[0], schema)

    def test_rejects_oversized_and_malformed_requests(self):
        model = self.open()
        state = model.props[1]
        self.view.onAction({'data': 'x' * 70000})
        self.view.onAction({'data': '{not json'})
        self.view.onAction('not a dict')
        self.assertIs(model.props[1], state)

    def test_only_opens_in_the_lobby_outside_battle(self):
        self.player[0] = types.SimpleNamespace(arena=object(), databaseID=1)
        self.assertFalse(self.controller.open())
        self.player[0] = types.SimpleNamespace(arena=None, databaseID=1)
        self.controller.onContextLeft(6)
        self.assertFalse(self.controller.open())

    def test_leaving_the_lobby_closes_and_discards(self):
        self.open()
        self.send(action='set', mod='dk.demo', key='volume', value=5)
        self.send(action='apply')
        self.assertEqual(self.api.get('dk.demo', 'volume'), 5)
        self.controller.onContextLeft(6)
        self.assertIsNone(self.controller.window)
        self.assertEqual(self.api.get('dk.demo', 'volume'), 5)

    def test_f10_toggle_and_capture_use_native_key_codes(self):
        event = lambda code: types.SimpleNamespace(key=code, isKeyDown=lambda: True)
        self.controller.onKey(event(68))
        self.assertTrue(self.controller.is_open)
        self.view = self.controller.window.content
        self.send(action='capture', mod='dk.settings', key='openKey')
        self.controller.onKey(event(30))
        self.assertTrue(self.controller.is_open)
        self.assertEqual(self.view.presenter.session.value('dk.settings', 'openKey'), [[30]])
        self.send(action='apply')
        self.controller.onKey(event(68))
        self.assertTrue(self.controller.is_open, 'old shortcut must no longer close the window')
        self.controller.onKey(event(30))
        self.assertFalse(self.controller.is_open)

    def test_modifier_capture_ignores_modifier_keydown_and_keeps_both_sides(self):
        self.open()
        event = lambda code: types.SimpleNamespace(key=code, isKeyDown=lambda: True)
        self.send(action='capture', mod='dk.settings', key='openKey')
        self.controller.onKey(event(29))
        self.assertIsNotNone(self.view.presenter.capture)
        with patch.object(self.module.BigWorld, 'isKeyDown', side_effect=lambda code: code == 29):
            self.controller.onKey(event(68))
        self.assertEqual(self.view.presenter.session.value('dk.settings', 'openKey'), [[29, 157], [68]])
        self.assertIsNone(self.view.presenter.capture)

    def test_mouse_capture_saves_native_codes_above_255(self):
        self.open()
        self.send(action='capture', mod='dk.settings', key='openKey')
        self.controller.onKey(types.SimpleNamespace(key=259, isKeyDown=lambda: True))
        self.assertEqual(self.view.presenter.session.value('dk.settings', 'openKey'), [[259]])
        self.assertIsNone(self.view.presenter.capture)
        self.send(action='save')
        self.assertEqual(self.api.get('dk.settings', 'openKey'), [[259]])

    def test_invalid_and_primary_mouse_events_do_not_break_capture(self):
        self.open()
        self.send(action='capture', mod='dk.settings', key='openKey')
        for code in (0, 256, 999, True, 1.5):
            self.controller.onKey(types.SimpleNamespace(key=code, isKeyDown=lambda: True))
            self.assertIsNotNone(self.view.presenter.capture)
        self.controller.onKey(types.SimpleNamespace(key=30, isKeyDown=lambda: True))
        self.assertEqual(self.view.presenter.session.value('dk.settings', 'openKey'), [[30]])
        self.assertIsNone(json.loads(self.view.model.props[1])['capture'])

    def test_modifier_alone_is_rejected_without_explicit_metadata(self):
        self.open()
        self.send(action='capture', mod='dk.settings', key='openKey')
        previous = self.view.presenter.session.value('dk.settings', 'openKey')
        self.controller.onKey(types.SimpleNamespace(key=29, isKeyDown=lambda: True))
        self.controller.onKey(types.SimpleNamespace(key=29, isKeyDown=lambda: False))
        self.assertEqual(self.view.presenter.session.value('dk.settings', 'openKey'), previous)
        self.assertIsNotNone(self.view.presenter.capture)

    def test_modifier_alone_can_be_assigned_on_release(self):
        self.open()
        self.api.registry.mods['dk.settings'].index['openKey'].metadata['allowModifierOnly'] = True
        self.send(action='capture', mod='dk.settings', key='openKey')
        self.controller.onKey(types.SimpleNamespace(key=29, isKeyDown=lambda: True))
        self.assertIsNotNone(self.view.presenter.capture)
        self.controller.onKey(types.SimpleNamespace(key=29, isKeyDown=lambda: False))
        self.assertEqual(self.view.presenter.session.value('dk.settings', 'openKey'), [[29, 157]])
        self.assertIsNone(self.view.presenter.capture)

    def test_capture_validation_failure_retains_capture_and_reports_error(self):
        self.open()
        self.send(action='capture', mod='dk.settings', key='openKey')
        with patch.object(self.view.presenter.session, 'set', side_effect=ValueError('disabled')):
            self.controller.onKey(types.SimpleNamespace(key=30, isKeyDown=lambda: True))
        self.assertIsNotNone(self.view.presenter.capture)
        self.assertEqual(json.loads(self.view.model.props[1])['message']['kind'], 'error')
        self.controller.onKey(types.SimpleNamespace(key=1, isKeyDown=lambda: True))
        self.assertIsNone(self.view.presenter.capture)
        self.assertTrue(self.controller.is_open)

    def test_clear_or_navigation_cancels_pending_capture(self):
        self.open()
        self.send(action='capture', mod='dk.settings', key='openKey')
        self.send(action='set', mod='dk.settings', key='openKey', value=[])
        self.assertIsNone(self.view.presenter.capture)
        self.controller.onKey(types.SimpleNamespace(key=30, isKeyDown=lambda: True))
        self.assertEqual(self.view.presenter.session.value('dk.settings', 'openKey'), [])
        self.send(action='capture', mod='dk.settings', key='openKey')
        self.send(action='select', mod='dk.demo')
        self.assertIsNone(self.view.presenter.capture)

    def test_battle_opens_via_shortcut_and_never_restarts_client(self):
        self.player[0] = types.SimpleNamespace(arena=object())
        self.controller.onContextEntered(5)
        self.controller.onKey(types.SimpleNamespace(key=68, isKeyDown=lambda:True))
        self.assertTrue(self.controller.is_open)
        self.assertTrue(self.api.in_battle)
        self.assertFalse(self.controller.restart())

    def updater_fixture(self, prepared=True):
        from Driftkings.core.updater.state import State, RESTART_REQUIRED, INSTALLING
        state = State()
        state.update(status=RESTART_REQUIRED if prepared else INSTALLING, installScheduled=prepared,
                     canRestart=prepared, latestVersion='1.0.0')
        updater = types.SimpleNamespace(state=state, restart_ready=Mock(return_value=prepared),
                                        claim_restart=Mock(side_effect=[prepared, False]),
                                        defer_restart=Mock(return_value=True), revoke_restart=Mock(), cancel_install=Mock(return_value=True),
                                        schedule_install=Mock(return_value=True))
        self.api.updater = updater
        bigworld = sys.modules['BigWorld']
        bigworld.savePreferences = Mock()
        bigworld.restartGame = Mock()
        bigworld.quit = Mock()
        wgc = types.SimpleNamespace(notifyRestart=Mock())
        patcher = patch.dict(sys.modules, {'WGC': wgc})
        patcher.start()
        self.addCleanup(patcher.stop)
        return updater, bigworld, wgc

    def test_updater_restart_is_blocked_before_prepared(self):
        updater, bigworld, wgc = self.updater_fixture(prepared=False)
        self.open()
        self.send(action='restart_update')
        self.assertFalse(self.view.presenter.restart_prompt)
        self.assertFalse(self.controller.restart(reason='updater'))
        bigworld.restartGame.assert_not_called()
        wgc.notifyRestart.assert_not_called()

    def test_updater_quits_for_coordinated_restart_and_prevents_duplicate_request(self):
        updater, bigworld, wgc = self.updater_fixture()
        self.open()
        self.send(action='restart_update')
        self.assertTrue(self.view.presenter.restart_prompt)
        self.send(action='restart', choice='now')
        bigworld.savePreferences.assert_called_once()
        wgc.notifyRestart.assert_not_called()
        bigworld.restartGame.assert_not_called()
        bigworld.quit.assert_called_once()
        self.assertFalse(self.controller.restart(reason='updater'))
        self.assertEqual(bigworld.quit.call_count, 1)

    def test_updater_later_only_closes_dialog_and_window_reopens_from_service_state(self):
        updater, bigworld, wgc = self.updater_fixture()
        self.open()
        self.send(action='restart_update')
        self.send(action='restart', choice='later')
        self.assertTrue(self.controller.is_open)
        self.assertFalse(self.view.presenter.restart_prompt)
        updater.defer_restart.assert_called_once()
        updater.cancel_install.assert_not_called()
        self.controller.close()
        self.assertEqual(updater.state._listeners, [])
        model = self.open()
        self.assertTrue(json.loads(model.props[1])['updater']['installScheduled'])
        self.assertFalse(self.view.presenter.restart_prompt)
        bigworld.restartGame.assert_not_called()

    def test_normal_settings_restart_keeps_engine_and_wgc_flow(self):
        updater, bigworld, wgc = self.updater_fixture()
        self.assertTrue(self.controller.restart())
        wgc.notifyRestart.assert_called_once()
        bigworld.restartGame.assert_called_once()
        bigworld.quit.assert_not_called()
        updater.claim_restart.assert_not_called()

    def test_updater_shutdown_failure_revokes_native_relaunch(self):
        updater, bigworld, wgc = self.updater_fixture()
        bigworld.quit.side_effect = RuntimeError('shutdown failed')
        self.assertFalse(self.controller.restart(reason='updater'))
        updater.revoke_restart.assert_called_once()
        bigworld.restartGame.assert_not_called()
        wgc.notifyRestart.assert_not_called()

    def test_preferences_failure_does_not_request_shutdown_or_native_relaunch(self):
        updater, bigworld, wgc = self.updater_fixture()
        bigworld.savePreferences.side_effect = RuntimeError('save failed')
        self.assertFalse(self.controller.restart(reason='updater'))
        updater.claim_restart.assert_not_called()
        bigworld.quit.assert_not_called()
        wgc.notifyRestart.assert_not_called()

    def test_shutdown_failure_after_window_disposal_does_not_use_disposed_presenter(self):
        updater, bigworld, wgc = self.updater_fixture()
        self.open()
        self.send(action='restart_update')
        bigworld.quit.side_effect = RuntimeError('shutdown failed')
        self.send(action='restart', choice='now')
        updater.revoke_restart.assert_called_once()
        self.assertFalse(self.controller.is_open)
        wgc.notifyRestart.assert_not_called()

    def test_updater_cancellation_delegates_to_service_without_claiming_success(self):
        updater, bigworld, wgc = self.updater_fixture()
        self.open()
        self.send(action='cancel_update_install')
        updater.cancel_install.assert_called_once()
        self.assertIsNone(updater.state.snapshot()['lastInstallResult'])
        updater.restart_ready.return_value = False
        self.send(action='restart_update')
        self.assertFalse(self.view.presenter.restart_prompt)
        bigworld.restartGame.assert_not_called()

    def test_updater_restart_rechecks_context_in_existing_controller(self):
        updater, bigworld, wgc = self.updater_fixture()
        self.open()
        self.send(action='restart_update')
        self.player[0] = types.SimpleNamespace(arena=object())
        self.send(action='restart', choice='now')
        bigworld.restartGame.assert_not_called()
        updater.claim_restart.assert_not_called()

    def test_updater_unsaved_edits_block_restart(self):
        updater, bigworld, wgc = self.updater_fixture()
        self.open()
        self.send(action='set', mod='dk.demo', key='volume', value=20)
        self.send(action='restart_update')
        self.assertFalse(self.view.presenter.restart_prompt)
        bigworld.restartGame.assert_not_called()

    def test_hangar_shortcut_button_is_removed(self):
        self.assertFalse(hasattr(self.module, 'install_gameface'))
        controls = self.api.registry.mods['dk.settings'].index
        self.assertNotIn('showButton', controls)
        self.assertNotIn('buttonX', controls)


if __name__ == '__main__':
    unittest.main()
