# -*- coding: utf-8 -*-
"""Official update policy; remote manifests cannot change these endpoints."""
try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

from Driftkings.core.updater.versioning import TEXT

REPOSITORY = 'dkruben/Driftkings_SettingsLab'
RELEASES = 'https://api.github.com/repos/' + REPOSITORY + '/releases?per_page=50'
ALLOWED_HOSTS = frozenset(('github.com', 'api.github.com',
                         'release-assets.githubusercontent.com',
                         'objects.githubusercontent.com', 'github-releases.githubusercontent.com'))


def validate_https(url):
    if not isinstance(url, TEXT) or not url or any(ord(char) <= 32 or ord(char) >= 127 for char in url):
        raise ValueError('Invalid HTTPS URL')
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.hostname not in ALLOWED_HOSTS or
            parts.username is not None or parts.password is not None or
            parts.port not in (None, 443) or parts.fragment or '\\' in url):
        raise ValueError('Unauthorized HTTPS URL')
    return url


def manifest_asset_url(url):
    validate_https(url)
    parts = urlsplit(url)
    if parts.hostname != 'github.com' or not parts.path.startswith('/' + REPOSITORY + '/releases/download/'):
        raise ValueError('Manifest asset outside official repository')
    if not parts.path.endswith('/release.json'):
        raise ValueError('Not a release manifest asset')
    return url
