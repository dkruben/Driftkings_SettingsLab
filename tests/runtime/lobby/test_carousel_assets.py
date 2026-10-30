import os
from support import RuntimeTest, module, source


class CarouselAssetCompatibilityTests(RuntimeTest):
    def test_svg_icons_load_directly_without_resmgr_or_base64(self):
        def reject_read(path):
            raise AssertionError('SVG must not be read through ResMgr')
        api = source('core/carousel_assets.py', {'ResMgr': module(openSection=reject_read)})
        images = api['CarouselImages']()
        names = ('battles', 'wins', 'damage', 'shooter', 'wn8',
                 '#1ea2d2', '#53b329', '#957d5b', '#b87ab2', '#f13439')
        paths = [api['RESOURCE_ROOT'] + name + '.svg' for name in names]
        payload = images.collect({'1': {'normal': {'extraFields': [
            {'format': '<img src="%s">' % path} for path in paths]}}})
        self.assertEqual(payload, {})
        for path in paths:
            self.assertEqual(images.resolve(path), 'coui://' + path.replace('#', '%23'))
        self.assertEqual(images.cache, {})
        self.assertEqual(images.missing, set())
        self.assertEqual(images.resolve('https://example.org/battles.svg'), '')
        self.assertEqual(images.resolve(api['RESOURCE_ROOT'] + '../battles.svg'), '')

    def test_svg_path_normalization_preserves_template_macros(self):
        assets = self.load('core.carousel_assets')
        self.assertEqual(assets.normalize_icon_paths('img://gui/maps/Driftkings/Carroucel/BATTLES.SVG'),
                         assets.RESOURCE_ROOT + 'battles.svg')
        self.assertEqual(assets.normalize_icon_paths('gui/maps/Driftkings/Carroucel/{{v.c_type}}.SVG'),
                         assets.RESOURCE_ROOT + '{{v.c_type}}.svg')

    def test_old_and_current_template_paths_use_same_packaged_png(self):
        assets = self.load('core.carousel_assets')
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../mod/res'))
        images = assets.CarouselImages(root)
        paths = ['mods/Driftkings/Carroucel/mark_0.png', 'mods/driftkings/Carroucel/mark_0.png',
                 'gui/maps/Driftkings/Carroucel/mark_0.png', 'coui://gui/maps/driftkings/Carroucel/mark_0.png']
        paths = [assets.normalize_icon_paths(path) for path in paths]
        resolved = [images.resolve(path) for path in paths]
        self.assertTrue(resolved[0].startswith('data:image/png;base64,'))
        self.assertEqual(resolved, [resolved[0]] * len(paths))
        payload = images.collect({'1': {'normal': {'extraFields': [
            {'format': '<img src="%s">' % path} for path in paths]}}})
        self.assertEqual(set(payload), set(paths))
        self.assertTrue(all(payload.values()))
        self.assertEqual(images.resolve('mods/Driftkings/Carroucel/../mark_0.png'), '')
        self.assertEqual(images.resolve('https://example.org/mark_0.png'), '')

    def test_normalization_preserves_macros_and_only_changes_owned_icons(self):
        assets = self.load('core.carousel_assets')
        text = "<img src='mods/Driftkings/Carroucel/{{v.customColor}}.PNG'> <font face='PFDINMax'>{{v.WinRate}}</font>"
        expected = "<img src='gui/maps/driftkings/carroucel/{{v.customColor}}.png'> <font face='PFDINMax'>{{v.WinRate}}</font>"
        self.assertEqual(assets.normalize_icon_paths(text), expected)
        path = assets.normalize_icon_paths('gui/maps/driftkings/carroucel/MARK_0.png')
        self.assertEqual(path, 'gui/maps/driftkings/carroucel/mark_0.png')
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../mod/res'))
        self.assertTrue(assets.CarouselImages(root).resolve(path))
