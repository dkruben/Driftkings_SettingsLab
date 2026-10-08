# -*- coding: utf-8 -*-
"""Account operations independent of the UI; passwords never enter view models."""
import copy
import uuid


class AccountError(ValueError):
    pass


class AccountService(object):
    def __init__(self, store, protect, unprotect, hosts):
        self.store, self.protect, self.unprotect, self.hosts = store, protect, unprotect, hosts

    def find(self, account_id):
        for account in self.store.accounts:
            if str(account['id']) == str(account_id):
                return account
        raise AccountError('Account no longer exists.')

    def cluster(self, account):
        hosts = self.hosts()
        if account.get('server'):
            for index, host in enumerate(hosts):
                if host[0] == account['server']:
                    return index
            return -1
        try:
            index = int(account['cluster'])
        except (ValueError, TypeError, KeyError):
            return -1
        return index if 0 <= index < len(hosts) else -1

    def rows(self):
        hosts = self.hosts()
        rows = []
        for account in self.store.accounts:
            index = self.cluster(account)
            rows.append({'id': str(account['id']), 'title': account['title'],
                         'server': hosts[index][1] if index >= 0 else '-', 'available': index >= 0})
        return rows

    def edit(self, account_id):
        account = self.find(account_id)
        return {'id': str(account['id']), 'title': account['title'],
                'email': self.unprotect(account['email']), 'cluster': self.cluster(account)}

    def _commit(self, accounts):
        if getattr(self.store, 'read_error', False):
            raise AccountError('The accounts file could not be read. The original file was preserved.')
        previous = self.store.accounts
        self.store.accounts = accounts
        try:
            saved = self.store.write_accounts()
        except Exception:
            saved = False
        if not saved:
            self.store.accounts = previous
            raise AccountError('Could not save accounts. The previous file was preserved.')

    def save(self, account_id, title, email, password, cluster):
        title, email = title.strip(), email.strip()
        if not title or not email or (not account_id and not password):
            raise AccountError('Fill in the name, email and password.')
        hosts = self.hosts()
        cluster = int(cluster)
        if not 0 <= cluster < len(hosts):
            raise AccountError('Select an available server.')
        accounts = copy.deepcopy(self.store.accounts)
        original = self.find(account_id) if account_id else None
        account = copy.deepcopy(original) if original else {'id': uuid.uuid4().hex}
        account.update(title=title, email=self.protect(email), cluster=cluster, server=hosts[cluster][0])
        if password:
            account['password'] = self.protect(password)
        if original:
            accounts = [account if str(item['id']) == str(account_id) else item for item in accounts]
        else:
            accounts.append(account)
        self._commit(accounts)

    def delete(self, account_id):
        self.find(account_id)
        self._commit([copy.deepcopy(item) for item in self.store.accounts if str(item['id']) != str(account_id)])

    def credentials(self, account_id):
        account = self.find(account_id)
        index = self.cluster(account)
        if index < 0:
            raise AccountError('Edit this account and select an available server.')
        return self.unprotect(account['email']), self.unprotect(account['password']), self.hosts()[index][0], index
