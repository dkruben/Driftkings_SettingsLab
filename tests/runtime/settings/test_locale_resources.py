# -*- coding: utf-8 -*-
"""Text resource parsing, VFS access, fallback and existing JSON overrides."""
from __future__ import unicode_literals
import json
import os
import shutil
import sys
import tempfile

from support import CLIENT, ROOT, RuntimeTest, module


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

    def recordFailures(self):
        # Expected failures are recorded instead of printing tracebacks into the test output.
        failures = []
        saved = self.resources.LOG
        self.resources.LOG = module(exception=lambda message, *args: failures.append(message % args))
        self.addCleanup(setattr, self.resources, 'LOG', saved)
        return failures

    def test_missing_or_bad_optional_resource_falls_back_for_both_consumers(self):
        original = self.resources.resources.reader
        def reader(code):
            if code == 'pt':
                raise IOError('missing')
            if code == 'fr':
                return 'bad format'
            return original(code)
        self.resources.resources.reader = reader
        failures = self.recordFailures()
        english = self.catalog.TranslationCatalog().bundled('en')
        for code in ('pt', 'fr'):
            self.assertEqual(self.catalog.TranslationCatalog().bundled(code), english)
            self.assertEqual(self.panel.load(code)[1], self.panel.load('en')[1])
        self.assertIn('Could not load bundled locale: pt', failures)
        self.assertIn('Could not load bundled locale: fr', failures)
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
        failures = self.recordFailures()
        resources = self.resources.CatalogResources(reader)
        with self.assertRaises(IOError):
            resources.load('en')
        self.assertNotIn('en', resources.cache)
        self.assertEqual(failures, ['Could not load bundled locale: en'])

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


class InterfaceLanguageSelectorTests(RuntimeTest):
    """Synthetic setup only: the real settings API with the bundled catalogues; no game client."""

    def setUp(self):
        super(InterfaceLanguageSelectorTests, self).setUp()
        sys.modules['driftkings.settings'] = module(__path__=[os.path.join(CLIENT, 'settings')])
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory, True)
        self.locale_support = self.load('locale_support')
        self.core_page = self.load('settings.panel.core_page')
        self.panel = self.load('i18n.panel')
        self.api = self.load('settings.panel.api').SettingsAPI(self.directory)
        self.api.client_language = 'pt'
        self.api.start('pt')

    def language_control(self):
        return [control for control in self.api.mod(self.core_page.CORE_ID)._mod.controls if control.id == 'language'][0]

    def test_language_list_has_no_empty_entries_and_only_supported_locales(self):
        options = self.core_page.language_options()
        self.assertEqual(options[0][0], 'auto')
        for value, label in options:
            self.assertTrue(label, value)
        codes = [value for value, _ in options[1:]]
        self.assertEqual(codes, list(self.locale_support.CODES))
        self.assertEqual(len(set(codes)), len(codes))

    def test_locale_without_a_loadable_catalogue_is_removed_from_the_list(self):
        original = self.panel.usable
        self.addCleanup(setattr, self.panel, 'usable', original)
        self.panel.usable = lambda code: code != 'th'
        values = [value for value, _ in self.core_page.language_options()]
        self.assertNotIn('th', values)
        self.assertIn('ja', values)

    def test_invalid_empty_or_unknown_locale_is_rejected_before_it_is_saved(self):
        control = self.language_control()
        for value in ('xx', '', 'not-a-locale', None):
            with self.assertRaises(ValueError):
                control.validate(value)
        self.assertEqual(control.validate('ja'), 'ja')

    def test_unknown_or_empty_locale_falls_back_to_game_language_and_keeps_text(self):
        for preference in ('xx', ''):
            self.api.set_language(preference)
            self.assertEqual(self.api.language, 'pt')
            self.assertEqual(self.api.strings['core.language'], 'Idioma da interface')
            self.assertEqual(len(self.api.strings), len(self.panel.load('en')[1]))

    def test_failed_catalogue_load_falls_back_to_english_and_keeps_text(self):
        original = self.panel.load
        def fail_for_japanese(language, override_root=None):
            if language == 'ja':
                raise IOError('synthetic missing catalogue')
            return original(language, override_root)
        self.panel.load = fail_for_japanese
        self.addCleanup(setattr, self.panel, 'load', original)
        self.api.set_language('ja')
        self.assertEqual(self.api.language, 'en')
        self.assertEqual(self.api.strings['core.language'], 'Interface language')
        self.assertTrue(all(self.api.strings.values()))

    def test_applying_a_valid_locale_keeps_every_text_available(self):
        self.api.set_language('ja')
        self.assertEqual(self.api.language, 'ja')
        self.assertEqual(len(self.api.strings), len(self.panel.load('en')[1]))
        self.assertTrue(all(value for value in self.api.strings.values()))


