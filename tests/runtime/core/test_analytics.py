# -*- coding: utf-8 -*-
"""Opt-in analytics: nothing happens before consent, nothing personal is sent, errors are reported by type."""
import json
import logging
import os
import re
import shutil
import tempfile
import threading
import time

from support import RuntimeTest, source

MEASUREMENT = 'G-TEST123456'
SECRET = 'test_secret_value'
LOGGER = logging.getLogger('Driftkings.AnalyticsTest')


class Callbacks(object):
    def __init__(self):
        self.scheduled, self.cancelled = [], []

    def schedule(self, delay, method, *args, **kwargs):
        self.scheduled.append((delay, method))
        return len(self.scheduled)

    def cancel(self, token):
        self.cancelled.append(token)


class Api(object):
    def __init__(self, enabled=False):
        self.values = {'analytics': enabled}

    def get(self, mod_id, setting_id, default=None):
        assert mod_id == 'dk.settings'
        return self.values.get(setting_id, default)


class Response(object):
    def read(self, size=-1):
        return b''

    def close(self):
        pass


class Opener(object):
    def __init__(self, fail=False):
        self.requests, self.fail = [], fail
        self.lock = threading.Lock()

    def open(self, request, timeout=None):
        if self.fail:
            raise IOError('offline')
        with self.lock:
            self.requests.append((request.get_full_url(), json.loads(request.data.decode('utf-8'))))
        return Response()

    def events(self):
        with self.lock:
            return [event for url, body in self.requests for event in body['events']]


def wait_for(condition, seconds=5.0):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return condition()


def write_file(path, data):
    with open(path, 'wb') as stream:
        stream.write(data)


def raise_and_log():
    try:
        raise ValueError('private player name Example_Player')
    except ValueError:
        LOGGER.exception('could not process Example_Player')


