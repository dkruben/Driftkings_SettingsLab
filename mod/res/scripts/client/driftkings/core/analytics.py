# -*- coding: utf-8 -*-
"""Opt-in, anonymous usage statistics through the GA4 Measurement Protocol.

Nothing is created, stored or sent until the player turns the switch on in the
Driftkings settings. Events carry a random installation id (never an account or
player name), the mod and game versions and the realm. Errors are reported by
exception type and source location only, never by message text.
"""
import json
import logging
import os
import re
import threading
import time
import uuid

try:
    from Queue import Empty, Full, Queue
    import urllib2 as http
except ImportError:
    from queue import Queue, Empty, Full
    import urllib.request as http

from driftkings import VERSION
from driftkings._constants import SETTINGS_MOD_ID as SETTINGS
from driftkings.logger import get_logger, NAMESPACE

LOG = get_logger('Driftkings.Analytics')

# Fill in before a release. The API secret ships inside the mod, so it is public
# by nature: GA4 accepts writes only, but anyone could send fake events with it.
MEASUREMENT_ID = 'G-B7Z425MJ3L'
API_SECRET = 'SD2sbCSKQACB-ILu408-EA'

ENDPOINT = 'https://www.google-analytics.com/mp/collect?measurement_id=%s&api_secret=%s'
OPTION = 'analytics'
IDENTITY = 'analytics_id'
HEARTBEAT = 60.0
TIMEOUT = 5.0
BATCH = 25          # GA4 accepts at most 25 events per request
BACKLOG = 100       # events waiting for the worker; the game thread never blocks
MAX_ERRORS = 20     # distinct errors reported per session
MAX_FAILURES = 3    # consecutive delivery failures before the session stops sending
TEXT_LIMIT = 100    # GA4 truncates longer parameter values

_MEASUREMENT = re.compile(r'\AG-[A-Z0-9]{4,20}\Z')
_SECRET = re.compile(r'\A[A-Za-z0-9_-]{8,64}\Z')
_IDENTITY = re.compile(r'\A[0-9a-f]{32}\Z')


def configured(measurement_id=None, api_secret=None):
    measurement_id = MEASUREMENT_ID if measurement_id is None else measurement_id
    api_secret = API_SECRET if api_secret is None else api_secret
    return bool(_MEASUREMENT.match(measurement_id) and _SECRET.match(api_secret))


class NoRedirects(http.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verified_opener():
    """Certificate-verified HTTPS without implicit proxies or redirects."""
    import ssl
    context = ssl.create_default_context()
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname or not context.get_ca_certs():
        raise ValueError('Verified TLS unavailable')
    return http.build_opener(http.ProxyHandler({}), NoRedirects(), http.HTTPSHandler(context=context))


def default_environment():
    result = {}
    try:
        from realm import CURRENT_REALM
        result['realm'] = str(CURRENT_REALM)
    except Exception:
        pass
    try:
        from helpers import getClientVersion

        from driftkings.core.updater.versioning import normalize_game_version
        version = normalize_game_version(getClientVersion())
        if version:
            result['game_version'] = version
    except Exception:
        pass
    return result


def clean(values):
    """Keep GA4-compatible parameters only: short names, text or numbers."""
    result = {}
    for key, value in values.items():
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, (int, float)):
            result[key[:40]] = value
        elif value is not None:
            result[key[:40]] = ('%s' % (value,))[:TEXT_LIMIT]
    return result


class Sender(object):
    """One daemon worker delivers batches; callers only ever do a non-blocking put."""

    def __init__(self, url, client_id, opener_factory=None):
        self.url = url
        # Keep the stored random identity, but use GA4's numeric wire format.
        self.client_id = '%d.%d' % (int(client_id[:16], 16), int(client_id[16:], 16))
        self.opener_factory = opener_factory or verified_opener
        self.queue = Queue(BACKLOG)
        self.closed = threading.Event()
        self.thread = None
        self.failures = 0

    def start(self):
        self.thread = threading.Thread(target=self.run, name='DriftkingsAnalytics')
        self.thread.daemon = True
        self.thread.start()

    def post(self, event):
        if self.closed.is_set():
            return
        try:
            self.queue.put_nowait(event)
        except Full:
            pass

    def stop(self):
        self.closed.set()
        try:
            self.queue.put_nowait(None)
        except Full:
            pass

    def run(self):
        opener = None
        while not self.closed.is_set():
            event = self.queue.get()
            if event is None or self.closed.is_set():
                break
            batch = [event]
            while len(batch) < BATCH:
                try:
                    item = self.queue.get_nowait()
                except Empty:
                    break
                if item is None:
                    break
                batch.append(item)
            try:
                if opener is None:
                    opener = self.opener_factory()
                self.deliver(opener, batch)
                self.failures = 0
            except Exception:
                self.failures += 1
                LOG.debug('Analytics delivery failed', exc_info=True)
                if self.failures >= MAX_FAILURES:
                    LOG.info('Analytics paused for this session after repeated delivery failures')
                    self.closed.set()

    def deliver(self, opener, batch):
        body = json.dumps({'client_id': self.client_id, 'events': batch}).encode('utf-8')
        request = http.Request(self.url, body, {'Content-Type': 'application/json'})
        response = opener.open(request, timeout=TIMEOUT)
        try:
            response.read(1)
        finally:
            response.close()


