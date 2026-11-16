# -*- coding: utf-8 -*-
"""Passwordless account profiles: persistence, presentation, login pre-fill and legacy isolation.

Synthetic data only. No real account file is opened and no password is created or read.
"""
import copy
import json
import os
import shutil
import tempfile

try:
    import __builtin__ as builtins
except ImportError:
    import builtins

from support import RuntimeTest, module, source
from support.accounts import Store, component, presentation, service

LEGACY_PASSWORD = 'legacy-synthetic-secret'


class AccountPersistenceTests(RuntimeTest):
    def setUp(self):
        super(AccountPersistenceTests, self).setUp()
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        self.api = component(self, self.directory)
        self.profiles = os.path.join(self.directory, 'driftkings', 'accounts_profiles.json')
        self.legacy = os.path.join(self.directory, 'driftkings', 'accounts.manager')

    def write(self, path, data):
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as stream:
            stream.write(data)

    def test_profile_roundtrip_keeps_unicode_and_writes_no_secret(self):
        store = self.api['ProfileFile'](self.profiles, self.legacy)
        store.accounts = [dict(id='one', title=u'Conta de teste ç', email='synthetic@example.com', cluster=0)]
        self.assertTrue(store.write_accounts())
        self.assertEqual(self.api['ProfileFile'](self.profiles, self.legacy).accounts, store.accounts)
        with open(self.profiles, 'rb') as stream:
            written = stream.read().decode('utf-8')
        self.assertNotIn('password', written)

    def test_record_with_a_secret_is_refused_and_never_written(self):
        store = self.api['ProfileFile'](self.profiles, self.legacy)
        store.accounts = [dict(id='one', title='Main', email='synthetic@example.com', cluster=0, password='x')]
        self.assertFalse(store.write_accounts())
        self.assertFalse(os.path.exists(self.profiles))

    def test_corrupt_file_is_preserved_and_blocks_writes(self):
        original = b'not a valid account document'
        self.write(self.profiles, original)
        store = self.api['ProfileFile'](self.profiles, self.legacy)
        self.assertTrue(store.read_error)
        self.assertFalse(store.write_accounts())
        with open(self.profiles, 'rb') as stream:
            self.assertEqual(stream.read(), original)

    def test_profile_with_a_secret_field_is_treated_as_corrupt(self):
        self.write(self.profiles, json.dumps([dict(id='one', title='Main', email='m@example.com',
                                                  cluster=0, token='synthetic')]).encode('utf-8'))
        store = self.api['ProfileFile'](self.profiles, self.legacy)
        self.assertTrue(store.read_error)
        self.assertEqual(store.accounts, [])

    def test_duplicate_identifiers_are_treated_as_corrupt(self):
        record = dict(id='same', title='Main', email='m@example.com', cluster=0)
        self.write(self.profiles, json.dumps([record, record]).encode('utf-8'))
        self.assertTrue(self.api['ProfileFile'](self.profiles, self.legacy).read_error)

    def test_legacy_file_is_never_opened_or_changed(self):
        legacy = json.dumps([dict(id='old', title='Old', email='old@example.com', password=LEGACY_PASSWORD,
                                  cluster=0)]).encode('utf-8')
        self.write(self.legacy, legacy)
        opened = []
        real_open = builtins.open

        def spy(path, *args, **kwargs):
            opened.append(os.path.basename(str(path)))
            return real_open(path, *args, **kwargs)
        builtins.open = spy
        self.addCleanup(setattr, builtins, 'open', real_open)

        store = self.api['ProfileFile'](self.profiles, self.legacy)
        self.assertTrue(store.legacy_present)
        self.assertEqual(store.accounts, [])
        self.assertFalse(store.read_error)
        store.accounts = [dict(id='new', title='New', email='new@example.com', cluster=0)]
        self.assertTrue(store.write_accounts())
        builtins.open = real_open
        with open(self.legacy, 'rb') as stream:
            self.assertEqual(stream.read(), legacy)
        self.assertNotIn(os.path.basename(self.legacy), opened)
        self.assertNotIn(os.path.basename(self.legacy) + '.bak', opened)

    def test_successful_write_leaves_no_temporary_files(self):
        store = self.api['ProfileFile'](self.profiles, self.legacy)
        store.accounts = [dict(id='one', title='Main', email='m@example.com', cluster=0)]
        self.assertTrue(store.write_accounts())
        leftovers = [name for name in os.listdir(os.path.dirname(self.profiles)) if name.startswith('.driftkings-')]
        self.assertEqual(leftovers, [])

    def test_legacy_passwords_are_not_loaded_into_memory(self):
        self.write(self.legacy, json.dumps([dict(id='old', title='Old', email='old@example.com',
                                                 password=LEGACY_PASSWORD, cluster=0)]).encode('utf-8'))
        store = self.api['ProfileFile'](self.profiles, self.legacy)
        self.assertNotIn(LEGACY_PASSWORD, json.dumps(store.accounts))

    def test_missing_legacy_file_is_reported_as_absent(self):
        self.assertFalse(self.api['ProfileFile'](self.profiles, self.legacy).legacy_present)

    def test_failed_validation_keeps_the_previous_profile_file(self):
        original = json.dumps([dict(id='one', title='Main', email='m@example.com', cluster=0)]).encode('utf-8')
        self.write(self.profiles, original)
        store = self.api['ProfileFile'](self.profiles, self.legacy)
        # A record that would carry a secret must never reach the disk; the old file stays as it was.
        store.accounts = [dict(id='two', title='Other', email='o@example.com', cluster=0, password='synthetic')]
        self.assertFalse(store.write_accounts())
        with open(self.profiles, 'rb') as stream:
            self.assertEqual(stream.read(), original)

    def test_read_error_prevents_deleting_profiles(self):
        accounts = service(self, self.stub_store(read_error=True))
        with self.assertRaises(self.load('core.accounts').AccountError):
            accounts.delete('first')

    def test_failed_write_rolls_back_service_records(self):
        store = Store()
        accounts = service(self, store)
        previous = copy.deepcopy(store.accounts)
        store.saved = False
        with self.assertRaises(self.load('core.accounts').AccountError):
            accounts.save('first', 'Changed', 'other@example.com', 0)
        self.assertEqual(store.accounts, previous)

    def stub_store(self, read_error=False):
        store = Store()
        store.read_error = read_error
        return store


