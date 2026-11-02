# -*- coding: utf-8 -*-
"""Account operations independent of the UI; passwords never enter view models."""
import copy
import uuid

from driftkings.logger import get_logger

LOG = get_logger('Driftkings.AccountManager')

# Records written before regions were stored only have a login URL. The automatic
# server URL is identical in every region, so it cannot identify one.
REALM_DOMAINS = (('worldoftanks.eu', 'EU'), ('worldoftanks.com', 'NA'), ('worldoftanks.asia', 'ASIA'))
READ_ERROR = 'The accounts file could not be read. The original file was preserved.'


class AccountError(ValueError):
    """Names its translation key; the English text is the fallback."""
    def __init__(self, key, text, **values):
        super(AccountError, self).__init__(text.format(**values))
        self.key, self.values = key, values


class AccountService(object):
    def __init__(self, store, protect, unprotect, hosts, realm=''):
        self.store, self.protect, self.unprotect, self.hosts = store, protect, unprotect, hosts
        # EU, NA and ASIA clients share the preferences folder, and therefore this file.
        self.realm = realm

    def find(self, account_id):
        for account in self.store.accounts:
            if str(account['id']) == str(account_id):
                return account
        raise AccountError('errorMissing', 'Account no longer exists.')

    def _index(self, account, hosts):
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

    def accountRealm(self, account, hosts=None):
        """Region of the account, or None when an older record cannot tell."""
        if account.get('realm'):
            return account['realm']
        server = account.get('server')
        if not server:
            return None
        if any(host[0] == server and host[3] is not None for host in hosts or self.hosts()):
            return self.realm or None
        name = server.split(':')[0].lower()
        for domain, realm in REALM_DOMAINS:
            if name == domain or name.endswith('.' + domain):
                return realm
        return None

    def foreign(self, account, hosts=None):
        realm = self.accountRealm(account, hosts)
        return bool(self.realm) and realm is not None and realm != self.realm

    def cluster(self, account):
        hosts = self.hosts()
        if self.realm and self.accountRealm(account, hosts) != self.realm:
            return -1
        return self._index(account, hosts)

    def rows(self):
        hosts = self.hosts()
        rows = []
        for account in self.store.accounts:
            realm = self.accountRealm(account, hosts)
            index = self._index(account, hosts)
            server = hosts[index][1] if index >= 0 else '-'
            if self.foreign(account, hosts):
                server = realm + (u' · ' + account['serverName'] if account.get('serverName') else '')
            elif self.realm and realm is None:
                # Unconfirmed region: saving the account in this client assigns it.
                server += ' (?)'
            rows.append({'id': str(account['id']), 'title': account['title'], 'server': server,
                         'available': self.cluster(account) >= 0})
        return rows

    def edit(self, account_id):
        account = self.find(account_id)
        hosts = self.hosts()
        index = -1 if self.foreign(account, hosts) else self._index(account, hosts)
        return {'id': str(account['id']), 'title': account['title'], 'email': self.unprotect(account['email']),
                'cluster': index}

    def _commit(self, accounts):
        if getattr(self.store, 'read_error', False):
            raise AccountError('errorRead', READ_ERROR)
        previous = self.store.accounts
        self.store.accounts = accounts
        try:
            saved = self.store.write_accounts()
        except Exception as error:
            # Type name only: the message or traceback could carry e-mail addresses or passwords.
            LOG.warning('Could not save accounts (%s); credentials are not logged', type(error).__name__)
            saved = False
        if not saved:
            self.store.accounts = previous
            raise AccountError('errorSave', 'Could not save accounts. The previous file was preserved.')

    def save(self, account_id, title, email, password, cluster):
        title, email = title.strip(), email.strip()
        if not title or not email or (not account_id and not password):
            raise AccountError('errorRequired', 'Fill in the name, email and password.')
        hosts = self.hosts()
        cluster = int(cluster)
        accounts = copy.deepcopy(self.store.accounts)
        original = self.find(account_id) if account_id else None
        account = copy.deepcopy(original) if original else {'id': uuid.uuid4().hex}
        if 0 <= cluster < len(hosts):
            account.update(cluster=cluster, server=hosts[cluster][0], serverName=hosts[cluster][1])
            if self.realm:
                account['realm'] = self.realm
        elif not (original and self.foreign(original, hosts)):
            raise AccountError('errorServer', 'Select an available server.')
        # Without a new selection, an account of another region keeps its server.
        account.update(title=title, email=self.protect(email))
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
            if self.foreign(account):
                raise AccountError('errorRegion', 'This account belongs to the {realm} region. Use the {realm} client.',
                                   realm=self.accountRealm(account))
            raise AccountError('errorEditServer', 'Edit this account and select an available server.')
        return self.unprotect(account['email']), self.unprotect(account['password']), self.hosts()[index][0], index
