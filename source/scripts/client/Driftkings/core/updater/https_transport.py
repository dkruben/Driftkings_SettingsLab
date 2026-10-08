# -*- coding: utf-8 -*-
"""Certificate-verified streaming workers; delivery uses existing Core callbacks."""
import math
import logging
import socket
import threading
import time
try:
    from Queue import Queue, Empty
    import urllib2 as http
    from urlparse import urljoin
except ImportError:
    from queue import Queue, Empty
    import urllib.request as http
    from urllib.parse import urljoin

from Driftkings.core.updater.endpoints import validate_https
from Driftkings.core.updater.transport import Response, UnavailableTransport

CHUNK = 64 * 1024
LOG = logging.getLogger('Driftkings.Updater')


class TransferError(ValueError):
    def __init__(self, code):
        self.code = code
        super(TransferError, self).__init__(code)


class HTTPSRedirects(http.HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_https(urljoin(req.get_full_url(), newurl))
        return super(HTTPSRedirects, self).redirect_request(req, fp, code, msg, headers, newurl)


def verified_opener():
    import ssl
    context = ssl.create_default_context()
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname or not context.get_ca_certs():
        raise ValueError('Verified TLS unavailable')
    # Disable implicit proxy configuration/credentials and preserve hostname checks.
    return http.build_opener(http.ProxyHandler({}), HTTPSRedirects(),
                             http.HTTPSHandler(context=context))


class Operation(object):
    def __init__(self):
        self.cancelled = threading.Event()
        self.finished = threading.Event()
        self.events = Queue()
        self.latest_progress = None
        self.token = None
        self.lock = threading.Lock()
        self.sink = None
        self.cleanup_error = None

    def cancel(self):
        with self.lock:
            self.cancelled.set()
            if self.finished.is_set() and self.sink is not None:
                try:
                    self.sink.abort()
                except Exception:
                    self.cleanup_error = 'stagingError'
                    LOG.error('Could not remove cancelled update staging')


class HttpsTransport(object):
    available = True

    def __init__(self, callbacks, opener_factory=None, clock=None):
        self.callbacks = callbacks
        self.opener_factory = opener_factory or verified_opener
        self.clock = clock or getattr(time, 'monotonic', time.time)
        self.closed = False
        self.operations = []

    @property
    def busy(self):
        return any(not item.finished.is_set() for item in self.operations)

    def close(self):
        self.closed = True
        for operation in tuple(self.operations):
            operation.cancel()
            if operation.token is not None:
                self.callbacks.cancel(operation.token)
                operation.token = None

    def request(self, url, callback, timeout, max_bytes):
        return self._start(url, None, callback, timeout, max_bytes, None)

    def stream(self, url, sink, callback, timeout, max_bytes, progress=None):
        return self._start(url, sink, callback, timeout, max_bytes, progress)

    def _start(self, url, sink, callback, timeout, maximum, progress):
        validate_https(url)
        if timeout <= 0 or math.isinf(timeout) or math.isnan(timeout):
            raise ValueError('Invalid network timeout')
        if self.closed or maximum <= 0:
            raise ValueError('Transport unavailable')
        if self.busy:
            raise ValueError('Network operation already running')
        operation = Operation()
        self.operations.append(operation)
        if sink is not None:
            operation.sink = sink
            sink.cancelled = operation.cancelled
            sink.verifying = lambda: operation.events.put(('verifying', None))

        def worker():
            response, result, error = None, None, None
            deadline = self.clock() + timeout
            def guard():
                if operation.cancelled.is_set():
                    raise TransferError('cancelled')
                if self.clock() >= deadline:
                    raise TransferError('timeout')
            try:
                guard()
                request = http.Request(url, headers={'User-Agent': 'Driftkings-Updater', 'Accept-Encoding': 'identity'})
                response = self.opener_factory().open(request, timeout=min(timeout, 15.0))
                guard()
                validate_https(response.geturl())
                if response.getcode() != 200:
                    raise TransferError('httpError')
                encoding = response.info().get('Content-Encoding', 'identity')
                if encoding.lower() not in ('identity', ''):
                    raise TransferError('invalidResponse')
                length = response.info().get('Content-Length')
                if length is not None:
                    if not length.isdigit() or int(length) > maximum:
                        raise TransferError('oversizedPayload')
                    length = int(length)
                total, chunks = 0, []
                while True:
                    guard()
                    chunk = response.read(min(CHUNK, maximum - total + 1))
                    guard()
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > maximum:
                        raise TransferError('oversizedPayload')
                    if sink is None:
                        chunks.append(chunk)
                    else:
                        try:
                            sink.write(chunk)
                        except (IOError, OSError):
                            raise TransferError('stagingError')
                    operation.latest_progress = total
                if length is not None and length != total:
                    raise TransferError('partialDownload')
                if sink is None:
                    result = Response(200, b''.join(chunks), response.geturl())
                else:
                    try:
                        result = sink.finish()
                    except (IOError, OSError):
                        raise TransferError('stagingError')
            except TransferError as caught:
                error = caught.code
            except socket.timeout:
                error = 'timeout'
            except http.HTTPError:
                error = 'httpError'
            except Exception:
                error = 'networkError'
            finally:
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        error = error or 'networkError'
                with operation.lock:
                    if operation.cancelled.is_set():
                        error = 'cancelled'
                    if sink is not None and error:
                        try:
                            sink.abort()
                        except Exception:
                            error = 'stagingError'
                    operation.events.put(('done', (result, error)))
                    operation.finished.set()

        def pump():
            operation.token = None
            if self.closed:
                return
            if progress is not None and operation.latest_progress is not None:
                received, operation.latest_progress = operation.latest_progress, None
                progress('bytes', received)
            if self.closed:
                return
            while True:
                try:
                    kind, value = operation.events.get_nowait()
                except Empty:
                    break
                if kind == 'done':
                    if operation in self.operations:
                        self.operations.remove(operation)
                    if operation.cancelled.is_set():
                        value = (None, operation.cleanup_error or 'cancelled')
                    callback(*value)
                    return
                if progress is not None:
                    progress(kind, value)
                if self.closed:
                    return
            if not self.closed:
                operation.token = self.callbacks.schedule(0.25, pump)

        thread = threading.Thread(target=worker, name='Driftkings.Updater')
        thread.daemon = True
        try:
            operation.token = self.callbacks.schedule(0.25, pump)
            thread.start()
        except Exception:
            operation.cancel()
            if operation.token is not None:
                self.callbacks.cancel(operation.token)
            self.operations.remove(operation)
            if sink is not None:
                sink.abort()
            raise
        return operation


def runtime_transport():
    """Fail closed on missing SSL, CA roots or hostname verification in WoT."""
    try:
        verified_opener()
        from Driftkings.core.callbacks import callbacks
        return HttpsTransport(callbacks)
    except Exception:
        return UnavailableTransport()
