import os
from support import RuntimeTest


class CarouselAssetCompatibilityTests(RuntimeTest):
    def test_old_and_current_template_paths_use_same_packaged_png(self):
        assets = self.load('core.carousel_assets')
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../mod/res'))
        images = assets.CarouselImages(root)
        paths = ['mods/Driftkings/Carroucel/battles.png', 'mods/driftkings/Carroucel/battles.png',
                 'gui/maps/Driftkings/Carroucel/battles.png', 'coui://gui/maps/driftkings/Carroucel/battles.png']
        paths = [assets.normalize_icon_paths(path) for path in paths]
        resolved = [images.resolve(path) for path in paths]
        self.assertTrue(resolved[0].startswith('data:image/png;base64,'))
        self.assertEqual(resolved, [resolved[0]] * len(paths))
        payload = images.collect({'1': {'normal': {'extraFields': [
            {'format': '<img src="%s">' % path} for path in paths]}}})
        self.assertEqual(set(payload), set(paths))
        self.assertTrue(all(payload.values()))
        self.assertEqual(images.resolve('mods/Driftkings/Carroucel/../battles.png'), '')
        self.assertEqual(images.resolve('https://example.org/battles.png'), '')

    def test_normalization_preserves_macros_and_only_changes_owned_icons(self):
        assets = self.load('core.carousel_assets')
        text = "<img src='mods/Driftkings/Carroucel/{{v.customColor}}.PNG'> <font face='PFDINMax'>{{v.WinRate}}</font>"
        expected = "<img src='gui/maps/driftkings/carroucel/{{v.customColor}}.png'> <font face='PFDINMax'>{{v.WinRate}}</font>"
        self.assertEqual(assets.normalize_icon_paths(text), expected)
        path = assets.normalize_icon_paths('gui/maps/driftkings/carroucel/#53B329.png')
        self.assertEqual(path, 'gui/maps/driftkings/carroucel/#53b329.png')
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../mod/res'))
        self.assertTrue(assets.CarouselImages(root).resolve(path))
