"""Font aliases use packaged resources without adding native Common modules."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from build_tools.validate_build_data import build_plan


class EmbeddedFontAssetTests(unittest.TestCase):
    def test_font_resources_ship_without_common_or_its_registration_package(self):
        plan = build_plan(ROOT)
        targets = {item['target'] for item in plan['assets']}
        for name in ('DriftkingsFont', 'VehicleType', 'DynamicDefault', 'DynamicOutline', 'ZurichCondMono'):
            self.assertIn('res/gui/fonts/driftkings/' + name + '.ttf', targets)
        self.assertTrue(any('net.openwg.gameface_' in path for path in plan['dependencies']))
        self.assertFalse(any('net.openwg.common_' in path for path in plan['dependencies']))
        self.assertFalse(any('openwg_packages/driftkings_fonts' in item['target']
                             for item in plan['assets'] + plan['python']))

    def test_flash_and_gameface_aliases_resolve_to_the_same_packaged_font(self):
        source = ROOT / 'flash_source/shared/as3/driftkings/utils/fontlibrary.as'
        embedded = dict((name, (source.parent / path).resolve()) for path, name in
                        re.findall(r'Embed\(source="([^"]+)", fontName="([^"]+)"', source.read_text()))
        css = ROOT / 'mod/res/gui/gameface/mods/driftkings/shared/fonts.css'
        gameface = dict((name, (ROOT / 'mod/res' / path).resolve()) for name, path in
                        re.findall(r"font-family: '([^']+)'; src: url\('coui://([^']+)'\)", css.read_text()))
        self.assertEqual(set(embedded), set(gameface))
        for name, path in embedded.items():
            self.assertEqual(path, gameface[name])
            self.assertTrue(path.is_file())
        for name in ('dkm', 'DriftkingsFont'):
            self.assertEqual(embedded[name].name, 'DriftkingsFont.ttf')
        # The legacy xvm/XVMSymbol aliases were retired in favour of dkm.
        self.assertFalse({'xvm', 'XVMSymbol'} & (set(embedded) | set(gameface)))
