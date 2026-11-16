# -*- coding: utf-8 -*-
"""Account profiles shared by EU and NA clients keep the region they were saved in. Synthetic data only."""
import io
import os
import re

from support import CLIENT, ROOT, RuntimeTest

AUTO = ('auto.login.app:0000', 'Auto', 0, None)
EU = [AUTO, ('login.p1.worldoftanks.eu:20016', 'WOT EU1', 0, 201), ('login.p2.worldoftanks.eu:20016', 'WOT EU2', 0, 202)]
NA = [AUTO, ('login.p7.worldoftanks.com:20016', 'WOT NA East', 0, 307)]


class Store(object):
    def __init__(self, accounts=None):
        self.accounts = accounts or []
        self.writes = 0
        self.saved = True
        self.read_error = False
        self.legacy_present = False

    def write_accounts(self):
        self.writes += 1
        return self.saved


class AccountRegionTests(RuntimeTest):
    def service(self, store, hosts, realm):
        accounts = self.load('core.accounts')
        return accounts, accounts.AccountService(store, lambda: hosts, realm)

    def test_automatic_server_account_stays_in_its_region(self):
        store = Store()
        accounts, na = self.service(store, NA, 'NA')
        na.save('', 'Main NA', 'na@example.com', 0)
        self.assertEqual(store.accounts[0]['realm'], 'NA')
        self.assertTrue(na.rows()[0]['available'])
        self.assertEqual(na.credentials(store.accounts[0]['id'])[1], AUTO[0])

        _, eu = self.service(store, EU, 'EU')
        row = eu.rows()[0]
        self.assertFalse(row['available'])
        self.assertTrue(row['server'].startswith('NA'))
        with self.assertRaises(accounts.AccountError):
            eu.credentials(store.accounts[0]['id'])

    def test_foreign_account_keeps_server_when_edited_elsewhere(self):
        store = Store()
        _, na = self.service(store, NA, 'NA')
        na.save('', 'Main NA', 'na@example.com', 1)
        account_id = store.accounts[0]['id']
        _, eu = self.service(store, EU, 'EU')
        self.assertEqual(eu.edit(account_id)['cluster'], -1)
        eu.save(account_id, 'Renamed', 'na@example.com', -1)
        account = store.accounts[0]
        self.assertEqual((account['title'], account['realm'], account['server']),
                         ('Renamed', 'NA', NA[1][0]))
        self.assertEqual(na.credentials(account_id)[1], NA[1][0])

    def test_failed_save_logs_only_the_error_type(self):
        records = self.capture_log('Driftkings.AccountManager')

        class FailingStore(Store):
            def write_accounts(self):
                raise IOError('cannot write na@example.com')
        store = FailingStore()
        accounts, na = self.service(store, NA, 'NA')
        with self.assertRaises(accounts.AccountError) as raised:
            na.save('', 'Main NA', 'na@example.com', 1)
        self.assertEqual(raised.exception.key, 'errorSave')
        self.assertEqual(store.accounts, [])
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.levelname, 'WARNING')
        self.assertIsNone(record.exc_info)
        self.assertEqual(record.args, (type(IOError()).__name__,))
        message = record.getMessage()
        for secret in ('na@example.com', 'Main NA', 'cannot write'):
            self.assertNotIn(secret, message)

    def test_older_records_infer_region_or_require_confirmation(self):
        store = Store([
            {'id': 'eu', 'title': 'EU', 'email': 'e@example.com', 'cluster': 1, 'server': EU[1][0]},
            {'id': 'na', 'title': 'NA', 'email': 'e@example.com', 'cluster': 1, 'server': NA[1][0]},
            {'id': 'auto', 'title': 'Auto', 'email': 'e@example.com', 'cluster': 0, 'server': AUTO[0]},
            {'id': 'index', 'title': 'Index', 'email': 'e@example.com', 'cluster': 2}])
        accounts, eu = self.service(store, EU, 'EU')
        rows = dict((row['id'], row) for row in eu.rows())
        self.assertTrue(rows['eu']['available'])
        self.assertEqual((rows['na']['available'], rows['na']['server']), (False, 'NA'))
        for name in ('auto', 'index'):
            self.assertFalse(rows[name]['available'])
            self.assertTrue(rows[name]['server'].endswith('(?)'))
            with self.assertRaises(accounts.AccountError):
                eu.credentials(name)
        # Saving an unconfirmed record from its own client assigns the region.
        self.assertEqual(eu.edit('auto')['cluster'], 0)
        eu.save('auto', 'Auto', 'e@example.com', 0)
        self.assertEqual(store.accounts[2]['realm'], 'EU')
        self.assertTrue(eu.rows()[2]['available'])

    def test_unknown_client_region_keeps_previous_behaviour(self):
        store = Store([{'id': 'index', 'title': 'Index', 'email': 'e@example.com', 'cluster': 0}])
        _, service = self.service(store, EU, '')
        self.assertTrue(service.rows()[0]['available'])
        service.save('', 'New', 'n@example.com', 1)
        self.assertNotIn('realm', store.accounts[1])

    def test_new_account_requires_a_server(self):
        accounts, eu = self.service(Store(), EU, 'EU')
        with self.assertRaises(accounts.AccountError) as raised:
            eu.save('', 'New', 'n@example.com', -1)
        self.assertEqual(raised.exception.key, 'errorServer')

    def test_profile_needs_a_name_and_an_email_only(self):
        accounts, eu = self.service(Store(), EU, 'EU')
        for title, email in (('', 'n@example.com'), ('New', ''), ('New', 'not-an-email'), ('x' * 61, 'n@example.com')):
            with self.assertRaises(accounts.AccountError) as raised:
                eu.save('', title, email, 1)
            self.assertEqual(raised.exception.key, 'errorRequiredProfile')

    def test_region_error_names_the_region_for_translation(self):
        store = Store([{'id': 'na', 'title': 'NA', 'email': 'e@example.com', 'cluster': 1,
                        'server': NA[1][0], 'realm': 'NA'}])
        accounts, eu = self.service(store, EU, 'EU')
        with self.assertRaises(accounts.AccountError) as raised:
            eu.credentials('na')
        self.assertEqual((raised.exception.key, raised.exception.values), ('errorRegion', {'realm': 'NA'}))
        self.assertIn('NA client', str(raised.exception))

    def test_credentials_never_contain_a_password(self):
        store = Store([{'id': 'one', 'title': 'Main', 'email': 'm@example.com', 'cluster': 1,
                        'server': NA[1][0], 'realm': 'NA'}])
        _, na = self.service(store, NA, 'NA')
        result = na.credentials('one')
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 'm@example.com')

    def test_every_account_error_key_has_english_text(self):
        with io.open(os.path.join(ROOT, 'mod', 'res', 'mods', 'driftkings', 'text', 'en.yml'), encoding='utf-8') as stream:
            catalog = stream.read()
        keys = set()
        for relative in ('core/accounts.py', 'components/account_manager.py'):
            with io.open(os.path.join(CLIENT, *relative.split('/')), encoding='utf-8') as stream:
                keys.update(re.findall(r"AccountError\('(\w+)'", stream.read()))
        self.assertTrue(keys)
        for key in keys:
            self.assertIn('\naccount_manager.UI_setting_%s: ' % key, catalog)
