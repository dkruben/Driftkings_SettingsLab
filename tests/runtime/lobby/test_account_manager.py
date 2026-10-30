# -*- coding: utf-8 -*-
"""Account persistence, active editing and native login ownership regressions."""
import copy
import json
import os
import shutil
import tempfile

from support import RuntimeTest, module
from support.accounts import Store, component, presentation, service


class AccountPersistenceTests(RuntimeTest):
    def setUp(self):
        super(AccountPersistenceTests, self).setUp()
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        self.api = component(self, self.directory)

    def test_protected_store_roundtrip_keeps_unicode(self):
        store = self.api['UserAccounts']()
        store.accounts = [dict(id='one', title=u'Conta de teste \u00e7', email='fictional', password='dummy', cluster=0)]
        self.assertTrue(store.write_accounts())
        self.assertEqual(self.api['UserAccounts']().accounts, store.accounts)

    def test_corrupt_file_is_preserved_and_blocks_writes(self):
        path = os.path.join(self.directory, 'driftkings', 'accounts.manager')
        os.makedirs(os.path.dirname(path))
        original = b'not a valid account document'
        with open(path, 'wb') as stream:
            stream.write(original)
        store = self.api['UserAccounts']()
        self.assertTrue(store.read_error)
        self.assertFalse(store.write_accounts())
        with open(path, 'rb') as stream:
            self.assertEqual(stream.read(), original)

    def test_failed_write_rolls_back_service_records(self):
        store = Store()
        accounts = service(self, store)
        previous = copy.deepcopy(store.accounts)
        store.saved = False
        with self.assertRaises(self.load('core.accounts').AccountError):
            accounts.save('first', 'Changed', 'other@example.com', 'replacement', 0)
        self.assertEqual(store.accounts, previous)

    def test_read_error_prevents_deleting_accounts(self):
        store = Store()
        accounts = service(self, store)
        store.read_error = True
        with self.assertRaises(self.load('core.accounts').AccountError):
            accounts.delete('first')
        self.assertEqual(len(store.accounts), 1)


class AccountPresentationTests(RuntimeTest):
    def setUp(self):
        super(AccountPresentationTests, self).setUp()
        self.accounts = service(self)
        self.closed = 0
        self.owner = module(canLogin=lambda: True)
        self.view = presentation(self, self.accounts, self.owner)
        self.view.parent = module(destroy=self.close)

    def close(self):
        self.closed += 1
        self.view._finalize()

    def action(self, action, **values):
        values['action'] = action
        self.view.onAction({'data': json.dumps(values)})
        return self.view.model.payload

    def test_password_is_absent_until_explicit_reveal(self):
        payload = self.action('edit', id='first')
        self.assertNotIn('password', payload['editing'])
        self.assertNotIn('fictional-secret', json.dumps(payload))
        payload = self.action('revealPassword')
        self.assertEqual(payload['editing']['password'], 'fictional-secret')
        self.assertTrue(all('password' not in row for row in payload['accounts']))

    def test_reveal_uses_active_edit_not_an_id_from_request(self):
        self.accounts.store.accounts.append(dict(self.accounts.store.accounts[0], id='second', password='other-dummy'))
        self.action('edit', id='first')
        payload = self.action('revealPassword', id='second')
        self.assertEqual(payload['editing']['password'], 'fictional-secret')

    def test_reveal_without_saved_edit_has_no_secret(self):
        payload = self.action('revealPassword')
        self.assertIsNone(payload['editing'])
        self.action('add')
        payload = self.action('revealPassword')
        self.assertNotIn('password', payload['editing'])

    def test_cancel_and_other_account_clear_revealed_password(self):
        self.action('edit', id='first')
        self.action('revealPassword')
        self.assertIsNone(self.action('cancel')['editing'])
        self.assertNotIn('password', self.action('edit', id='first')['editing'])

    def test_close_releases_edit_and_ignores_late_actions(self):
        self.action('edit', id='first')
        self.action('revealPassword')
        self.action('close')
        self.assertFalse(self.view.live)
        self.assertIsNone(self.view.editing)
        self.assertIsNone(self.view.controller)
        self.action('delete', id='first', confirmed=True)
        self.assertEqual(len(self.accounts.store.accounts), 1)
        self.assertEqual(self.closed, 1)

    def test_save_without_password_preserves_stored_secret(self):
        self.action('edit', id='first')
        payload = self.action('save', id='first', title='Renamed', email='test@example.com', password='', cluster=0)
        self.assertIsNone(payload['editing'])
        self.assertEqual(self.accounts.store.accounts[0]['password'], 'fictional-secret')


class AccountControllerTests(RuntimeTest):
    def setUp(self):
        super(AccountControllerTests, self).setUp()
        self.scheduled, self.cancelled = [], []
        def schedule(delay, handler):
            self.scheduled.append(handler)
            return len(self.scheduled)
        self.api = component(self, '.', module(callback=schedule, cancelCallback=self.cancelled.append))
        self.controller = self.api['controller']
        self.controller.active = True
        self.controller.space = 1
        class Login(object):
            pass
        self.login = Login()
        self.controller.loginPopulated(self.login)

    def test_repeated_login_updates_schedule_only_one_launcher(self):
        self.controller.scheduleLauncher()
        self.controller.scheduleLauncher()
        self.assertEqual(len(self.scheduled), 1)

    def test_context_exit_cancels_callback_and_closes_views_once(self):
        closed = []
        self.controller.window = module(destroy=lambda: closed.append('window'))
        self.controller.launcher = module(destroy=lambda: closed.append('launcher'))
        self.api['onContextLeft'](1)
        self.controller.closeViews()
        self.assertEqual(self.cancelled, [1])
        self.assertEqual(sorted(closed), ['launcher', 'window'])
        self.assertIsNone(self.controller.window)
        self.assertIsNone(self.controller.launcher)

    def test_disposal_of_an_old_login_does_not_close_the_current_login(self):
        result = self.controller.loginDisposed(lambda view: 'native', object())
        self.assertEqual(result, 'native')
        self.assertTrue(self.controller.canLogin())
        self.assertEqual(self.cancelled, [])
