# -*- coding: utf-8 -*-
"""Export real frontend contracts using the shared settings test fixture."""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
from support.localized_controls import LocalizedControlsFixture
from support import CLIENT, module


def export(language='en'):
    test = LocalizedControlsFixture('setUp')
    test.setUp()
    try:
        test.Base.onPanelOpened = lambda self: None
        registry = test.settings_registry(language)
        for name in ('driftkings.settings','driftkings.settings.panel','driftkings.settings.definitions'):
            sys.modules[name].__name__ = name
        sys.modules['driftkings.i18n'] = module(__path__=[os.path.join(CLIENT, 'i18n')])
        sys.modules['driftkings.i18n'].__name__ = 'driftkings.i18n'
        resources = test.load('i18n.resources')
        def reader(code):
            with open(os.path.join(ROOT, 'mod/res/mods/driftkings/text', code + '.yml'), 'rb') as stream:
                return stream.read()
        resources.resources.reader = reader
        resources.resources.cache = {}
        class Images(object):
            def resolve(self, path):
                return path or ''
            def clear(self):
                pass
        media = sys.modules['driftkings.settings.panel.media']
        media.ImagePreviews = Images
        media.resource_image = lambda path: path
        sys.modules['driftkings.settings.panel'].VERSION = 'test'
        with tempfile.TemporaryDirectory(prefix='dk-panel-test-') as directory:
            api = test.load('settings.panel.api').SettingsAPI(directory)
            api.client_language = language
            api.language, api.strings = test.load('i18n.panel').load(language)
            test.load('settings.panel.core_page').install(api)
            test.load('settings.panel.sections').SectionPanelBinding(api, registry).populate()
            presenter = test.load('settings.panel.presenter').Presenter(api)
            return {'schema': presenter.schema(), 'state': presenter.state()}
    finally:
        test.doCleanups()
        test.tearDown()


if __name__ == '__main__':
    print(json.dumps(export(sys.argv[1] if len(sys.argv) > 1 else 'en')))