class AnalyticsTests(RuntimeTest):
    def setUp(self):
        super(AnalyticsTests, self).setUp()
        self.module = self.load('core.analytics')
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.api, self.callbacks, self.opener = Api(), Callbacks(), Opener()
        self.listeners, self.replay = [], [False]

    def service(self, **options):
        values = dict(api=self.api, callbacks=self.callbacks, opener_factory=lambda: self.opener, root=self.root,
                      environment=lambda: {'realm': 'EU', 'game_version': '2.4.1.0'}, replay=lambda: self.replay[0],
                      listen=self.listeners.append, unlisten=self.listeners.remove, clock=lambda: 1700000000.4,
                      measurement_id=MEASUREMENT, api_secret=SECRET,
                      write=write_file)
        values.update(options)
        service = self.module.AnalyticsService(**values)
        self.addCleanup(service.stop)
        return service

    def identity(self):
        return os.path.join(self.root, 'analytics_id')

    def test_configuration_requires_valid_ids(self):
        configured = self.module.configured
        self.assertTrue(configured(MEASUREMENT, SECRET))
        for measurement, secret in (('', ''), ('G-TEST123456', ''), ('', SECRET), ('UA-1234-1', SECRET),
                                    (MEASUREMENT, 'bad secret&x=1'), (MEASUREMENT, 'short')):
            self.assertFalse(configured(measurement, secret))
        original = self.module.MEASUREMENT_ID, self.module.API_SECRET
        try:
            self.module.MEASUREMENT_ID, self.module.API_SECRET = '', ''
            self.assertFalse(configured())
            self.module.MEASUREMENT_ID, self.module.API_SECRET = MEASUREMENT, SECRET
            self.assertTrue(configured())
        finally:
            self.module.MEASUREMENT_ID, self.module.API_SECRET = original

    def test_off_by_default_stores_and_sends_nothing(self):
        service = self.service()
        service.start()
        self.assertIsNone(service.sender)
        self.assertFalse(os.path.exists(self.identity()))
        self.assertEqual(self.callbacks.scheduled, [])
        self.assertEqual(self.opener.requests, [])

    def test_unconfigured_build_ignores_the_switch(self):
        self.api.values['analytics'] = True
        service = self.service(measurement_id='', api_secret='')
        service.start()
        self.assertIsNone(service.sender)
        self.assertEqual(self.listeners, [])
        self.assertFalse(os.path.exists(self.identity()))

    def test_enabling_sends_anonymous_start_event_and_schedules_heartbeat(self):
        service = self.service()
        service.start()
        service.changed({'analytics': True})
        self.assertTrue(wait_for(lambda: self.opener.events()))
        url, body = self.opener.requests[0]
        self.assertEqual(url, 'https://www.google-analytics.com/mp/collect?measurement_id=%s&api_secret=%s' % (MEASUREMENT, SECRET))
        with open(self.identity(), 'rb') as stream:
            stored = stream.read().decode('ascii')
        self.assertTrue(re.match(r'\A[0-9a-f]{32}\Z', stored))
        self.assertEqual(body['client_id'], '%d.%d' % (int(stored[:16], 16), int(stored[16:], 16)))
        self.assertTrue(re.match(r'\A[0-9]+\.[0-9]+\Z', body['client_id']))
        event = body['events'][0]
        self.assertEqual(event['name'], 'mod_loaded')
        self.assertEqual(event['params'], {'mod_version': '1.0.0', 'session_id': 1700000000, 'engagement_time_msec': 100,
                                           'realm': 'EU', 'game_version': '2.4.1.0'})
        self.assertEqual([delay for delay, method in self.callbacks.scheduled], [60.0])

    def test_heartbeat_reports_engagement_and_reschedules(self):
        service = self.service()
        service.start()
        service.changed({'analytics': True})
        delay, method = self.callbacks.scheduled[0]
        method()
        self.assertEqual(len(self.callbacks.scheduled), 2)
        self.assertTrue(wait_for(lambda: len(self.opener.events()) == 2))
        beat = self.opener.events()[1]
        self.assertEqual(beat['name'], 'heartbeat')
        self.assertEqual(beat['params']['engagement_time_msec'], 60000)

    def test_existing_identity_is_reused_and_garbage_is_replaced(self):
        with open(self.identity(), 'wb') as stream:
            stream.write(b'0123456789abcdef0123456789abcdef\n')
        service = self.service()
        self.assertEqual(service.identity(), '0123456789abcdef0123456789abcdef')
        with open(self.identity(), 'wb') as stream:
            stream.write(b'not an id')
        replacement = service.identity()
        self.assertTrue(re.match(r'\A[0-9a-f]{32}\Z', replacement))
        self.assertNotEqual(replacement, 'not an id')

    def test_disabling_forgets_the_identity_and_stops_everything(self):
        service = self.service()
        service.start()
        service.changed({'analytics': True})
        self.assertTrue(os.path.exists(self.identity()))
        handlers = len(logging.getLogger('Driftkings').handlers)
        sender = service.sender
        service.changed({'analytics': False})
        self.assertFalse(os.path.exists(self.identity()))
        self.assertIsNone(service.sender)
        self.assertEqual(self.callbacks.cancelled, [1])
        self.assertEqual(len(logging.getLogger('Driftkings').handlers), handlers - 1)
        # stop() is nonblocking: an already-started in-memory request may finish.
        # Drain that worker before checking that disabled tracking adds no events.
        sender.thread.join(5.0)
        self.assertFalse(sender.thread.is_alive())
        before = len(self.opener.events())
        service.track('mod_loaded')
        self.assertEqual(len(self.opener.events()), before)

    def test_stop_keeps_the_identity_of_an_opted_in_player(self):
        service = self.service()
        service.start()
        service.changed({'analytics': True})
        service.stop()
        self.assertTrue(os.path.exists(self.identity()))
        self.assertEqual(self.listeners, [])

    def test_opted_in_player_is_enabled_at_startup_but_replays_are_skipped(self):
        self.api.values['analytics'] = True
        self.replay[0] = True
        service = self.service()
        service.start()
        self.assertIsNone(service.sender)
        self.assertFalse(os.path.exists(self.identity()))
        self.replay[0] = False
        second = self.service()
        second.start()
        self.assertIsNotNone(second.sender)

    def test_unwritable_identity_keeps_statistics_off(self):
        def refuse(path, data):
            raise IOError('read-only')
        service = self.service(write=refuse)
        service.start()
        service.changed({'analytics': True})
        self.assertIsNone(service.sender)

    def test_logged_exceptions_are_reported_by_type_and_location_only(self):
        service = self.service()
        service.start()
        service.changed({'analytics': True})
        for _ in range(3):
            raise_and_log()
        self.assertTrue(wait_for(lambda: [e for e in self.opener.events() if e['name'] == 'exception']))
        time.sleep(0.05)
        errors = [e for e in self.opener.events() if e['name'] == 'exception']
        self.assertEqual(len(errors), 1)    # the same place is reported once per session
        params = errors[0]['params']
        self.assertEqual(params['error_type'], 'ValueError')
        self.assertEqual(params['error_file'], 'test_analytics.py')
        self.assertEqual(params['error_function'], 'raise_and_log')
        self.assertEqual(params['error_channel'], 'AnalyticsTest')
        self.assertEqual(params['fatal'], 0)
        self.assertNotIn('Example_Player', json.dumps(self.opener.events()))
        self.assertTrue(all(len(value) <= 100 for value in params.values() if hasattr(value, 'upper')))

    def test_distinct_errors_are_capped_and_own_logger_is_ignored(self):
        service = self.service()
        service.start()
        service.changed({'analytics': True})
        for index in range(self.module.MAX_ERRORS + 10):
            service.report('Driftkings.Channel%d' % index, KeyError, None)
        own = logging.getLogger(self.module.LOG.name)
        try:
            raise RuntimeError('delivery trouble')
        except RuntimeError:
            own.error('analytics failure', exc_info=True)
        self.assertTrue(wait_for(lambda: len(self.opener.events()) > self.module.MAX_ERRORS))
        time.sleep(0.05)
        reported = [e for e in self.opener.events() if e['name'] == 'exception']
        self.assertEqual(len(reported), self.module.MAX_ERRORS)
        self.assertNotIn('RuntimeError', json.dumps(reported))

    def test_sender_pauses_after_repeated_delivery_failures(self):
        self.opener.fail = True
        sender = self.module.Sender('https://example.invalid/', 'a' * 32, lambda: self.opener)
        sender.start()
        self.addCleanup(sender.stop)
        for expected in range(1, self.module.MAX_FAILURES + 1):
            sender.post({'name': 'heartbeat', 'params': {}})
            self.assertTrue(wait_for(lambda: sender.failures == expected or sender.closed.is_set()))
        self.assertTrue(wait_for(sender.closed.is_set))

    def test_parameters_are_clean_for_ga4(self):
        values = self.module.clean({'a' * 50: 1, 'flag': True, 'text': 'x' * 300, 'none': None, 'ratio': 1.5})
        self.assertEqual(sorted(values), ['a' * 40, 'flag', 'ratio', 'text'])
        self.assertEqual(values['flag'], 1)
        self.assertEqual(len(values['text']), 100)

    def test_runtime_registers_the_service_after_the_settings_panel(self):
        specs = dict((spec.name, spec) for spec in source('core/__init__.py', {})['default_services']())
        self.assertEqual(specs['analytics'].requires, ('settings_panel', 'callbacks'))
        self.assertEqual(specs['analytics'].phase, 'interface')