class AccountPresentationTests(RuntimeTest):
    def setUp(self):
        super(AccountPresentationTests, self).setUp()
        self.store = Store()
        self.accounts = service(self, self.store)
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

    def test_payload_never_carries_a_password_field(self):
        payload = self.action('edit', id='first')
        self.assertNotIn('password', payload['editing'])
        self.assertTrue(all('password' not in row for row in payload['accounts']))
        self.assertNotIn('password', json.dumps(payload))

    def test_notices_are_available_to_the_view(self):
        payload = self.action('add')
        self.assertIn('notice', payload['labels'])
        self.assertIn('legacyNotice', payload['labels'])
        self.assertFalse(payload['legacy'])

    def test_legacy_presence_is_reported_without_content(self):
        self.store.legacy_present = True
        payload = self.action('cancel')
        self.assertTrue(payload['legacy'])

    def test_save_ignores_any_password_sent_by_the_client(self):
        self.action('edit', id='first')
        payload = self.action('save', id='first', title='Renamed', email='test@example.com',
                              password='injected', cluster=0)
        self.assertIsNone(payload['editing'])
        self.assertEqual(self.store.accounts[0]['title'], 'Renamed')
        self.assertNotIn('password', self.store.accounts[0])
        self.assertNotIn('injected', json.dumps(self.store.accounts))

    def test_add_creates_a_profile_without_a_password(self):
        self.action('add')
        self.action('save', id='', title='New', email='new@example.com', cluster=0)
        created = self.store.accounts[-1]
        self.assertEqual((created['title'], created['email']), ('New', 'new@example.com'))
        self.assertNotIn('password', created)

    def test_enter_prefills_without_sending_a_password(self):
        calls = []
        self.owner.useAccount = lambda account_id: calls.append(account_id)
        self.action('enter', id='first', autoEnter=True)
        self.assertEqual(calls, ['first'])

    def test_removing_a_profile_leaves_legacy_files_alone(self):
        self.store.legacy_present = True
        self.action('delete', id='first', confirmed=True)
        self.assertEqual(self.store.accounts, [])
        self.assertTrue(self.store.legacy_present)

    def test_cancel_clears_the_editor(self):
        self.action('edit', id='first')
        self.assertIsNone(self.action('cancel')['editing'])

    def test_close_releases_edit_and_ignores_late_actions(self):
        self.action('edit', id='first')
        self.action('close')
        self.assertFalse(self.view.live)
        self.assertIsNone(self.view.editing)
        self.assertIsNone(self.view.controller)
        self.action('delete', id='first', confirmed=True)
        self.assertEqual(len(self.store.accounts), 1)
        self.assertEqual(self.closed, 1)


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

    def test_settings_panel_opens_the_manager_only_in_the_hangar(self):
        self.controller.openManager()
        self.assertIsNone(self.controller.window)
        self.controller.space = 2
        self.controller.openManager()
        window = self.controller.window
        self.assertTrue(window.loaded)
        self.assertFalse(window.launcher)
        self.controller.openManager()
        self.assertIs(self.controller.window, window)

    def test_disposal_of_an_old_login_does_not_close_the_current_login(self):
        result = self.controller.loginDisposed(lambda view: 'native', object())
        self.assertEqual(result, 'native')
        self.assertTrue(self.controller.canLogin())
        self.assertEqual(self.cancelled, [])


class AccountSettingsPageTests(RuntimeTest):
    def test_page_offers_a_button_that_opens_the_manager(self):
        opened = []
        api = source('settings/definitions/components/account_manager.py', {
            'driftkings._constants': self.load('_constants'),
            'driftkings.settings.controls_schema': self.load('settings.controls_schema'),
            'driftkings.settings.definitions.base': module(SectionDefinition=object),
            'driftkings.components.account_manager': module(controller=module(openManager=lambda: opened.append(True))),
        })
        page = api['AccountManagerSettings']()
        page.i18n = {'UI_setting_openManager': 'Manage accounts', 'UI_setting_openManagerInfo': 'Add, edit or delete saved accounts.'}
        self.assertEqual(page.NAME, 'account_manager')
        left, right = page.getControlColumns()
        self.assertEqual(left, [{'type': 'Label', 'text': 'Add, edit or delete saved accounts.', 'button': 'Manage accounts'}])
        self.assertEqual(right, [])
        page.onButtonPress(None, None)
        self.assertEqual(opened, [True])
