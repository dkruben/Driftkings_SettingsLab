# -*- coding: utf-8 -*-
"""Commented JSON configs: create, read, merge and keep comments on Python 2.7 and 3."""
import io
import os
import shutil
import sys
import tempfile

from support import CLIENT, module, RuntimeTest


class JSONReaderTests(RuntimeTest):
    def setUp(self):
        super(JSONReaderTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        # Import config_utils without starting the settings services.
        sys.modules['driftkings.settings'] = module(__path__=[os.path.join(CLIENT, 'settings')])
        self.api = self.load('common.config.json_reader')

    def path(self, name):
        return os.path.join(self.root, name + '.json')

    def write(self, name, text):
        with io.open(self.path(name), 'w', encoding='utf-8') as stream:
            stream.write(text)

    def read(self, name):
        with io.open(self.path(name), encoding='utf-8-sig') as stream:
            return stream.read()

    def test_missing_config_is_created_from_defaults(self):
        defaults = {'enabled': True, 'size': 12}
        self.assertIs(self.api.loadJson('Test', 'created', defaults, self.root), defaults)
        self.assertEqual(self.api.loadJson('Test', 'created', {}, self.root), defaults)

    def test_comments_are_ignored_on_read_and_kept_on_save(self):
        self.write('commented', u'{\n    // Opção\n    "enabled": false, // inline\n    "url": "http://example.com"\n}')
        self.assertEqual(self.api.loadJson('Test', 'commented', {}, self.root),
                         {'enabled': False, 'url': 'http://example.com'})
        self.api.loadJson('Test', 'commented', {'enabled': True, 'url': 'http://example.com'}, self.root, True)
        text = self.read('commented')
        self.assertIn(u'// Opção', text)
        self.assertIn(u'// inline', text)
        self.assertEqual(self.api.loadJson('Test', 'commented', {}, self.root)['enabled'], True)

    def test_damaged_config_is_replaced_on_save(self):
        self.write('damaged', u'{"enabled": ')
        self.api.loadJson('Test', 'damaged', {'enabled': True}, self.root, True, quiet=True)
        self.assertEqual(self.api.loadJson('Test', 'damaged', {}, self.root), {'enabled': True})

    def test_encrypted_round_trip_and_plain_text_detection(self):
        self.assertEqual(self.api.JSONLoader.decrypt(self.api.JSONLoader.encrypt(u'{"a": 1}'), True), (b'{"a": 1}', True))
        self.assertEqual(self.api.JSONLoader.decrypt(u'{"a": "ç"}', False), (u'{"a": "ç"}', False))
