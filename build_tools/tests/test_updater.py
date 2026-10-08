"""Updater metadata checks: no external network, install or personal config writes."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings import VERSION
from Driftkings.core import Core
from Driftkings.core.updater import UpdaterService
from Driftkings.core.updater.versioning import Version, normalize_game_version
from Driftkings.core.updater.manifest import Manifest, MAX_MANIFEST, MAX_PACKAGE
from Driftkings.core.updater.endpoints import RELEASES, REPOSITORY
from Driftkings.core.updater.checker import Checker
from Driftkings.core.updater.transport import Response
from Driftkings.core.updater.state import State, IDLE, CHECKING, AVAILABLE, ERROR
from Driftkings.settings.panel.api import SettingsAPI
from Driftkings.settings.panel import core_page
from Driftkings.settings.panel.presenter import Presenter


def document(version='1.0.0', **changes):
    value = dict(schema=1, version=version, channel='beta' if '-' in version else 'stable',
                 gameVersion='2.4.0.2', file='Driftkings.wotmod', size=123,
                 sha256='a' * 64, download='https://github.com/' + REPOSITORY + '/releases/download/v' + version + '/Driftkings.wotmod',
                 changelog=['Example change'])
    value.update(changes)
    return value


def release(version='1.0.0', **changes):
    value = dict(tag_name='v' + version, draft=False, prerelease='-' in version,
                 assets=[dict(name='release.json', browser_download_url='https://github.com/' + REPOSITORY + '/releases/download/v' + version + '/release.json')])
    value.update(changes)
    return value


class FakeTransport:
    def __init__(self, releases=None, manifests=None, deferred=False):
        self.releases = releases or []
        self.manifests = manifests or {}
        self.deferred = deferred
        self.calls = []
        self.pending = []
        self.cancelled = 0

    def request(self, url, callback, timeout, max_bytes):
        self.calls.append((url, timeout, max_bytes))
        self.pending.append((url, callback))
        if not self.deferred:
            self.respond()
        return self if self.deferred else None

    def cancel(self):
        self.cancelled += 1

    def respond(self, error=None, status=200, raw=None, final_url=None):
        url, callback = self.pending.pop(0)
        value = self.releases if url == RELEASES else self.manifests[url]
        callback(Response(status, json.dumps(value) if raw is None else raw, final_url or url), error)


class VersionTests(unittest.TestCase):
    def test_official_semver_ordering(self):
        ordered = ['1.0.0-alpha', '1.0.0-alpha.1', '1.0.0-alpha.beta', '1.0.0-beta',
                   '1.0.0-beta.2', '1.0.0-beta.11', '1.0.0-rc.1', '1.0.0', '1.2.3', '2.0.0']
        self.assertEqual(sorted(reversed(ordered), key=Version), ordered)

    def test_build_metadata_has_no_precedence(self):
        self.assertEqual(Version('1.2.3+build.01'), Version('1.2.3+other'))
        self.assertFalse(Version('1.2.3+new') > Version('1.2.3'))

    def test_invalid_versions(self):
        for value in ('1', '1.0', '1.2.3.4', '-1.0.0', '01.0.0', '1.02.0', '1.0.03',
                      '1.0.0-beta.01', '1.0.0-', '1.0.0+', ' arbitrary ', '1.0.0\n', None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Version(value)

    def test_channels(self):
        self.assertTrue(Version('1.2.3').allowed('stable'))
        self.assertTrue(Version('1.2.3').allowed('beta'))
        for value in ('1.2.3-beta.1', '1.2.3-rc.1'):
            self.assertFalse(Version(value).allowed('stable'))
            self.assertTrue(Version(value).allowed('beta'))
        self.assertFalse(Version('1.2.3-dev.1').allowed('beta'))
        with self.assertRaises(ValueError):
            Version('1.2.3').allowed('development')

    def test_game_version_is_separate(self):
        self.assertEqual(normalize_game_version(' v.2.4.0.2 #966 '), '2.4.0.2')
        for value in (None, '', '2.4.0', '2.4.0.2-beta', 'unknown', 'v.2.4.0.2 #build'):
            self.assertIsNone(normalize_game_version(value))

    def test_builder_uses_same_grammar(self):
        spec = importlib.util.spec_from_file_location('build_unified_updater', ROOT / 'build_tools/build_unified.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / 'source/scripts/client/Driftkings/__init__.py'
            target.parent.mkdir(parents=True)
            for value in ('1.2.3-beta.1', '1.2.3-rc.1', '1.2.3+build'):
                target.write_text('VERSION = ' + repr(value))
                self.assertEqual(builder.package_version(root), value)
            target.write_text("VERSION = '1.2.3-beta.01'")
            with self.assertRaises(ValueError):
                builder.package_version(root)


class ManifestTests(unittest.TestCase):
    def test_valid_contract_and_compatibility(self):
        manifest = Manifest.parse(json.dumps(document(sha256='A' * 64)))
        self.assertEqual(manifest.sha256, 'a' * 64)
        self.assertTrue(manifest.compatible('v.2.4.0.2 #966'))
        self.assertFalse(manifest.compatible('2.5.0.0'))
        self.assertFalse(manifest.compatible(None))

    def test_game_range_numeric_not_lexical(self):
        manifest = Manifest(document(minGameVersion='2.4.0.2', maxGameVersion='2.10.0.0'))
        self.assertTrue(manifest.compatible('2.9.0.0'))
        self.assertFalse(manifest.compatible('2.11.0.0'))
        with self.assertRaises(ValueError):
            Manifest(document(minGameVersion='2.5.0.0'))

    def test_missing_and_unknown_fields(self):
        for key in document():
            if key == 'changelog':
                continue
            value = document()
            del value[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                Manifest(value)
        with self.assertRaises(ValueError):
            Manifest(document(command='run'))

    def test_schema_types(self):
        for value in (True, 1.0, '1', 2, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Manifest(document(schema=value))

    def test_size_boundaries(self):
        for value in (1, MAX_PACKAGE):
            self.assertEqual(Manifest(document(size=value)).size, value)
        for value in (True, 0, -1, MAX_PACKAGE + 1, 1.0, '123', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Manifest(document(size=value))

    def test_hash_and_fixed_filename(self):
        for value in ('a' * 63, 'a' * 65, 'g' * 64, None, 123):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Manifest(document(sha256=value))
        for name in ('../Driftkings.wotmod', 'Driftkings.zip', '/Driftkings.wotmod'):
            with self.assertRaises(ValueError):
                Manifest(document(file=name))

    def test_https_host_and_credentials(self):
        for url in ('http://github.com/a', 'file:///a', 'ftp://github.com/a', 'https://evil.test/a',
                    'https://github.com.evil.test/a', 'https://user@github.com/a', 'https://user:pass@github.com/a',
                    'https://github.com:80/a', 'https://github.com:bad/a', 'https://github.com/a\n',
                    'https://github.com/a#fragment', 'https://github.com\\evil.test/a', None):
            with self.subTest(url=url), self.assertRaises(ValueError):
                Manifest(document(download=url))

    def test_changelog_bounds_and_text(self):
        self.assertEqual(len(Manifest(document(changelog=['a' * 500] * 32)).changelog), 32)
        for value in ('text', [1], ['a'] * 51, ['a' * 501], ['a' * 500] * 33, ['\u20ac' * 500] * 11):
            with self.subTest(value=str(value)[:20]), self.assertRaises(ValueError):
                Manifest(document(changelog=value))
        self.assertEqual(Manifest(document(changelog=['<script>text</script>'])).changelog[0], '<script>text</script>')

    def test_manifest_bytes_and_duplicates(self):
        for value in (b' ' * (MAX_MANIFEST + 1), b'not JSON', b'\xff', b'{"schema":1,"schema":1}'):
            with self.assertRaises((ValueError, UnicodeError)):
                Manifest.parse(value)

    def test_channel_and_normalized_game_version(self):
        for values in ({'channel': 'development'}, {'version': '1.0.0-beta.1', 'channel': 'stable'},
                       {'channel': 'beta'}, {'gameVersion': 'v.2.4.0.2 #966'}, {'gameVersion': None}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                Manifest(document(**values))


class CheckerTests(unittest.TestCase):
    def run_check(self, versions=(), installed='0.1.0', channel='stable', game='2.4.0.2', records=None, manifests=None):
        records = [release(value) for value in versions] if records is None else records
        mapping = {item['assets'][0]['browser_download_url']: document(item['tag_name'][1:]) for item in records if item.get('assets')}
        mapping.update(manifests or {})
        transport = FakeTransport(records, mapping)
        results = []
        Checker(transport).check(installed, channel, game, lambda value, error: results.append((value, error)))
        self.assertEqual(len(results), 1)
        self.assertTrue(all(not call[0].endswith('.wotmod') for call in transport.calls))
        return results[0], transport

    def test_no_update_and_no_downgrade(self):
        for versions in ((), ('0.1.0',), ('0.0.1',), ('0.1.0+new',)):
            result, transport = self.run_check(versions)
            self.assertEqual(result, (dict(latestVersion=None, changelog=[], compatible=None), None))
            self.assertEqual(len(transport.calls), 1)

    def test_newer_version(self):
        (result, error), transport = self.run_check(('1.0.0', '1.2.0'))
        self.assertIsNone(error)
        self.assertEqual(result['latestVersion'], '1.2.0')
        self.assertTrue(result['compatible'])
        self.assertEqual(transport.calls[0][2], 1024 * 1024)
        self.assertEqual(transport.calls[1][2], MAX_MANIFEST)

    def test_draft_ignored(self):
        (result, error), transport = self.run_check(records=[release(draft=True)])
        self.assertIsNone(result['latestVersion'])
        self.assertIsNone(error)

    def test_stable_ignores_prerelease(self):
        (result, error), transport = self.run_check(('1.0.0-beta.1', '1.0.0-rc.1'))
        self.assertIsNone(result['latestVersion'])
        self.assertEqual(len(transport.calls), 1)

    def test_beta_considers_prerelease_and_final(self):
        (result, error), transport = self.run_check(('1.0.0-beta.2', '1.0.0-rc.1'), channel='beta')
        self.assertEqual(result['latestVersion'], '1.0.0-rc.1')
        (result, error), transport = self.run_check(('1.0.0-beta.2', '1.0.0'), channel='beta')
        self.assertEqual(result['latestVersion'], '1.0.0')

    def test_incompatible_game_informative(self):
        (result, error), transport = self.run_check(('1.0.0',), game='2.5.0.0')
        self.assertEqual(result['latestVersion'], '1.0.0')
        self.assertFalse(result['compatible'])
        (result, error), transport = self.run_check(('1.0.0',), game=None)
        self.assertFalse(result['compatible'])

    def test_prefer_compatible_release(self):
        url = release('2.0.0')['assets'][0]['browser_download_url']
        (result, error), transport = self.run_check(('1.0.0', '2.0.0'), manifests={url: document('2.0.0', gameVersion='2.5.0.0')})
        self.assertEqual(result['latestVersion'], '1.0.0')

    def test_invalid_manifest_and_version_disagreement(self):
        url = release()['assets'][0]['browser_download_url']
        for value in ({}, document('2.0.0'), document(schema=2)):
            (result, error), transport = self.run_check(('1.0.0',), manifests={url: value})
            self.assertIsNone(result)
            self.assertEqual(error, 'invalidManifest')

    def test_missing_manifest_and_unauthorized_asset(self):
        for record in (release(assets=[]), release(assets=[dict(name='release.json', browser_download_url='https://github.com/other/repo/releases/download/v1/release.json')])):
            (result, error), transport = self.run_check(records=[record])
            self.assertEqual(error, 'invalidManifest')
            self.assertEqual(len(transport.calls), 1)

    def test_failure_timeout_404_limits_and_redirect(self):
        for args in ({'error': 'networkError'}, {'error': 'timeout'}, {'status': 404},
                     {'raw': ' ' * (1024 * 1024 + 1)}, {'final_url': 'http://github.com/a'}):
            transport = FakeTransport(deferred=True)
            results = []
            Checker(transport, timeout=3.0).check('0.1.0', 'stable', '2.4.0.2', lambda *value: results.append(value))
            transport.respond(**args)
            self.assertEqual(len(results), 1)
            self.assertIsNotNone(results[0][1])
            self.assertEqual(transport.calls[0][1], 3.0)

    def test_concurrent_check_and_late_result(self):
        transport = FakeTransport(deferred=True)
        checker, results = Checker(transport), []
        args = ('0.1.0', 'stable', '2.4.0.2', lambda *value: results.append(value))
        self.assertTrue(checker.check(*args))
        self.assertFalse(checker.check(*args))
        checker.cancel()
        transport.respond()
        self.assertEqual(results, [])
        self.assertEqual(transport.cancelled, 1)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.api = SettingsAPI(self.temp.name)
        core_page.install(self.api)
        self.api.client_version = 'v.2.4.0.2 #966'
        self.now = 100.0
        self.transport = FakeTransport()
        self.service = UpdaterService(self.api, self.transport, clock=lambda: self.now, safe_spaces=('login', 'lobby'))
        self.service.start()
        self.addCleanup(self.service.stop)

    def test_login_lobby_interval_and_manual_bypass(self):
        self.service.onContextEntered('login')
        self.assertEqual(len(self.transport.calls), 1)
        self.service.onContextLeft('login')
        self.service.onContextEntered('lobby')
        self.assertEqual(len(self.transport.calls), 1)
        self.service.check(manual=True)
        self.assertEqual(len(self.transport.calls), 2)
        self.now += 4 * 60 * 60
        self.service.onContextEntered('lobby')
        self.assertEqual(len(self.transport.calls), 3)

    def test_battle_does_not_trigger_auto_check(self):
        self.service.onContextEntered('battle')
        self.assertEqual(self.transport.calls, [])
        self.assertTrue(self.service.check(manual=True))

    def test_disable_auto_only_manual_bypasses(self):
        self.api.registry.mods['dk.settings'].values['autoCheckUpdates'] = False
        self.assertFalse(self.service.check())
        self.assertTrue(self.service.check(manual=True))

    def test_stop_invalidates_late_result_and_duplicate_checks(self):
        self.transport.deferred = True
        self.assertTrue(self.service.check(manual=True))
        self.assertEqual(self.service.state.snapshot()['status'], CHECKING)
        self.assertFalse(self.service.check(manual=True))
        self.service.stop()
        self.transport.respond()
        self.assertEqual(self.service.state.snapshot()['status'], IDLE)
        self.assertIsNone(self.api.updater)

    def test_stop_from_observer_prevents_request_start(self):
        def close_when_checking():
            if self.service.state.snapshot()['status'] == CHECKING:
                self.service.stop()
        self.service.state.subscribe(close_when_checking)
        self.assertFalse(self.service.check(manual=True))
        self.assertEqual(self.transport.calls, [])
        self.assertEqual(self.service.state.snapshot()['status'], IDLE)

    def test_state_observers_and_read_only_presenter(self):
        observations = []
        self.service.state.subscribe(lambda: observations.append(self.service.state.snapshot()))
        presenter = Presenter(self.api)
        self.addCleanup(presenter.dispose)
        presenter.handle({'action': 'check_updates'})
        self.assertEqual(len(observations), 2)
        snapshot = presenter.state()['updater']
        self.assertEqual(snapshot['installedVersion'], VERSION)
        snapshot['changelog'].append('tamper')
        self.assertEqual(self.service.state.snapshot()['changelog'], [])

    def test_only_preferences_in_config_no_runtime_persistence(self):
        before = {path.name: path.read_bytes() for path in Path(self.temp.name).rglob('*') if path.is_file()}
        self.service.check(manual=True)
        after = {path.name: path.read_bytes() for path in Path(self.temp.name).rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        values = self.api.registry.mods['dk.settings'].values
        self.assertTrue(values['autoCheckUpdates'])
        self.assertEqual(values['updateChannel'], 'stable')
        for key in ('status', 'lastCheck', 'lastResult', 'downloadPercent', 'error'):
            self.assertNotIn(key, values)

    def test_channel_change_cancels_old_result(self):
        self.transport.deferred = True
        self.service.check(manual=True)
        self.api.registry.mods['dk.settings'].values['updateChannel'] = 'beta'
        self.service._preferences_changed({'updateChannel': 'beta'})
        self.transport.respond()
        self.assertEqual(self.service.state.snapshot()['channel'], 'beta')
        self.assertEqual(self.service.state.snapshot()['status'], IDLE)

    def test_unavailable_runtime_transport_has_clear_manual_error(self):
        service = UpdaterService(self.api, safe_spaces=('login', 'lobby'))
        service.start()
        self.addCleanup(service.stop)
        self.assertFalse(service.check())
        service.check(manual=True)
        self.assertEqual(service.state.snapshot()['status'], ERROR)
        self.assertEqual(service.state.snapshot()['error'], 'transportUnavailable')

    def test_explicit_core_services_unchanged(self):
        core = Core(names=(), services=(self.service,), context_factory=None)
        self.assertEqual(core.services, (self.service,))

    def test_installer_states_are_explicit_and_unknown_states_remain_invalid(self):
        state = State()
        state.update(status='INSTALLING')
        self.assertEqual(state.snapshot()['status'], 'INSTALLING')
        state.update(status='RESTART_REQUIRED')
        with self.assertRaises(ValueError):
            state.update(status='INSTALLED')


if __name__ == '__main__':
    unittest.main()
