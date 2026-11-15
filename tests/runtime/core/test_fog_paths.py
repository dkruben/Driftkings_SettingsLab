# -*- coding: utf-8 -*-
"""Fog runtime follows the installed mod path without allowing arbitrary paths."""
import os
import shutil
import tempfile

from support import RuntimeTest, module, source


class FogPathTests(RuntimeTest):
    def setUp(self):
        super(FogPathTests, self).setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.api = source('core/fog_package.py', {
            'driftkings.core.updater.installer': module(read_resource=None),
            'driftkings.settings.service': module(settings_service=None)})
        for name in ('2.4.2.0', '2.4.2.0 Common Test'):
            os.makedirs(os.path.join(self.root, 'mods', name))

    def paths(self, values):
        with open(os.path.join(self.root, 'paths.xml'), 'w') as stream:
            stream.write('<root><Paths>' + ''.join('<Path>' + value + '</Path>' for value in values) + '</Paths></root>')

    def test_ct_declared_folder_wins_even_when_numeric_folder_exists(self):
        self.paths(['./res_mods/2.4.2.0 Common Test', './mods/2.4.2.0 Common Test'])
        self.assertEqual(self.api['mod_directory'](self.root, '2.4.2.0'),
                         os.path.join(self.root, 'mods', '2.4.2.0 Common Test'))

    def test_production_and_missing_paths_file_use_numeric_folder(self):
        self.assertEqual(self.api['mod_directory'](self.root, '2.4.2.0'), os.path.join(self.root, 'mods', '2.4.2.0'))
        self.paths(['./mods/2.4.2.0'])
        self.assertEqual(self.api['mod_directory'](self.root, '2.4.2.0'), os.path.join(self.root, 'mods', '2.4.2.0'))

    def test_unsafe_unknown_or_ambiguous_paths_are_rejected(self):
        for values in (['./mods/../other'], ['./mods/2.4.1.1'],
                       ['./mods/2.4.2.0', './mods/2.4.2.0 Common Test']):
            self.paths(values)
            self.assertRaises(ValueError, self.api['mod_directory'], self.root, '2.4.2.0')
        self.assertRaises(ValueError, self.api['mod_directory'], self.root, '../2.4.2.0')

    def test_declared_folder_must_exist(self):
        self.paths(['./mods/2.4.2.0 Common Test'])
        os.rmdir(os.path.join(self.root, 'mods', '2.4.2.0 Common Test'))
        self.assertRaises(ValueError, self.api['mod_directory'], self.root, '2.4.2.0')
