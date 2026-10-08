import ast
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings._constants import BANKS_LOADER
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults


class Event:
    def __init__(self): self.handlers = []
    def __iadd__(self, handler): self.handlers.append(handler); return self
    def __isub__(self, handler): self.handlers.remove(handler); return self


class SoundBanksControllerTests(unittest.TestCase):
    def setUp(self):
        strings = {'UI_restart_reason':'{}', 'UI_restart_text':'{reason} {reasons}',
                   'UI_restart_reason_new':'New banks', 'UI_restart_reason_update':'Version change',
                   'UI_restart_header':'Restart', 'UI_restart_button_restart':'Restart',
                   'UI_restart_button_shutdown':'Exit', 'UI_restart_button_close':'Later',
                   'UI_restart_create':'Created: '}
        self.config = NS(ID=BANKS_LOADER.ID, LOG='BanksLoader:', data=defaults(BANKS_LOADER.ID), i18n=strings)
        self.config.data['debug'] = False
        self.signals = [NS(event=Event()) for _ in range(3)]
        events = NS(LoginView=NS(populate=NS(after=self.signals[0])),
                    LobbyView=NS(populate=NS(after=self.signals[1])),
                    PlayerAvatar=NS(startGUI=NS(after=self.signals[2])))
        self.engine = NS(savePreferences=Mock(), restartGame=Mock(), quit=Mock())
        self.builder = Mock()
        self.builder.setFormattedMessage.return_value = self.builder
        self.builder.setFormattedTitle.return_value = self.builder
        self.dialog = Mock(return_value='pending')
        ns = dict(BANKS_LOADER=BANKS_LOADER, settings_service=SettingsService(SettingsData()),
                  events=events, BigWorld=self.engine, wg_async=lambda fn:fn, wg_await=lambda result:result,
                  WarningDialogBuilder=lambda:self.builder, dialogs=NS(show=self.dialog),
                  SL=NS(appLoader=NS(getApp=lambda:None)), WindowLayer=NS(VIEW='view'),
                  DButtons=NS(PURCHASE='restart', RESEARCH='exit', SUBMIT='close'), remDups=lambda values:list(set(values)))
        path = ROOT / 'source/scripts/client/Driftkings/components/sound_banks.py'
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        exec(compile(tree, str(path), 'exec'), ns)
        self.controller = ns['BanksLoaderController'](self.config)
        self.controller.suppress_old_mod = Mock()
        self.controller.checkConfigs = Mock()

    def start_with_changes(self):
        self.controller.start()
        self.controller.editedBanks['create'].append('custom.bnk')

    def finish(self, request, result):
        with self.assertRaises(StopIteration): request.send(NS(result=result))

    def test_start_stop_are_idempotent_and_do_not_change_preferences(self):
        before = deepcopy(self.config.data)
        c = self.controller
        c.start(); c.start()
        c.checkConfigs.assert_called_once()
        c.suppress_old_mod.assert_called_once()
        self.assertEqual([len(s.event.handlers) for s in self.signals], [1,1,1])
        c.stop(); c.stop()
        self.assertEqual([len(s.event.handlers) for s in self.signals], [0,0,0])
        self.assertEqual(self.config.data, before)
        c.start()
        self.assertEqual([len(s.event.handlers) for s in self.signals], [1,1,1])

    def test_failed_start_leaves_no_subscriptions_and_can_retry(self):
        self.controller.checkConfigs.side_effect = RuntimeError('unavailable resources')
        with self.assertRaises(RuntimeError): self.controller.start()
        self.assertFalse(self.controller._runtimeActive)
        self.assertEqual([len(s.event.handlers) for s in self.signals], [0,0,0])
        self.controller.checkConfigs.side_effect = None
        self.controller.start()
        self.assertTrue(self.controller._runtimeActive)

    def test_restart_dialog_only_opens_once_and_later_suppresses_further_prompts(self):
        c = self.controller
        c.start()
        with self.assertRaises(StopIteration): next(c.tryRestart())
        self.dialog.assert_not_called()
        c.editedBanks['create'].append('custom.bnk')
        request = c.tryRestart()
        self.assertEqual(next(request), 'pending')
        with self.assertRaises(StopIteration): next(c.tryRestart())
        self.dialog.assert_called_once()
        self.finish(request, 'close')
        self.assertFalse(c._restartPending)
        with self.assertRaises(StopIteration): next(c.tryRestart())
        self.dialog.assert_called_once()
        self.engine.restartGame.assert_not_called()
        self.engine.quit.assert_not_called()

    def test_old_dialog_cannot_restart_after_stop_and_reentry(self):
        self.start_with_changes()
        request = self.controller.tryRestart()
        next(request)
        self.controller.stop()
        self.controller.start()
        self.finish(request, 'restart')
        self.engine.savePreferences.assert_not_called()
        self.engine.restartGame.assert_not_called()
        self.assertFalse(self.controller._restartPending)

    def test_confirmed_restart_and_exit_preserve_preferences_first(self):
        self.start_with_changes()
        calls = []
        self.engine.savePreferences.side_effect = lambda:calls.append('save')
        self.engine.restartGame.side_effect = lambda:calls.append('restart')
        self.engine.quit.side_effect = lambda:calls.append('exit')
        for action in ('restart', 'exit'):
            request = self.controller.tryRestart()
            next(request)
            self.finish(request, action)
        self.assertEqual(calls, ['save','restart','save','exit'])

    def test_dialog_error_releases_pending_flag_and_uses_current_debug_option(self):
        self.start_with_changes()
        self.config.data['debug'] = True
        self.dialog.side_effect = RuntimeError('dialog unavailable')
        with self.assertRaises(RuntimeError): next(self.controller.tryRestart())
        self.assertFalse(self.controller._restartPending)
        self.assertIn('custom.bnk', self.builder.setFormattedMessage.call_args.args[0])
        self.dialog.side_effect = None
        request = self.controller.tryRestart()
        next(request)
        request.close()
        self.assertFalse(self.controller._restartPending)

    def test_memory_changes_read_settings_without_writing_them(self):
        before = deepcopy(self.config.data)
        class Section(dict):
            def writeInt(self, key, value): self[key].asInt = value
        section = Section(memoryLimit=NS(asInt=0))
        self.controller.manageMemorySettings(section)
        self.assertEqual(section['memoryLimit'].asInt, before['memoryLimit'])
        self.assertEqual(self.controller.editedBanks['memory'], ['memoryLimit'])
        self.controller.manageMemorySettings(section)
        self.assertEqual(self.controller.editedBanks['memory'], ['memoryLimit'])
        self.assertEqual(self.config.data, before)


if __name__ == '__main__':
    unittest.main()
