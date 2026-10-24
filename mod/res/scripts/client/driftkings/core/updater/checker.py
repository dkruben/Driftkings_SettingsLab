# -*- coding: utf-8 -*-
"""GitHub metadata checks only. Never request the WOTMOD download URL."""
from driftkings.core.updater import endpoints, signature
from driftkings.core.updater.manifest import bounded_json, Manifest, MAX_MANIFEST
from driftkings.core.updater.versioning import Version
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Updater')
MAX_RELEASES_RESPONSE = 1024 * 1024


class Checker(object):
    def __init__(self, transport, timeout=15.0):
        if timeout <= 0:
            raise ValueError('Invalid timeout')
        self.transport = transport
        self.timeout = timeout
        self._generation = 0
        self._busy = False
        self._handles = []
        self.selected_manifest = None

    def cancel(self):
        self._generation += 1
        self._busy = False
        handles, self._handles = self._handles, []
        for handle in handles:
            try:
                handle.cancel()
            except Exception:
                LOG.warning('Could not cancel metadata request')

    def check(self, installed, channel, game_version, callback):
        if self._busy:
            return False
        current = Version(installed)
        current.allowed(channel)
        self._busy = True
        self.selected_manifest = None
        self._generation += 1
        generation = self._generation
        candidates, failures = [], []

        def alive():
            return self._busy and generation == self._generation

        def finish(result=None, error=None):
            if not alive():
                return
            self._busy = False
            self._handles = []
            callback(result, error)

        def request(url, maximum, success, raw=False):
            try:
                endpoints.validate_https(url)
                delivered = [False]
                def received(response, error):
                    if not alive() or delivered[0]:
                        return
                    delivered[0] = True
                    if error:
                        finish(error=error if error in ('timeout', 'networkError', 'transportUnavailable') else 'networkError')
                        return
                    try:
                        if response is None or response.status != 200:
                            raise ValueError('httpError')
                        endpoints.validate_https(response.url)
                        value = response.body if raw else bounded_json(response.body, maximum)
                        if raw and (not isinstance(value, bytes) or len(value) > maximum):
                            raise ValueError('invalidBody')
                    except (ValueError, TypeError, AttributeError, UnicodeError):
                        finish(error='invalidResponse')
                        return
                    success(value)
                handle = self.transport.request(url, received, self.timeout, maximum)
                if handle is not None and alive():
                    self._handles.append(handle)
            except Exception:
                LOG.exception('Could not start update metadata request')
                finish(error='networkError')

        def next_manifest(queue):
            if not alive():
                return
            if not queue:
                if candidates:
                    compatible = [item for item in candidates if item.compatible(game_version)]
                    selected = max(compatible or candidates, key=lambda item: item.version)
                    self.selected_manifest = selected
                    finish(dict(latestVersion=selected.version.text, changelog=list(selected.changelog),
                                compatible=selected.compatible(game_version)))
                elif failures:
                    finish(error='invalidManifest')
                else:
                    finish(dict(latestVersion=None, changelog=[], compatible=None))
                return
            release, version, url, sig_url = queue.pop(0)
            def parsed(raw):
                try:
                    manifest = Manifest(bounded_json(raw))
                    if manifest.version.text != version.text or bool(manifest.version.prerelease) != release['prerelease']:
                        raise ValueError('Release metadata disagrees with manifest')
                    if manifest.version.allowed(channel):
                        candidates.append(manifest)
                except (ValueError, TypeError, UnicodeError):
                    failures.append(url)
                next_manifest(queue)
            def loaded(raw):
                if not signature.enforced():
                    parsed(raw)
                    return
                def signed(encoded):
                    try:
                        signature.verify_manifest(raw, encoded)
                    except (ValueError, TypeError):
                        LOG.warning('Rejected release %s: invalid manifest signature', version.text)
                        failures.append(url)
                        next_manifest(queue)
                        return
                    parsed(raw)
                request(sig_url, signature.MAX_SIGNATURE, signed, raw=True)
            request(url, MAX_MANIFEST, loaded, raw=True)

        def releases_loaded(releases):
            if not isinstance(releases, list) or len(releases) > 50:
                finish(error='invalidReleaseList')
                return
            queue = []
            for release in releases:
                try:
                    if not isinstance(release, dict) or type(release.get('draft')) is not bool or type(release.get('prerelease')) is not bool:
                        raise ValueError('Invalid release record')
                    if release['draft']:
                        continue
                    tag = release.get('tag_name', '')
                    version = Version(tag[1:] if tag.startswith('v') else tag)
                    if not version.allowed(channel) or version <= current:
                        continue
                    if bool(version.prerelease) != release['prerelease']:
                        raise ValueError('Invalid prerelease flag')
                    assets = release.get('assets')
                    if not isinstance(assets, list):
                        raise ValueError('Invalid assets')
                    matches = [item for item in assets if isinstance(item, dict) and item.get('name') == 'release.json']
                    if len(matches) != 1:
                        raise ValueError('Missing or ambiguous release manifest')
                    url = endpoints.manifest_asset_url(matches[0].get('browser_download_url'))
                    sig_url = None
                    if signature.enforced():
                        signed = [item for item in assets if isinstance(item, dict) and item.get('name') == signature.SIGNATURE_ASSET]
                        if len(signed) != 1:
                            raise ValueError('Missing or ambiguous manifest signature')
                        sig_url = endpoints.signature_asset_url(signed[0].get('browser_download_url'))
                    queue.append((release, version, url, sig_url))
                except (ValueError, TypeError, AttributeError):
                    failures.append('release')
            queue.sort(key=lambda item: item[1], reverse=True)
            next_manifest(queue)

        request(endpoints.RELEASES, MAX_RELEASES_RESPONSE, releases_loaded)
        return True
