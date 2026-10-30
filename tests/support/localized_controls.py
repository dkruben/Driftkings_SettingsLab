# -*- coding: utf-8 -*-
"""Every live settings declaration resolves against every bundled language."""
import copy
import os
import sys

from support import CLIENT, ROOT, RuntimeTest, module


class LocalizedControlsFixture(RuntimeTest):
    def setUp(self):
        super(LocalizedControlsFixture, self).setUp()
        for name, relative in (('driftkings.settings', 'settings'),
                               ('driftkings.settings.panel', 'settings/panel'),
                               ('driftkings.settings.definitions', 'settings/definitions')):
            sys.modules[name] = module(__path__=[os.path.join(CLIENT, relative)])
        self.defaults = self.load('settings.default_values').DEFAULTS
        # Load bundled colours before installing the icon-directory-only ResMgr stub.
        self.load('common.utils.color_rating_data')
        self.schema = self.load('settings.controls_schema')
        self.parser = self.load('core.locale_catalog').parse_catalog
        self.documents = {}
        for code, _ in self.load('locale_support').LANGUAGES:
            with open(os.path.join(ROOT, 'mod/res/mods/driftkings/text', code + '.yml'), 'rb') as stream:
                self.documents[code] = self.parser(stream.read())['TEXT']
        test = self
        class Base(object):
            NAME = None
            COLUMNS = ((), ())
            def __init__(self):
                self.data = copy.deepcopy(test.defaults.get(self.NAME, {}))
                self.i18n = dict(test.text.get('common', {}))
                self.i18n.update(test.text.get(self.NAME, {}))
            def getControlColumns(self):
                return self.COLUMNS
        self.Base = Base
        sys.modules['driftkings.settings.definitions.base'] = module(SectionDefinition=Base)
        sys.modules['driftkings.settings.service'] = module(
            settings_service=module(getComponentDict=lambda config: config.data))
        sys.modules['driftkings.settings.panel.media'] = module(SIXTH_SENSE_EVENTS=('sixthSense',))
        class Names(object):
            def __getattr__(self, key):
                return key
        for name, stub in (
                ('ResMgr', module(openSection=lambda path: module(keys=lambda: ['0.png', '1.png']))),
                ('gui', module(__path__=[])),
                ('gui.Scaleform', module(__path__=[])),
                ('gui.Scaleform.locale', module(__path__=[])),
                ('gui.Scaleform.locale.SETTINGS', module(SETTINGS=Names())),
                ('helpers', module(i18n=module(makeString=lambda text: text)))):
            previous = sys.modules.get(name)
            sys.modules[name] = stub
            self.addCleanup(self.restore_external, name, previous)
        self.definitions = []
        for area in ('battle', 'lobby', 'components'):
            for filename in sorted(os.listdir(os.path.join(CLIENT, 'settings/definitions', area))):
                if not filename.endswith('.py') or filename == '__init__.py':
                    continue
                api = self.load('settings.definitions.' + area + '.' + filename[:-3])
                # Python 2 compatibility names used by two existing definitions.
                api.xrange = range
                api.basestring = type('')
                cls = next(value for value in vars(api).values()
                           if isinstance(value, type) and value is not Base and issubclass(value, Base))
                self.definitions.append(cls)

    @staticmethod
    def restore_external(name, previous):
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous

    def settings_registry(self, language='en'):
        self.text = self.documents[language]
        metadata = self.load('settings.settings_data')
        key_names = set()
        def collect(value):
            if isinstance(value, (list, tuple)):
                for item in value:
                    collect(item)
            elif isinstance(value, (str, type(u''))):
                key_names.add(value)
        for name, keys in metadata.HOTKEY_FIELDS.items():
            for key in keys:
                collect(self.defaults[name][key])
        previous = sys.modules.get('Keys')
        sys.modules['Keys'] = module(**dict((key, index + 1) for index, key in enumerate(sorted(key_names))))
        self.addCleanup(self.restore_external, 'Keys', previous)
        process = self.load('settings.hotkeys').processHotKeys
        registry = self.load('settings.registry').SettingsRegistry()
        service = sys.modules['driftkings.settings.service'].settings_service
        def apply(config, changes):
            updated = copy.deepcopy(config.data)
            updated.update(changes)
            if hasattr(config, 'normalize_changes'):
                updated = config.normalize_changes(updated, changes)
            config.data = updated
        service.apply = apply
        for definition in self.definitions:
            config = definition()
            if hasattr(config, 'normalize_loaded'):
                config.data = config.normalize_loaded(config.data)
            process(config.data, metadata.default_keys(config.NAME), 'read')
            registry.register(config)
            before = registry.describe(config.NAME)
            after = registry.apply(config.NAME, copy.deepcopy(before['values']))
            self.assertEqual(before['values'], after['values'], config.NAME)

        return registry
