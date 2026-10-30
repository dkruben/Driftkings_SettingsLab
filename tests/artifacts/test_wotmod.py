"""Opt-in checks against actual packaged movies; not a substitute for in-game rendering."""
import os
from pathlib import Path
import re
import struct
import unittest
import zipfile

from build_tools.vehicle_markers_patch import swf_parts, tag_payload

ROOT = Path(__file__).resolve().parents[2]
MOVIES = ('res/gui/flash/driftkingsbattle.swf', 'res/gui/flash/battleVehicleMarkersApp.swf')


def embedded_fonts(raw):
    fonts = {}
    for kind, tag in swf_parts(raw)[1]:
        if kind not in (48, 75):  # DefineFont2 / DefineFont3
            continue
        data = tag_payload(tag)
        flags, name_length = data[2], data[4]
        name = data[5:5 + name_length].rstrip(b'\0').decode('utf-8')
        count = struct.unpack_from('<H', data, 5 + name_length)[0]
        offsets = 7 + name_length
        width = 4 if flags & 8 else 2
        code_offset = struct.unpack_from('<I' if width == 4 else '<H', data, offsets + count * width)[0]
        code_width = 2 if flags & 4 else 1
        codes = set(struct.unpack_from('<H' if code_width == 2 else '<B', data,
                                       offsets + code_offset + index * code_width)[0] for index in range(count))
        fonts[name] = codes
    return fonts


class PackagedFontTests(unittest.TestCase):
    def setUp(self):
        self.archive = zipfile.ZipFile(os.environ['DK_TEST_WOTMOD'])
        self.addCleanup(self.archive.close)

    def test_both_movies_preserve_every_declared_font_name(self):
        source = (ROOT / 'flash_source/shared/as3/driftkings/utils/fontlibrary.as').read_text(encoding='utf-8')
        expected = set(re.findall(r'fontName="([^"]+)"', source))
        self.assertTrue(expected)
        for movie in MOVIES:
            actual = embedded_fonts(self.archive.read(movie))
            self.assertTrue(expected.issubset(actual), '%s: missing fonts %s' % (movie, sorted(expected - set(actual))))

    def test_rating_glyph_survives_native_marker_injection(self):
        for movie in MOVIES:
            fonts = embedded_fonts(self.archive.read(movie))
            for alias in ('dkm', 'DriftkingsFont', 'xvm', 'XVMSymbol'):
                self.assertIn(0x115, fonts[alias], '%s: missing rating glyph in %s' % (movie, alias))

    def test_ttf_resources_ship_without_native_registration_package(self):
        names = self.archive.namelist()
        self.assertFalse(any('openwg_packages/driftkings_fonts' in name for name in names))
        for name in ('DriftkingsFont', 'VehicleType', 'DynamicDefault', 'DynamicOutline', 'ZurichCondMono'):
            self.assertGreater(len(self.archive.read('res/gui/fonts/driftkings/' + name + '.ttf')), 0)
