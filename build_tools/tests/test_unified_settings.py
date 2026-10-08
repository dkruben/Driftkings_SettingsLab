import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT/'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings.settings.settings_data import DEFAULTS, HOTKEYS, defaults, default_keys
from Driftkings.settings.registry import SettingsRegistry
from Driftkings.settings.store import SettingsStore
from Driftkings.i18n import TranslationCatalog, LANGUAGES


def load_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def component_templates():
    from Driftkings import _constants
    root = CLIENT/'Driftkings/settings/templates'
    for path in sorted(root.glob('*/*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            for node in cls.body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'COMPONENT' for t in node.targets):
                    component = getattr(getattr(_constants, node.value.value.id), node.value.attr)
                    yield component, path, cls.name


class UnifiedSettingsTests(unittest.TestCase):
    def test_defaults_cover_exactly_the_enabled_components_and_are_independent(self):
        from Driftkings.component_list import COMPONENTS
        # File names are internal; stable settings IDs are declared by templates.
        templates = list(component_templates())
        ids = {component for component, path, cls in templates}
        self.assertEqual(len(templates), len(ids))
        self.assertEqual(set(DEFAULTS), ids)
        self.assertEqual(len(COMPONENTS), len(ids))
        self.assertTrue(all(name == name.lower() for name in COMPONENTS))
        data = defaults('PlayerPanelPro')
        del data['profiles']['large']['extraFieldsLeft'][:]
        self.assertTrue(defaults('PlayerPanelPro')['profiles']['large']['extraFieldsLeft'])
        keys = default_keys('ArtySplash')
        keys['buttonShowDot'].clear()
        self.assertTrue(default_keys('ArtySplash')['buttonShowDot'])

    def test_constant_catalogue_preserves_unique_json_sections(self):
        from Driftkings._constants import CONFIG_SECTIONS, CONFIG_BY_ID
        from Driftkings.settings.settings_data import part_name
        self.assertEqual(set(CONFIG_BY_ID), set(DEFAULTS))
        self.assertEqual(len(set(s.NAME for s in CONFIG_SECTIONS)), len(CONFIG_SECTIONS))
        with tempfile.TemporaryDirectory() as folder:
            from Driftkings.settings.loader import SettingsLoader
            loader = SettingsLoader(folder)
            for section in CONFIG_SECTIONS:
                with self.subTest(component=section.ID):
                    self.assertEqual(part_name(section.ID), section.NAME)
                    sample = defaults(section.ID)
                    loader.save(section.ID, sample)
                    self.assertEqual(loader.load(section.ID, sample), sample)
            self.assertTrue((Path(folder) / 'default/own_health.json').is_file())

    def test_all_templates_keep_ids_controls_and_hotkeys(self):
        builders = load_file(CLIENT/'Driftkings/common/config/template_builders.py', 'unified_builders')
        utils_tree = ast.parse((CLIENT/'Driftkings/common/config/utils.py').read_text(encoding='utf-8'))
        hotkey_fn = next(n for n in utils_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'processHotKeys')
        names = sorted({node.value for node in ast.walk(ast.parse(repr(HOTKEYS))) if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith('KEY_')})
        codes = {name: index + 1 for index, name in enumerate(names)}
        ns = {'Keys': types.SimpleNamespace(**codes), 'SPECIAL_TO_KEYS': {},
              'BigWorld': types.SimpleNamespace(keyToString=lambda code: names[code-1])}
        exec(compile(ast.Module(body=[hotkey_fn], type_ignores=[]), 'hotkeys', 'exec'), ns)
        with tempfile.TemporaryDirectory() as folder:
            catalog = TranslationCatalog(folder)
            class Base:
                def __init__(self):
                    self.init()
                    self.i18n = catalog.section(self.ID)
                    self.tb = builders.TemplateBuilder(self.data, self.i18n)
                def init(self): pass
                def getPanelProfile(self): return self.data['profiles']['large']
                def createTemplate(self): return None
            common = types.ModuleType('Driftkings.common')
            common.DriftkingsConfigInterface = Base
            common.ConfigNoInterface = type('NoInterface', (), {})
            common.color_tables = [{'ScaleColor': 'Default'}, {'ScaleColor': 'Alternative'}]
            fake_utils = types.ModuleType('Driftkings.common.config.utils')
            fake_utils.processHotKeys = ns['processHotKeys']
            game_labels = types.SimpleNamespace(**dict(('AIM_MIXING_TYPE%d'%i, str(i)) for i in range(4)),
                                               **dict(('AIM_GUNTAG_TYPE%d'%i, str(i)) for i in range(20)))
            patches = {'Driftkings.common': common, 'Driftkings.common.config.utils': fake_utils,
                       'ResMgr': types.SimpleNamespace(openSection=lambda path: {'default.png': None}),
                       'gui.Scaleform.locale.SETTINGS': types.SimpleNamespace(SETTINGS=game_labels),
                       'helpers': types.SimpleNamespace(i18n=types.SimpleNamespace(makeString=lambda text: text))}
            with patch.dict(sys.modules, patches):
                # A simple menu must import without the sixth-sense resource API.
                with patch.dict(sys.modules, {'ResMgr': None}):
                    own_health = importlib.import_module('Driftkings.settings.templates.battle.own_health')
                    self.assertEqual(own_health.OwnHealthSettings().ID, 'OwnHealth')
                for component, path, class_name in component_templates():
                    with self.subTest(component=component):
                        module_name = '.'.join(path.relative_to(CLIENT).with_suffix('').parts)
                        menu = importlib.import_module(module_name)
                        menu.xrange = range
                        menu.basestring = str
                        config = getattr(menu, class_name)()
                        self.assertEqual(config.ID, component)
                        registry = SettingsRegistry()
                        registry.register(config)
                        description = registry.describe(component)
                        self.assertEqual(description['id'], component)
                        from Driftkings.settings.panel.api import SettingsAPI
                        from Driftkings.settings.panel.compatibility import TemplateAdapter
                        api = SettingsAPI(folder + '/framework')
                        adapter = TemplateAdapter(api, registry)
                        adapter._register(component)
                        adapted = api.registry.mods['legacy.' + component]
                        self.assertEqual(len(adapted.values), len(description['values']))
                        from Driftkings._constants import HANDLER_VALUES
                        control_names = {source: field for field, source in adapter.mapping['legacy.' + component][1].items()}
                        for parent, children in HANDLER_VALUES.get(component, {}).items():
                            for child in children:
                                if component == 'SixthSense' and parent == 'userSound' and child == 'sixthSenseSound':
                                    sound_control = adapted.index[control_names[child]]
                                    self.assertEqual(sound_control.preview['kind'], 'audio')
                                    self.assertNotIn(control_names[parent], sound_control.depends_on)
                                    continue
                                accepted = children[child] if isinstance(children, dict) else (True,)
                                source = next(c for c in description['controls'] if c.get('varName') == parent)
                                choices = source.get('optionValues')
                                expected = [choices.index(v) if choices is not None else v for v in accepted]
                                self.assertEqual(adapted.index[control_names[child]].depends_on[control_names[parent]], expected)

                        self.assertFalse(any(c.type == 'number' for c in adapted.controls))
                        if component == 'MinimapPlugins':
                            from Driftkings.core.minimap import ARTILLERY_AIMS
                            aim = next(c for c in description['controls'] if c.get('varName') == 'artilleryAim.src')
                            self.assertEqual(aim['optionValues'], list(ARTILLERY_AIMS))
                            preview = adapted.index[control_names['artilleryAim.src']].preview
                            self.assertEqual(preview['images'], ['coui://' + p for p in ARTILLERY_AIMS])
                            # Stored custom JSON images stay selectable and keep their preview.
                            config.data['artilleryAim']['src'] = 'gui/custom/aim.png'
                            custom = registry.describe(component)
                            aim = next(c for c in custom['controls'] if c.get('varName') == 'artilleryAim.src')
                            self.assertEqual(aim['optionValues'][-1], 'gui/custom/aim.png')
                            config.data['artilleryAim']['src'] = ARTILLERY_AIMS[0]
                        from Driftkings.settings.panel.layout import balance_columns
                        balance_columns(adapted.controls)
                        if len(adapted.values) > 1:
                            self.assertEqual({c.column for c in adapted.value_controls()}, {0, 1})
                        ns['processHotKeys'](config.data, config.defaultKeys, 'write')
                        for key in HOTKEYS.get(component, {}):
                            self.assertEqual(config.data[key], DEFAULTS[component][key])
                        self.assertFalse(any('%(mod_ID)s' in str(value) for value in config.i18n.values()))
                        if component == 'CarouselStats':
                            extra = config.data['carousel']['normal']['extraFields']
                            extra.append({'enabled': True, 'format': '{{vehicle}}', 'x': '{{v.level}}',
                                          'color': '{{c:winrate}}', 'src': 'custom.png'})
                            updated = registry.describe(component)
                            path = ['carousel', 'normal', 'extraFields', len(extra) - 1, 'x']
                            field = next(c for c in updated['controls'] if c.get('path') == path)
                            self.assertEqual(field['type'], 'TextInput')
                            self.assertEqual(updated['values'][field['varName']], '{{v.level}}')
                        if component == 'SixthSense':
                            config.sixthSenseIconsNamesList = lambda: ['0.png', '17.png']
                            config.data['defaultIconName'] = 17
                            config.data['sixthSenseSound'] = 'custom_bank_event'
                            updated = registry.describe(component)
                            icon = next(c for c in updated['controls'] if c.get('varName') == 'defaultIconName')
                            sound = next(c for c in updated['controls'] if c.get('varName') == 'sixthSenseSound')
                            self.assertEqual(icon['optionValues'], [0, 17])
                            self.assertEqual(updated['values']['defaultIconName'], 1)
                            self.assertTrue(icon['previewImage'])
                            self.assertEqual(icon['options'][1]['image'], 'gui/maps/icons/SixthSense/17.png')
                            self.assertIn('custom_bank_event', sound['optionValues'])
                            adapter._register(component)
                            preview = api.registry.mods['legacy.' + component]
                            self.assertTrue(any(c.preview and c.preview['kind'] == 'audio' for c in preview.controls))
                        if component == 'MinimapPlugins':
                            config.i18n['UI_mode_on'] = 'Ligado personalizado'
                            updated = registry.describe(component)
                            direction = next(c for c in updated['controls'] if c.get('path') == ['lines', 'direction'])
                            self.assertEqual(direction['options'][1]['label'], 'Ligado personalizado')
                            # Editing returned metadata must not affect a later window.
                            direction['path'].append('damaged')
                            self.assertTrue(any(c.get('path') == ['lines', 'direction'] for c in registry.describe(component)['controls']))



class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = TranslationCatalog(self.temp.name)

    def write(self, relative, data):
        SettingsStore(str(self.root/relative)).write(data)

    def test_one_time_migration_keeps_component_namespaces_and_originals(self):
        old = {'UI_description': 'My HP', 'custom': 'José {{name}}'}
        self.write('OwnHealth/i18n/en.json', old)
        self.write('MainGun/i18n/en.json', {'UI_description': 'My gun'})
        original = (self.root/'OwnHealth/i18n/en.json').read_bytes()
        self.assertEqual(self.catalog.section('OwnHealth')['custom'], old['custom'])
        self.assertEqual(self.catalog.section('MainGun')['UI_description'], 'My gun')
        self.assertEqual((self.root/'OwnHealth/i18n/en.json').read_bytes(), original)
        self.write('OwnHealth/i18n/en.json', {'UI_description': 'Ignored later'})
        self.assertEqual(self.catalog.section('OwnHealth')['UI_description'], 'My HP')
        self.assertEqual(set(json.loads((self.root/'i18n/en.json').read_text())), {'OwnHealth', 'MainGun'})

    def test_common_window_labels_and_component_override(self):
        self.write('i18n/en.json', {'common': {'UI_native_save': 'Guardar'},
                                  'OwnHealth': {'UI_native_save': 'Aplicar'}})
        self.assertEqual(self.catalog.section('OwnHealth')['UI_native_save'], 'Aplicar')
        self.assertEqual(self.catalog.section('MainGun')['UI_native_save'], 'Guardar')

    def test_partial_unified_overrides_and_reload(self):
        self.write('i18n/en.json', {'OwnHealth': {'UI_description': 'Custom'}})
        self.assertEqual(self.catalog.section('OwnHealth')['UI_description'], 'Custom')
        self.assertIn('UI_setting_y_text', self.catalog.section('OwnHealth'))
        self.write('i18n/en.json', {'OwnHealth': {'UI_description': 'Changed description'}})
        self.assertEqual(self.catalog.section('OwnHealth')['UI_description'], 'Changed description')

    def test_unknown_language_fallback_and_independent_sections(self):
        data = self.catalog.section('OwnHealth', '../../en')
        self.assertIn('UI_setting_x_text', data)
        data['UI_setting_x_text'] = 'Changed'
        self.assertNotEqual(self.catalog.section('OwnHealth')['UI_setting_x_text'], 'Changed')
        self.assertEqual(self.catalog.section('Future')['UI_description'], 'Future')

    def test_invalid_override_is_preserved_and_falls_back(self):
        path = self.root/'i18n/en.json'
        path.parent.mkdir()
        path.write_text('{broken')
        with self.assertLogs('Driftkings.i18n', level='ERROR'):
            labels = self.catalog.section('OwnHealth')
        self.assertIn('UI_setting_x_text', labels)
        self.assertEqual(path.read_text(), '{broken')

    def test_invalid_legacy_does_not_complete_migration(self):
        path = self.root/'OwnHealth/i18n/en.json'
        path.parent.mkdir(parents=True)
        path.write_text('[]')
        with self.assertLogs('Driftkings.i18n', level='ERROR'):
            self.catalog.section('OwnHealth')
        self.assertFalse((self.root/'i18n/en.json').exists())

    def test_every_bundled_language_covers_active_components(self):
        for language in LANGUAGES:
            catalog = self.catalog.bundled(language)
            self.assertTrue(set(DEFAULTS).issubset(catalog))
            self.assertIn('UI_profile_restart', catalog['Driftkings'])


if __name__ == '__main__': unittest.main()
