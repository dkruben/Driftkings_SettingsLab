import hashlib

BASE = 'https://github.com/dkruben/Driftkings_SettingsLab/releases/download/'


def manifest(version='1.1.0', data=b'package'):
    return dict(schema=1, version=version, channel='beta' if '-' in version else 'stable',
                gameVersion='2.4.1.0', file='driftkings.wotmod', size=len(data),
                sha256=hashlib.sha256(data).hexdigest(), download=BASE + 'v' + version + '/driftkings.wotmod')
