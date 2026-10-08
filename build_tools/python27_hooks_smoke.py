from mercurial import registrar
import imp
import os
import sys
import types
from functools import partial
cmdtable = {}
command = registrar.command(cmdtable)
@command('dksmoke', [], '', norepo=True)
def smoke(ui, **opts):
    base = os.path.abspath('source/scripts/client')
    sys.path.insert(0, base)
    import ast
    for folder, dirs, files in os.walk(os.path.join(base, 'Driftkings')):
        for filename in files:
            if not filename.endswith('.py'):
                continue
            path = os.path.join(folder, filename)
            with open(path, 'rb') as stream:
                tree = ast.parse(stream.read(), path)
            for node in ast.walk(tree):
                names = ([node.module] if isinstance(node, ast.ImportFrom) and node.module else
                         [entry.name for entry in node.names] if isinstance(node, ast.Import) else [])
                for name in names:
                    if name.startswith('Driftkings.'):
                        target = os.path.join(base, *name.split('.'))
                        assert os.path.isfile(target + '.py') or os.path.isfile(os.path.join(target, '__init__.py')), (path, name)
    ui.write('Python 2.7 unified namespace and imports: OK\n')
    from Driftkings.core.keycodes import valid_key_code
    assert valid_key_code(30L) and valid_key_code(259L) and valid_key_code(326)
    assert not any(valid_key_code(code) for code in (True, 0, 327, 30.0, '30'))
    ui.write('Python 2.7 native keyboard/mouse codes: OK\n')

    from Driftkings.settings.service import SettingsService
    from Driftkings.settings.settings_data import SettingsData
    from Driftkings._constants import OWN_HEALTH, GLOBAL, PLAYER_PANEL_PRO
    from Driftkings.settings.dependencies import option_dependencies
    from Driftkings.settings.template_schema import field
    class Config(object):
        ID = OWN_HEALTH.ID
        REFRESH_KEYS = (GLOBAL.ENABLED,)
        def __init__(self):
            self.data = {GLOBAL.ENABLED: True, 'position': {'x': 1}}
            self.saved = []
            self.refreshed = []
        def onApplySettings(self, changes):
            self.saved.append(changes)
            self.data.update(changes)
        def onModSettingsChanged(self, component, changes):
            self.refreshed.append((component, changes))
    config = Config()
    service = SettingsService(SettingsData())
    service.register(config)
    position = config.data['position']
    service.apply(OWN_HEALTH, {'position': {'x': 2}}, persist=False)
    assert config.data['position'] is position and position['x'] == 2
    assert not config.saved and not config.refreshed
    service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
    service.setSetting(OWN_HEALTH, GLOBAL.ENABLED, False)
    assert config.saved == [{GLOBAL.ENABLED: False}]
    assert config.refreshed == [(OWN_HEALTH.NAME, {GLOBAL.ENABLED: False})]
    assert config.refreshed[0][1].paths == frozenset([(GLOBAL.ENABLED,)])
    from Driftkings.settings.service import affects
    assert affects(config.refreshed[0][1], GLOBAL.ENABLED)
    assert not affects(config.refreshed[0][1], 'position')
    controls = [field(['hpVisibility'], 'HP', 'Dropdown', choices=['never', 'hold', 'always']),
                field(['hpKey'], 'Key', 'HotKey')]
    assert option_dependencies(PLAYER_PANEL_PRO.ID, controls)['hpKey'] == {'hpVisibility': [1]}
    ui.write('Python 2.7 settings service, filtered events and declarations: OK\n')

    for name in ('Driftkings.common', 'Driftkings.common.utils'):
        module = types.ModuleType(name)
        module.__path__ = [os.path.join(base, *name.split('.'))]
        sys.modules[name] = module
    h = imp.load_source('dk_test_hooks', os.path.join(base, 'Driftkings/core/hooks.py'))
    class Target(object):
        def method(self, value): return value + 1
        @staticmethod
        def static(value): return value + 2
        @classmethod
        def classed(cls, value): return value + 3
        @property
        def prop(self): return self._value
        @prop.setter
        def prop(self, value): self._value = value
    obj = Target()
    obj.prop = 4
    def method(original, self, value): return original(self, value) * 2
    def static(original, value): return original(value) * 2
    def classed(original, cls, value): return original(value) * 2
    def getter(original, self): return original(self) * 2
    def setter(original, self, value): return original(self, value + 1)
    h.hooks.current = 'smoke'
    h.override(Target, 'method', partial(method))
    h.overrideStaticMethod(Target, 'static')(static)
    h.overrideClassMethod(Target, 'classed')(classed)
    h.override(Target, 'prop', getter=getter, setter=setter)
    assert obj.method(1) == 2
    h.hooks.activate('smoke')
    assert obj.method(1) == 4
    assert Target.static(1) == 6
    assert Target.classed(1) == 8
    obj.prop = 4
    assert obj.prop == 10
    h.hooks.deactivate('smoke')
    assert obj.method(1) == 2
    assert Target.static(1) == 3
    assert Target.classed(1) == 4
    obj.prop = 4
    assert obj.prop == 4
    ui.write('Python 2.7 managed hooks: OK\n')
    import tempfile
    import shutil
    settings = imp.load_source('dk_test_settings', os.path.join(base, 'Driftkings/settings/store.py'))
    directory = tempfile.mkdtemp(prefix='dk-settings-test-')
    try:
        path = os.path.join(directory, 'settings.json')
        store = settings.SettingsStore(path)
        store.load('A', {'value': 1})
        store.save('A', {'value': 2})
        assert store.read()['components']['A']['value'] == 2
        os.rename(path, path + '.previous')
        assert store.read()['components']['A']['value'] == 2
        assert os.path.isfile(path)
    finally:
        shutil.rmtree(directory)
    ui.write('Python 2.7 settings publication and recovery: OK\n')

    from Driftkings.settings.loader import SettingsLoader
    from Driftkings.settings.profiles import ProfileSettings
    from Driftkings.settings.registry import SettingsRegistry
    directory = tempfile.mkdtemp(prefix='dk-profile-test-')
    try:
        loader = SettingsLoader(directory)
        data = loader.load('OwnHealth', {'enabled': True, 'colors': {'ally': '#60CB00'}})
        assert data['enabled'] is True
        page = ProfileSettings(loader)
        registry = SettingsRegistry()
        registry.register(page)
        values = registry.describe('Driftkings')['values']
        values['newProfile'] = 'custom'
        registry.apply('Driftkings', values)
        assert loader.active == 'default' and loader.selected() == 'custom'
        loader.save('OwnHealth', {'enabled': False})
        assert SettingsLoader(directory).load('OwnHealth', {'enabled': True})['enabled'] is True
    finally:
        shutil.rmtree(directory)
    ui.write('Python 2.7 profile migration, cloning and settings menu: OK\n')

    from Driftkings.settings.settings_data import DEFAULTS, defaults
    from Driftkings.i18n import TranslationCatalog, LANGUAGES
    assert len(DEFAULTS) == 33
    directory = tempfile.mkdtemp(prefix='dk-i18n-test-')
    try:
        catalog = TranslationCatalog(directory)
        for language in LANGUAGES:
            assert set(DEFAULTS).issubset(catalog.bundled(language))
        custom = u'Minha vida \u00e9 {{value}}'
        settings.SettingsStore(os.path.join(directory, 'OwnHealth', 'i18n', 'en.json')).write({'UI_description': custom})
        labels = catalog.section('OwnHealth', 'en')
        assert labels['UI_description'] == custom.encode('utf-8')
        assert 'UI_native_save' in labels
        assert os.path.isfile(os.path.join(directory, 'i18n', 'en.json'))
        data = defaults('PlayerPanelPro')
        del data['profiles']['large']['extraFieldsLeft'][:]
        assert defaults('PlayerPanelPro')['profiles']['large']['extraFieldsLeft']
    finally:
        shutil.rmtree(directory)
    ui.write('Python 2.7 shared defaults and unified UTF-8 translations: OK\n')

    layout = imp.load_source('dk_test_carousel', os.path.join(base, 'Driftkings/core/carousel.py'))
    data = layout.config_defaults()
    assert len(data['carousel']['normal']['extraFields']) == 14
    assert len(data['carousel']['small']['extraFields']) == 4
    rendered = layout.render('{{v.name}} {{v.winrate%2d~%}}',
                             {'vehicle': u'Tigre II', 'winRate': 52.3},
                             lambda *args: '#FFFFFF', lambda key: '')
    assert rendered == u'Tigre II 52%'
    render = lambda text: layout.render(text, {'premium': True, 'classColor': '#957D5B'},
                                       lambda *args: '#FFFFFF', lambda key: '')
    normal = layout.build_profile(data['carousel']['normal'], render, True)
    small = layout.build_profile(data['carousel']['small'], render, True)
    assert normal['extraFields'][0]['shadow']['strength'] == 2
    assert small['extraFields'][2]['shadow']['alpha'] == 85
    assert 'mods/Driftkings/Carroucel/#957D5B.png' in normal['extraFields'][-1]['format']
    ui.write('Python 2.7 carousel defaults and macros: OK\n')

    sys.path.insert(0, base)
    from Driftkings.settings.player_panel_store import PlayerPanelStore
    directory = tempfile.mkdtemp(prefix='dk-panel-test-')
    try:
        store = PlayerPanelStore(os.path.join(directory, 'PlayerPanelPro'))
        data = store.load()
        data['profiles']['short']['extraFieldsLeft'] = []
        data['tab']['formatLeftNick'] = u'Player {{name}}'
        store.save(data)
        assert store.load() == data
    finally:
        shutil.rmtree(directory)
    ui.write('Python 2.7 unified panel JSON roundtrip: OK\n')

    from Driftkings.core import minimap
    import json
    from Driftkings.settings.minimap_store import FILES as minimap_files
    minimap_config = {}
    for filename in minimap_files:
        with open('res/configs/Driftkings/default/minimap_plugins/' + filename, 'rb') as stream:
            minimap_config.update(json.loads(stream.read().decode('utf-8')))
    minimap.validate(minimap_config)
    assert minimap.render('{{name}}', {'name': u'Jo\u00e3o'.encode('utf-8')}) == u'Jo\u00e3o'
    assert minimap.visible('client', False) is False
    ui.write('Python 2.7 minimap labels and configuration: OK\n')