class ErrorHandler(logging.Handler):
    """Forward the mod's own logged exceptions; the existing LOG.exception calls need no change."""

    def __init__(self, report):
        logging.Handler.__init__(self, logging.ERROR)
        self.report = report
        self.busy = False

    def emit(self, record):
        info = record.exc_info
        if self.busy or record.name == LOG.name or not isinstance(info, tuple) or info[0] is None:
            return
        self.busy = True
        try:
            self.report(record.name, info[0], info[2])
        except Exception:
            pass    # telemetry must never raise into game code or print to stderr
        finally:
            self.busy = False


class AnalyticsService(object):
    def __init__(self, api=None, callbacks=None, opener_factory=None, root=None, environment=None,
                 replay=None, listen=None, unlisten=None, clock=None, measurement_id=None, api_secret=None, write=None):
        self.api = api
        self.callbacks = callbacks
        self.opener_factory = opener_factory
        self.root = root
        self.environment = environment
        self.replay = replay
        self.listen = listen
        self.unlisten = unlisten
        self.clock = clock or time.time
        self.measurement_id = MEASUREMENT_ID if measurement_id is None else measurement_id
        self.api_secret = API_SECRET if api_secret is None else api_secret
        self.write = write
        self.active = False
        self.listening = False
        self.sender = None
        self.handler = None
        self.beat = None
        self.session = None
        self.context = {}
        self.seen = set()

    def start(self):
        if self.active:
            return
        if self.api is None:
            from driftkings.settings.panel import settings
            self.api = settings
        if self.callbacks is None:
            from driftkings.core.callbacks import callbacks
            self.callbacks = callbacks
        if self.root is None:
            from driftkings.core.cache import CONFIG_ROOT
            self.root = CONFIG_ROOT
        if self.listen is None:
            from driftkings.settings.panel import core_page
            self.listen, self.unlisten = core_page.subscribe, core_page.unsubscribe
        self.active = True
        if not configured(self.measurement_id, self.api_secret):
            LOG.info('Analytics is not configured in this build')
            return
        self.listen(self.changed)
        self.listening = True
        self.apply(bool(self.api.get(SETTINGS, OPTION, False)))

    def stop(self):
        if self.listening:
            self.listening = False
            self.unlisten(self.changed)
        self.close(False)
        self.active = False

    def changed(self, changes):
        if OPTION in changes:
            self.apply(bool(changes[OPTION]))

    def apply(self, enabled):
        if enabled and self.sender is None and not self.in_replay():
            self.open()
        elif not enabled and self.sender is not None:
            self.close(True)
        elif not enabled:
            self.forget()

    def in_replay(self):
        if self.replay is not None:
            return bool(self.replay())
        from driftkings.core import replay_session
        return replay_session()

    def open(self):
        client_id = self.identity()
        if client_id is None:
            return
        self.context = (self.environment or default_environment)()
        self.session = int(self.clock())
        self.seen = set()
        self.sender = Sender(ENDPOINT % (self.measurement_id, self.api_secret), client_id, self.opener_factory)
        self.sender.start()
        self.handler = ErrorHandler(self.report)
        logging.getLogger(NAMESPACE).addHandler(self.handler)
        self.track('mod_loaded')
        self.beat = self.callbacks.schedule(HEARTBEAT, self.heartbeat)
        LOG.info('Anonymous usage statistics are enabled')

    def close(self, forget):
        if self.beat is not None:
            self.callbacks.cancel(self.beat)
            self.beat = None
        if self.handler is not None:
            logging.getLogger(NAMESPACE).removeHandler(self.handler)
            self.handler = None
        if self.sender is not None:
            self.sender.stop()
            self.sender = None
        if forget:
            self.forget()
            LOG.info('Anonymous usage statistics are disabled; the installation id was removed')

    def heartbeat(self):
        self.beat = None
        if self.sender is None:
            return
        self.track('heartbeat', engagement_time_msec=int(HEARTBEAT * 1000))
        self.beat = self.callbacks.schedule(HEARTBEAT, self.heartbeat)

    def track(self, name, **params):
        sender = self.sender
        if sender is None:
            return
        values = {'mod_version': VERSION, 'session_id': self.session, 'engagement_time_msec': 100}
        values.update(self.context)
        values.update(params)
        sender.post({'name': name, 'params': clean(values)})

    def report(self, channel, kind, trace):
        file_name, line, function = '?', 0, '?'
        while trace is not None and trace.tb_next is not None:
            trace = trace.tb_next
        if trace is not None:
            code = trace.tb_frame.f_code
            file_name, line, function = os.path.basename(code.co_filename), trace.tb_lineno, code.co_name
        key = (channel, kind.__name__, file_name, line)
        if key in self.seen or len(self.seen) >= MAX_ERRORS:
            return
        self.seen.add(key)
        self.track('exception', description='%s %s:%s' % (kind.__name__, file_name, line), fatal=0,
                   error_channel=channel[len(NAMESPACE) + 1:] or NAMESPACE, error_type=kind.__name__,
                   error_file=file_name, error_line=line, error_function=function)

    def path(self):
        return os.path.join(self.root, IDENTITY)

    def identity(self):
        """Random per-installation id; created only after the player opted in."""
        try:
            with open(self.path(), 'rb') as stream:
                value = stream.read(64).decode('ascii', 'ignore').strip()
            if _IDENTITY.match(value):
                return value
        except (IOError, OSError):
            pass
        value = uuid.uuid4().hex
        try:
            write = self.write
            if write is None:
                from driftkings.common.utils.filesystem import atomicWrite as write
            write(self.path(), value.encode('ascii'))
        except Exception:
            LOG.warning('Could not store the analytics id; statistics stay off', exc_info=True)
            return None
        return value

    def forget(self):
        try:
            os.remove(self.path())
        except (IOError, OSError):
            pass
