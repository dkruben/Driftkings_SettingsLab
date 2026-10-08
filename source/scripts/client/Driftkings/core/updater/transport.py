# -*- coding: utf-8 -*-
"""Transport interface shared by bounded metadata checks and package streaming.

request(url, callback, timeout, max_bytes) must call callback(response, error)
on the client thread, enforce bounds/timeout/TLS on every redirect and return
an optional cancel handle. Response contains status, body and final url.
"""


class Response(object):
    def __init__(self, status, body, url):
        self.status, self.body, self.url = status, body, url


class UnavailableTransport(object):
    available = False

    def request(self, url, callback, timeout, max_bytes):
        callback(None, 'transportUnavailable')

    def stream(self, url, sink, callback, timeout, max_bytes, progress=None):
        sink.abort()
        callback(None, 'transportUnavailable')
