# -*- coding: utf-8 -*-
"""Accounts shared by EU and NA clients keep the region they were saved in."""
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

    def write_accounts(self):
        self.writes += 1
        return True


class AccountRegionTests(RuntimeTest):
    def service(self, store, hosts, realm):
        accounts = self.load('core.accounts')
        return accounts, accounts.AccountService(store, lambda text: text, lambda text: text, lambda: hosts, realm)

    def test_automatic_server_account_stays_in_its_region(self):
        store = Store()
        accounts, na = self.service(store, NA, 'NA')
        na.save('', 'Main NA', 'na@example.com', 'secret', 0)
        self.assertEqual(store.accounts[0]['realm'], 'NA')
        self.assertTrue(na.rows()[0]['available'])
        self.assertEqual(na.credentials(store.accounts[0]['id'])[2], AUTO[0])

        _, eu = self.service(store, EU, 'EU')
        row = eu.rows()[0]
        self.assertFalse(row['available'])
        self.assertTrue(row['server'].startswith('NA'))
        with self.assertRaises(accounts.AccountError):
            eu.credentials(store.accounts[0]['id'])

    def test_foreign_account_keeps_server_when_edited_elsewhere(self):
        store = Store()
        _, na = self.service(store, NA, 'NA')
        na.save('', 'Main NA', 'na@example.com', 'secret', 1)
        account_id = store.accounts[0]['id']
        _, eu = self.service(store, EU, 'EU')
        self.assertEqual(eu.edit(account_id)['cluster'], -1)
        eu.save(account_id, 'Renamed', 'na@example.com', '', -1)
        account = store.accounts[0]
        self.assertEqual((account['title'], account['realm'], account['server']),
                         ('Renamed', 'NA', NA[1][0]))
        self.assertEqual(account['password'], 'secret')
        self.assertEqual(na.credentials(account_id)[2], NA[1][0])

    def test_older_records_infer_region_or_require_confirmation(self):
        store = Store([
            {'id': 'eu', 'title': 'EU', 'email': 'e', 'password': 'p', 'cluster': 1, 'server': EU[1][0]},
            {'id': 'na', 'title': 'NA', 'email': 'e', 'password': 'p', 'cluster': 1, 'server': NA[1][0]},
            {'id': 'auto', 'title': 'Auto', 'email': 'e', 'password': 'p', 'cluster': 0, 'server': AUTO[0]},
            {'id': 'index', 'title': 'Index', 'email': 'e', 'password': 'p', 'cluster': 2}])
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
        eu.save('auto', 'Auto', 'e', '', 0)
        self.assertEqual(store.accounts[2]['realm'], 'EU')
        self.assertTrue(eu.rows()[2]['available'])

    def test_unknown_client_region_keeps_previous_behaviour(self):
        store = Store([{'id': 'index', 'title': 'Index', 'email': 'e', 'password': 'p', 'cluster': 0}])
        _, service = self.service(store, EU, '')
        self.assertTrue(service.rows()[0]['available'])
        service.save('', 'New', 'n@example.com', 'p', 1)
        self.assertNotIn('realm', store.accounts[1])

    def test_new_account_requires_a_server(self):
        accounts, eu = self.service(Store(), EU, 'EU')
        with self.assertRaises(accounts.AccountError) as raised:
            eu.save('', 'New', 'n@example.com', 'p', -1)
        self.assertEqual(raised.exception.key, 'errorServer')

    def test_region_error_names_the_region_for_translation(self):
        store = Store([{'id': 'na', 'title': 'NA', 'email': 'e', 'password': 'p', 'cluster': 1,
                        'server': NA[1][0], 'realm': 'NA'}])
        accounts, eu = self.service(store, EU, 'EU')
        with self.assertRaises(accounts.AccountError) as raised:
            eu.credentials('na')
        self.assertEqual((raised.exception.key, raised.exception.values), ('errorRegion', {'realm': 'NA'}))
        self.assertIn('NA client', str(raised.exception))

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
