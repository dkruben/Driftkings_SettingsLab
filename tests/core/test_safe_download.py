# -*- coding: utf-8 -*-
import json
import os
import shutil
import tempfile

from support import RuntimeTest


class Response(object):
    def __init__(self, body, status=200):
        self.body, self.status, self.closed = body, status, False

    def getcode(self):
        return self.status

    def read(self, limit=-1):
        return self.body if limit < 0 else self.body[:limit]

    def close(self):
        self.closed = True


class SafeDownloadTests(RuntimeTest):
    def setUp(self):
        super(SafeDownloadTests, self).setUp()
        self.api = self.load('core.safe_download')
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.path = os.path.join(self.folder, 'data.json')

    def fetch(self, response=None, error=None, **options):
        def opener(url, timeout):
            if error:
                raise error
            self.response = response
            return response
        return self.api.download_json('https://example.invalid/x.json', self.path, opener=opener, **options)

    def read(self):
        with open(self.path) as stream:
            return json.load(stream)

    def test_success_replaces_file_atomically_and_closes_response(self):
        with open(self.path, 'w') as stream:
            stream.write('{"old": 1}')
        response = Response(b'{"new": 2}')
        self.assertTrue(self.fetch(response))
        self.assertEqual(self.read(), {'new': 2})
        self.assertTrue(response.closed)
        self.assertEqual(os.listdir(self.folder), ['data.json'])

    def test_failures_keep_existing_cache_and_leave_no_temporary_file(self):
        with open(self.path, 'w') as stream:
            stream.write('{"old": 1}')
        cases = (dict(response=Response(b'{"new": 2}', status=500)), dict(response=Response(b'{not json')),
                 dict(response=Response(b'')), dict(response=Response(b'{"a": "' + b'x' * 50 + b'"}'), limit=10),
                 dict(error=IOError('offline')))
        for options in cases:
            self.assertFalse(self.fetch(**options))
            self.assertEqual(self.read(), {'old': 1})
            self.assertEqual(os.listdir(self.folder), ['data.json'])

    def test_failure_does_not_create_a_placeholder(self):
        self.assertFalse(self.fetch(error=IOError('offline')))
        self.assertFalse(os.path.exists(self.path))


if __name__ == '__main__':
    import unittest
    unittest.main()
