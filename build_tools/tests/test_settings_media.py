# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.settings.panel.api import SettingsAPI
from Driftkings.settings.panel.presenter import Presenter
from Driftkings.settings.panel.compatibility import TemplateAdapter
from Driftkings.settings.panel.media import ImagePreviews, resource_image, SIXTH_SENSE_EVENTS
from Driftkings.settings.panel.sound import SoundManager
from Driftkings.settings.registry import SettingsRegistry


class PreviewTests(unittest.TestCase):
    def test_images_are_local_bounded_and_cached_only_in_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = root / 'mods/configs/test.png'
            image.parent.mkdir(parents=True)
            image.write_bytes((ROOT / 'res/res/maps/icons/SixthSense/0.png').read_bytes())
            resolver = ImagePreviews(folder)
            url = resolver.resolve('mods/configs/test.png')
            self.assertTrue(url.startswith('data:image/png;base64,'))
            self.assertEqual(url, resolver.resolve('mods/configs/test.png'))
            self.assertEqual(len(resolver.cache), 1)
            self.assertEqual(resource_image('img://gui/maps/icon.png'), 'coui://gui/maps/icon.png')
            for value in ('https://example.com/a.png', 'gui/../a.png', 'mods/configs/../../test.png', 'mods/configs/missing.png'):
                self.assertEqual(resolver.resolve(value), '')
            image.write_bytes(b'not an image')
            self.assertEqual(resolver.resolve('mods/configs/test.png'), '')
            resolver.clear()
            self.assertFalse(resolver.cache)

    def test_preview_tracks_unsaved_selection_and_cancel(self):
        with tempfile.TemporaryDirectory() as folder:
            api = SettingsAPI(folder)
            handle = api.register_mod('images', name='Images')
            handle.add_dropdown('icon', 'Icon', values=[(0, 'First'), (1, 'Second')], default=0)
            handle._mod.index['icon'].preview = {'kind': 'image', 'images': ['coui://gui/a.png', 'coui://gui/b.png']}
            presenter = Presenter(api)
            self.assertEqual(presenter.state()['previews']['icon'], 'coui://gui/a.png')
            presenter.handle({'action': 'set', 'mod': 'images', 'key': 'icon', 'value': 1})
            self.assertEqual(presenter.state()['previews']['icon'], 'coui://gui/b.png')
            self.assertEqual(handle.get('icon'), 0)
            presenter.handle({'action': 'cancel'})
            self.assertEqual(presenter.state()['previews']['icon'], 'coui://gui/a.png')
            presenter.dispose()

    def test_sound_preview_uses_draft_event_and_stops_on_switch_and_close(self):
        class Config:
            ID = 'SixthSense'
            i18n = {}
            data = {'enabled': True, 'sixthSenseSound': 'SixthSense_06'}
            def createTemplate(self):
                return {'column1': [{'type': 'Dropdown', 'varName': 'sixthSenseSound',
                                    'options': [{'label': e} for e in SIXTH_SENSE_EVENTS],
                                    'optionValues': list(SIXTH_SENSE_EVENTS)}]}
        class Sound:
            def __init__(self, event): self.event, self.active = event, False
            def play(self): self.active = True
            def stop(self): self.active = False
        played = []
        def factory(event):
            sound = Sound(event)
            played.append(sound)
            return sound
        manager = SoundManager(factory)
        with tempfile.TemporaryDirectory() as folder, patch('Driftkings.settings.panel.sound.sound_manager', manager):
            api = SettingsAPI(folder)
            legacy = SettingsRegistry()
            config = Config()
            legacy.register(config)
            adapter = TemplateAdapter(api, legacy)
            adapter._register('SixthSense')
            presenter = Presenter(api)
            mod = api.registry.mods['legacy.SixthSense']
            field = next(c.id for c in mod.controls if c.type == 'dropdown')
            def action(kind, **kwargs):
                return presenter.handle(dict(action=kind, mod=mod.id, **kwargs))
            action('set', key=field, value=2)
            action('button', key='soundPreview')
            self.assertEqual(played[-1].event, 'SixthSense_03')
            self.assertEqual(config.data['sixthSenseSound'], 'SixthSense_06')
            action('set', key=field, value=4)
            self.assertFalse(played[-1].active)
            action('button', key='soundPreview')
            action('button', key='soundPreview')
            self.assertFalse(played[-2].active)
            self.assertTrue(played[-1].active)
            action('select')
            self.assertFalse(played[-1].active)
            action('button', key='soundPreview')
            action('cancel')
            self.assertFalse(played[-1].active)
            action('button', key='soundPreview')
            presenter.dispose()
            self.assertFalse(played[-1].active)

    def test_core_columns_are_stable_and_numeric_controls_are_sliders(self):
        with tempfile.TemporaryDirectory() as folder:
            api = SettingsAPI(folder)
            from Driftkings.settings.panel.core_page import install
            install(api)
            presenter = Presenter(api)
            schema = presenter.schema()
            self.assertEqual(schema, presenter.schema())
            controls = schema['mods'][0]['controls']
            self.assertEqual({c['column'] for c in controls if c['type'] != 'section'}, {0, 1})
            self.assertNotIn('number', [c['type'] for c in controls])


if __name__ == '__main__': unittest.main()
