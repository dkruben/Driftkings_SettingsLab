# -*- coding: utf-8 -*-
"""Text resource parsing, VFS access, fallback and existing JSON overrides."""
from __future__ import unicode_literals
import json
import os
import shutil
import sys
import tempfile

from support import CLIENT, RuntimeTest, module


class LocaleResourceTests(RuntimeTest):
    def setUp(self):
        super(LocaleResourceTests, self).setUp()
        # Import the real localization stack without starting settings services.
        sys.modules['driftkings.settings'] = module(__path__=[os.path.join(CLIENT, 'settings')])
        self.parser = self.load('core.locale_catalog').parse_catalog
        self.catalog = self.load('i18n')
        self.resources = self.load('i18n.resources')
        self.panel = self.load('i18n.panel')

    def test_parser_preserves_unicode_html_whitespace_paths_and_nested_values(self):
        value = u'  VitÃ³ria: <font color="{c:wn8}">{wn8}</font>\nC:\\mods\\text  '
        document = self.parser(('\ufeff# comment\ncommon.label: ' + json.dumps(value) +
                                '\npenetration_indicator.UI_colors.green: "#60CB00"\n'
                                'panel.page.title: "DefiniÃ§Ãµes"\n').encode('utf-8'))
        self.assertEqual(document['TEXT']['common']['label'], value)
        self.assertEqual(document['TEXT']['penetration_indicator']['UI_colors']['green'], '#60CB00')
        self.assertEqual(document['PANEL']['page.title'], u'DefiniÃ§Ãµes')
        self.assertEqual(self.parser("common.label: 'It''s ready'\n")['TEXT']['common']['label'], "It's ready")

    def test_parser_rejects_duplicate_conflicting_and_malformed_entries(self):
        for content in ('common.a: "one"\ncommon.a: "two"',
                        'common.a: "one"\ncommon.a.b: "two"',
                        'common.a.b: "one"\ncommon.a: "two"',
                        'invalid line', 'common.a: "unclosed', 'common..a: "text"'):
            with self.assertRaises(ValueError):
                self.parser(content)

    def test_resources_cache_reads_return_independent_copies_and_use_language_aliases(self):
        reads = []
        def reader(code):
            reads.append(code)
            return 'common.label: "Text"\npanel.title: "Settings"'
        resources = self.resources.CatalogResources(reader)
        first = resources.load('pt-BR')
        first['TEXT']['common']['label'] = 'Changed'
        self.assertEqual(resources.load('pt')['TEXT']['common']['label'], 'Text')
        self.assertEqual(reads, ['pt'])

    def test_missing_or_bad_optional_resource_falls_back_for_both_consumers(self):
        original = self.resources.resources.reader
        def reader(code):
            if code == 'pt':
                raise IOError('missing')
            if code == 'fr':
                return 'bad format'
            return original(code)
        self.resources.resources.reader = reader
        english = self.catalog.TranslationCatalog().bundled('en')
        for code in ('pt', 'fr'):
            self.assertEqual(self.catalog.TranslationCatalog().bundled(code), english)
            self.assertEqual(self.panel.load(code)[1], self.panel.load('en')[1])
        self.resources.resources.cache['de'] = self.parser('common.custom: "Deutsch"\npanel.title: "Deutsch"')
        merged = self.catalog.TranslationCatalog().bundled('de')
        self.assertEqual(merged['common']['custom'], 'Deutsch')
        self.assertEqual(merged['high_caliber_progress'], english['high_caliber_progress'])
        self.assertEqual(self.panel.load('de')[1]['title'], 'Deutsch')
        self.assertEqual(self.panel.load('de')[1]['author'], self.panel.load('en')[1]['author'])

    def test_vfs_reader_uses_packaged_path_without_opening_local_files(self):
        saved = sys.modules.get('ResMgr')
        paths = []
        sys.modules['ResMgr'] = module(
            openSection=lambda path: paths.append(path) or module(asBinary=b'panel.title: "Title"'),
            isFile=lambda path: True)
        try:
            self.assertEqual(self.resources.read_resource('en'), b'panel.title: "Title"')
            self.assertEqual(paths, ['mods/driftkings/text/en.yml'])
        finally:
            if saved is None:
                del sys.modules['ResMgr']
            else:
                sys.modules['ResMgr'] = saved

    def test_missing_english_resource_is_reported_instead_of_cached_as_empty(self):
        def reader(code):
            raise IOError('missing English')
        resources = self.resources.CatalogResources(reader)
        with self.assertRaises(IOError):
            resources.load('en')
        self.assertNotIn('en', resources.cache)

    def test_old_component_overrides_are_ignored_and_left_untouched(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        folder = os.path.join(root, 'MainGun', 'i18n')
        os.makedirs(folder)
        legacy = os.path.join(folder, 'pt.json')
        original = json.dumps({'UI_custom': u'Legado'}).encode('utf-8')
        with open(legacy, 'wb') as stream:
            stream.write(original)
        result = self.catalog.TranslationCatalog(root).read('pt')
        self.assertNotIn('UI_custom', result['high_caliber_progress'])
        self.assertFalse(os.path.exists(os.path.join(root, 'i18n', 'pt.json')))
        with open(legacy, 'rb') as stream:
            self.assertEqual(stream.read(), original)

    def test_both_json_override_formats_remain_unchanged(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        for folder in ('i18n', 'locales'):
            os.mkdir(os.path.join(root, folder))
        component_path = os.path.join(root, 'i18n', 'pt.json')
        component_bytes = json.dumps({'common': {'UI_custom': u'Personalizado'}}).encode('utf-8')
        with open(component_path, 'wb') as stream:
            stream.write(component_bytes)
        with open(os.path.join(root, 'locales', 'pt.json'), 'wb') as stream:
            stream.write(json.dumps({'title': u'O meu painel'}).encode('utf-8'))
        value = self.catalog.TranslationCatalog(root).section('high_caliber_progress', 'pt')
        self.assertEqual(value['UI_custom'].decode('utf-8') if isinstance(value['UI_custom'], bytes)
                         else value['UI_custom'], u'Personalizado')
        self.assertEqual(self.panel.load('pt', root)[1]['title'], u'O meu painel')
        with open(component_path, 'rb') as stream:
            self.assertEqual(stream.read(), component_bytes)