class SettingsFontFallbackTests(RuntimeTest):
    """Static contracts for explicit multilingual font registration in the settings panel (no runtime font APIs)."""
    VERIFIED_FILES = ('Warhelios-Regular.ttf', 'Warhelios-Bold.ttf', 'WarheliosJA-Medium.ttf', 'WarheliosJA-Bold.ttf',
                      'WarheliosKO-Medium.ttf', 'WarheliosKO-Bold.ttf', 'WarheliosZHCN-Medium.ttf',
                      'WarheliosZHCN-Bold.ttf', 'WarheliosZHTW-Medium.ttf', 'WarheliosZHTW-Bold.ttf')
    FAMILIES = ('DKWarhelios', 'DKWarheliosJA', 'DKWarheliosKO', 'DKWarheliosZHCN', 'DKWarheliosZHTW')

    def read(self, relative):
        path = os.path.join(ROOT, 'mod', 'res', 'gui', 'gameface', 'mods', 'driftkings', *relative.split('/'))
        with open(path, 'rb') as stream:
            return stream.read().decode('utf-8')

    def test_every_native_font_file_is_registered_under_a_distinct_family(self):
        css = self.read('settings_window/css/panel.css')
        for name in self.VERIFIED_FILES:
            self.assertIn("coui://gui/gameface/fonts/%s'" % name, css, name)
        for family in self.FAMILIES:
            self.assertIn("font-family: '%s'" % family, css, family)
        self.assertNotIn("font-family: Warhelios;", css)

    def test_each_language_option_is_assigned_its_script_family(self):
        core = self.read('settings_window/js/core.js')
        for code, family in (('ja', 'DKWarheliosJA'), ('ko', 'DKWarheliosKO'), ('zh_cn', 'DKWarheliosZHCN'),
                             ('zh_tw', 'DKWarheliosZHTW')):
            self.assertIn("%s: '%s'" % (code, family), core)
        controls = self.read('settings_window/js/controls.js')
        self.assertIn("if (def.id === 'language') { item.style.fontFamily = DK.languageFamily(", controls)
        self.assertIn("if (def.id === 'language') { label.style.fontFamily = DK.languageFamily(", controls)

    def test_whole_panel_text_selects_the_script_family_from_the_interface_language(self):
        css = self.read('settings_window/css/panel.css')
        for code, family in (('ja', 'DKWarheliosJA'), ('ko', 'DKWarheliosKO'), ('zh_cn', 'DKWarheliosZHCN'),
                             ('zh_tw', 'DKWarheliosZHTW')):
            self.assertIn("html[lang=%s] body, html[lang=%s] button, html[lang=%s] input, html[lang=%s] textarea { "
                          "font-family: '%s'; }" % (code, code, code, code, family), css)
        self.assertNotIn('var(--dk-font', css)
        app = self.read('settings_window/js/app.js')
        self.assertIn("setAttribute('lang', schema.language);", app)

    def test_font_diagnostic_overlay_is_removed_from_production_panel(self):
        app = self.read('settings_window/js/app.js')
        self.assertNotIn('FONT_DIAGNOSTIC', app)
        self.assertNotIn('renderFontDiagnostic', app)
        self.assertNotIn('dk-font-diagnostic', app)

    def test_traditional_catalogue_has_no_simplified_only_forms_that_the_font_cannot_draw(self):
        text = os.path.join(ROOT, 'mod', 'res', 'mods', 'driftkings', 'text', 'zh_tw.yml')
        with open(text, 'rb') as stream:
            content = stream.read().decode('utf-8')
        for simplified in ('关闭', '游戏', '安装', '检查', '设置', '语言', '这个', '客户端', '编辑'):
            self.assertNotIn(simplified, content, simplified)
