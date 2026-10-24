# -*- coding: utf-8 -*-
"""Statistics boundaries and cache recovery without the game or network."""
import json
import os
import shutil
import tempfile
from support import RuntimeTest, module, source


class StatsTests(RuntimeTest):
    def setUp(self):
        super(StatsTests, self).setUp()
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        self.response = b'{"xwn8": [100, 200]}'
        self.failure = None
        self.network = module(urlopen=self.download)
        store = source('settings/store.py', {})
        filesystem = source('common/utils/filesystem.py', {'driftkings.settings.store': module(**store)})
        self.api = source('stats/vehinfo.py', {
            'urllib2': self.network, 'ResMgr': module(), 'nations': module(NAMES=[]),
            'items': module(vehicles=module()),
            'driftkings.core.callbacks': module(callback=lambda *args: None),
            'driftkings.common.utils.filesystem': module(**filesystem),
            'driftkings.core.cache': module(cache_directory=lambda name: self.directory),
        })
        self.api['open'] = lambda *args, **kwargs: open(*args, **kwargs)
        self.scale = self.api['scaleValuesInstance']
        self.scale._inHangar = lambda: True
        self.api['LOG'] = module(exception=lambda *args: None, warning=lambda *args: None)

    def download(self, url, timeout):
        if self.failure:
            raise self.failure
        pending = [self.response]
        def read(amount=None):
            data = pending.pop(0) if pending else b''
            if amount is not None and len(data) > amount:
                pending.insert(0, data[amount:])
                data = data[:amount]
            return data
        return module(read=read, close=lambda: None)

    def test_scale_endpoints_and_invalid_values(self):
        self.scale.xvmScale_data = {'xwn8': [100, 200]}
        for value, expected in ((0, 0), (99, 0), (100, 1), (199, 1), (200, 100)):
            self.assertEqual(self.scale.calculateXvmScale('wn8', value), expected)
        self.assertEqual(self.scale.calculateXvmScale('missing', 100), -1)
        for value in (None, float('nan'), float('inf')):
            self.assertEqual(self.scale.calculateXvmScale('wn8', value), -1)
        for value, expected in ((None, None), (0, 0.0), (1, '1'), (99, '99'), (100, '100'), (101, '100')):
            self.assertEqual(self.scale.XvmScaleToSup(value), expected)

    def test_invalid_download_preserves_existing_cache(self):
        path = os.path.join(self.directory, 'xvmScales.json')
        original = b'{"xwn8": [5, 10]}'
        with open(path, 'wb') as stream:
            stream.write(original)
        for response in (b'<html>unavailable</html>', b'[]', b'{}'):
            self.response = response
            self.assertFalse(self.scale.loadJsonData('test', path))
            with open(path, 'rb') as stream:
                self.assertEqual(stream.read(), original)
        self.failure = IOError('offline')
        self.scale._loadXvmScaleData()
        self.assertEqual(self.scale.xvmScale_data, {'xwn8': [5, 10]})

    def test_valid_download_and_publish_failure(self):
        path = os.path.join(self.directory, 'xvmScales.json')
        self.assertTrue(self.scale.loadJsonData('test', path))
        with open(path, 'rb') as stream:
            self.assertEqual(json.load(stream), {'xwn8': [100, 200]})
        def fail(path, data):
            raise IOError('disk full')
        self.api['atomicWrite'] = fail
        self.assertFalse(self.scale.loadJsonData('test', path))
        with open(path, 'rb') as stream:
            self.assertEqual(json.load(stream), {'xwn8': [100, 200]})

    def test_truncated_oversized_and_invalid_downloads_keep_cache(self):
        path = os.path.join(self.directory, 'xvmScales.json')
        original = b'{"xwn8": [5, 10]}'
        with open(path, 'wb') as stream:
            stream.write(original)
        class IncompleteRead(Exception):
            """Stands for httplib.IncompleteRead, which is not an IOError in Python 2.7."""
        self.failure = IncompleteRead('partial')
        self.assertFalse(self.scale.loadJsonData('test', path))
        self.failure = None
        self.response = b'{"xwn8": [1]}' + b' ' * (self.api['MAX_DOWNLOAD'] + 1)
        self.assertFalse(self.scale.loadJsonData('test', path))
        self.response = b'{"xwn8": [3, 1]}'
        self.assertFalse(self.scale.loadJsonData('test', path, self.api['valid_xvm_scales']))
        self.response = b'{"xwn8": [1, 3]}'
        self.assertTrue(self.scale.loadJsonData('test', path, self.api['valid_xvm_scales']))
        with open(path, 'rb') as stream:
            self.assertEqual(json.load(stream), {'xwn8': [1, 3]})

    def test_download_deadline_is_enforced(self):
        clock = iter([0.0, 1000.0, 2000.0])
        self.api['time'] = module(time=lambda: next(clock))
        self.assertRaises(IOError, self.scale.download, 'test', 30.0)

    def test_schema_validators(self):
        v = self.api
        self.assertTrue(v['valid_wn8']({'data': [dict(IDNum=1, expDamage=1000, expSpot=1, expWinRate=50, expDef=1, expFrag=1)]}))
        for bad in ({}, {'data': []}, {'data': {}}, []):
            self.assertFalse(v['valid_wn8'](bad))
        self.assertTrue(v['valid_scaled_vehicles']({'1': {'x': [1, 2]}}))
        for bad in ({'1': {'x': [2, 1]}}, {'1': 5}, {}):
            self.assertFalse(v['valid_scaled_vehicles'](bad))
        self.assertFalse(v['valid_xvm_scales']({'xwn8': 'text'}))

    def test_invalid_records_preserve_last_cache(self):
        original = {'data': [dict(IDNum=1, expDamage=1000, expSpot=1, expWinRate=50, expDef=1, expFrag=1)]}
        path = os.path.join(self.directory, 'wn8exp.json')
        with open(path, 'wb') as stream:
            stream.write(json.dumps(original).encode('utf-8'))
        for record in ({}, dict(original['data'][0], expDamage=0), dict(original['data'][0], expFrag=float('nan'))):
            self.response = json.dumps({'data': [record]}).encode('utf-8')
            self.assertFalse(self.scale.loadJsonData('test', path, self.api['valid_wn8']))
            with open(path, 'rb') as stream:
                self.assertEqual(json.load(stream), original)
        self.assertFalse(self.api['valid_xvm_scales']({'xwn8': [1, 2], 'xeff': 'invalid'}))
        self.assertFalse(self.api['valid_scaled_vehicles']({'1': {'x': [1, 2]}, '2': {'x': [2, 1]}}))
        self.assertTrue(self.api['valid_xvm_scales']({'xwn8': [1, 2], 'info': {'version': 1}}))

    def test_wn8_loading_advances_revision(self):
        path = os.path.join(self.directory, 'wn8exp.json')
        record = dict(IDNum=1, expDamage=1000, expSpot=1, expWinRate=50, expDef=1, expFrag=1)
        with open(path, 'wb') as stream:
            stream.write(json.dumps({'data': [record]}).encode('utf-8'))
        self.scale.vehicleInfoData[1] = {}
        revision = self.scale.wn8_revision
        self.scale._loadWn8Data()
        self.assertEqual(self.scale.wn8_revision, revision + 1)
        self.assertEqual(self.scale.vehicleInfoData[1]['wn8expDamage'], 1000)

    def test_invalid_local_wn8_preserves_active_table_and_revision(self):
        record = dict(IDNum=1, expDamage=1000, expSpot=1, expWinRate=50, expDef=1, expFrag=1)
        path = os.path.join(self.directory, 'wn8exp.json')
        self.scale.vehicleInfoData[1] = {}
        with open(path, 'w') as stream:
            json.dump({'data': [record]}, stream)
        self.scale._loadWn8Data()
        revision = self.scale.wn8_revision
        with open(path, 'w') as stream:
            json.dump({'data': [dict(record, expDamage=-1)]}, stream)
        self.scale._loadWn8Data()
        self.assertEqual(self.scale.wn8_revision, revision)
        self.assertEqual(self.scale.vehicleInfoData[1]['wn8expDamage'], 1000)

    def test_replacement_wn8_removes_obsolete_vehicle_expectations(self):
        self.scale.vehicleInfoData[1] = {'wn8expDamage': 999, 'level': 6}
        self.scale.vehicleInfoData[2] = {}
        record = dict(IDNum=2, expDamage=1000, expSpot=1, expWinRate=50, expDef=1, expFrag=1)
        with open(os.path.join(self.directory, 'wn8exp.json'), 'w') as stream:
            json.dump({'data': [record]}, stream)
        self.scale._loadWn8Data()
        self.assertNotIn('wn8expDamage', self.scale.vehicleInfoData[1])
        self.assertEqual(self.scale.vehicleInfoData[1]['level'], 6)
        self.assertEqual(self.scale.vehicleInfoData[2]['wn8expDamage'], 1000)

    def test_download_rejects_read_that_finishes_after_deadline(self):
        clock = iter([0, 0, 31])
        self.api['time'] = module(time=lambda: next(clock))
        self.assertRaises(IOError, self.scale.download, 'test', 30)

    def test_downloads_run_off_the_client_thread_and_are_applied_by_polling(self):
        calls = []
        self.api['callback'] = lambda delay, method: calls.append(method)
        self.scale.config_path = self.directory
        self.response = b'{"xwn8": [100, 200]}'
        # The worker body is synchronous here; the point is that nothing downloads on the client path.
        self.scale._loadXvmScaleData()
        self.assertEqual(self.scale.xvmScale_data, {})
        updated = self.scale._downloadAll()
        self.assertEqual(updated, ['xvmScales.json'])  # other sources fail their schema check
        self.assertFalse(self.scale._updates.empty())
        self.scale._downloading = False
        self.scale._pollDownloads()
        self.assertEqual(self.scale.xvmScale_data, {'xwn8': [100, 200]})
        self.assertEqual(calls, [])

    def test_offline_start_uses_cache_without_blocking(self):
        with open(os.path.join(self.directory, 'xvmScales.json'), 'wb') as stream:
            stream.write(b'{"xwn8": [5, 10]}')
        self.failure = IOError('offline')
        self.assertEqual(self.scale._downloadAll(), [])
        self.scale._loadXvmScaleData()
        self.assertEqual(self.scale.xvmScale_data, {'xwn8': [5, 10]})

    def test_missing_and_degenerate_vehicle_ratings(self):
        self.assertEqual(self.scale.calculateXTE(1, 10, 1), -1)
        for data in ({}, {'ad': 0, 'td': 10, 'af': 0, 'tf': 1, 'x': [10]},
                     {'ad': 10, 'td': 10, 'af': 1, 'tf': 2, 'x': [10]}):
            self.scale.xte_data = {'1': data}
            self.assertEqual(self.scale.calculateXTE(1, 10, 1), -1)
        self.scale.xte_data = {'1': {'ad': 100, 'td': 200, 'af': 1, 'tf': 2, 'x': [500, 1000, 1500]}}
        self.assertEqual(self.scale.calculateXTE(1, 100, 1), 2)
        self.scale.xtdb_data = {'1': {'x': [100, 200]}}
        self.assertEqual(self.scale.calculateXTDB(1, 100), 1)
        self.assertEqual(self.scale.calculateXTDB(1, 200), 100)
        self.scale.xtdb_data = {'1': {'x': [200, 100]}}
        self.assertEqual(self.scale.calculateXTDB(1, 150), -1)

    def test_refresh_waits_for_hangar_and_selects_only_due_table(self):
        now = 200000.0
        self.api['time'] = module(time=lambda: now)
        started = []
        self.api['threading'] = module(Thread=lambda **kwargs: module(
            start=lambda: started.append(self.scale._downloadSources), daemon=False))
        for name, url, validate in self.scale.SOURCES:
            with open(os.path.join(self.directory, name), 'wb') as stream:
                stream.write(b'{}')
            self.scale._refreshState[name] = {'success': now - 100, 'retry': 0}
        self.scale._startDownloads()
        self.assertEqual(started, [])
        self.scale._refreshState['wn8exp.json']['success'] = now - 86400
        self.scale._inHangar = lambda: False
        self.scale._startDownloads()
        self.assertEqual(started, [])
        self.scale._inHangar = lambda: True
        self.scale._startDownloads()
        self.assertEqual([s[0] for s in started[0]], ['wn8exp.json'])

    def test_failure_backoff_is_persisted_and_blocks_early_retry(self):
        now = 200000.0
        self.api['time'] = module(time=lambda: now)
        self.scale._updates.put(('wn8exp.json', False, now))
        self.scale._pollDownloads()
        self.assertEqual(self.scale._refreshState['wn8exp.json']['retry'], now + 1800)
        self.scale._refreshState = {}
        self.scale._loadRefreshState()
        self.assertEqual(self.scale._refreshState['wn8exp.json']['retry'], now + 1800)
        self.scale.SOURCES = tuple(s for s in self.scale.SOURCES if s[0] == 'wn8exp.json')
        started = []
        self.api['threading'] = module(Thread=lambda **kwargs: module(start=lambda: started.append(True)))
        self.scale._startDownloads()
        self.assertEqual(started, [])
        self.api['time'] = module(time=lambda: now + 1800)
        self.scale._startDownloads()
        self.assertEqual(started, [True])

    def test_completed_download_is_applied_only_after_returning_to_hangar(self):
        applied = []
        self.scale.APPLY = {'wn8exp.json': lambda instance: applied.append(True)}
        self.scale._updates.put(('wn8exp.json', True, 12345))
        self.scale._inHangar = lambda: False
        self.scale._pollDownloads()
        self.assertEqual(applied, [])
        self.assertFalse(self.scale._updates.empty())
        self.scale._inHangar = lambda: True
        self.scale._pollDownloads()
        self.assertEqual(applied, [True])
        self.assertEqual(self.scale._refreshState['wn8exp.json']['success'], 12345)

    def test_invalid_local_cache_is_refreshed_even_with_recent_success(self):
        now = 200000.0
        self.api['time'] = module(time=lambda: now)
        self.scale.SOURCES = tuple(s for s in self.scale.SOURCES if s[0] == 'wn8exp.json')
        with open(os.path.join(self.directory, 'wn8exp.json'), 'wb') as stream:
            stream.write(b'{}')
        self.scale._refreshState['wn8exp.json'] = {'success': now - 1}
        self.scale._loadWn8Data()
        started = []
        self.api['threading'] = module(Thread=lambda **kwargs: module(start=lambda: started.append(True)))
        self.scale._startDownloads()
        self.assertEqual(started, [True])

    def test_player_aliases_none_ratings_and_missing_hp(self):
        self.scale.vehicleInfoData[1] = {'level': 6}
        api = source('stats/xvm_stats.py', {'driftkings.stats.vehinfo': module(**self.api)})
        stats = api['xvm_stat']
        value = {'_id': 5, 'b': 10, 'w': 5, 'wn8': None, 'v': None, 'ver': 1,
                 'vehicles': {'bad': {}, '1': {'b': 10, 'w': 5, 'dmg': 1000}}}
        stats._fix_common(value)
        stats._fix_common2(value, 'Player')
        self.assertEqual(value['player_id'], 5)
        self.assertEqual(value['winrate'], 50.0)
        self.assertEqual(value['vehicles']['1']['db'], 100.0)
        self.assertNotIn('dv', value['vehicles']['1'])
        self.assertIsNone(value['wn8'])
        self.assertNotIn('_id', value)
