"""Opt-in checks against actual packaged movies; not a substitute for in-game rendering."""
import hashlib
import json
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

    def test_distribution_excludes_temporary_diagnostics(self):
        for name in self.archive.namelist():
            lower = name.lower()
            self.assertNotIn('clock_diagnostics', lower, name)
            self.assertNotIn('loadinggeometry', lower, name)
            self.assertNotIn('/probe', lower, name)

    def test_remove_fog_ships_only_the_restored_production_components(self):
        # Remove Fog was restored (Phase 7, commit 8f227de7) under the WGMods moderation confirmation: disabled by
        # default, explicit player opt-in. The package carries the controller and the native helper only. The
        # auxiliary Driftkings.RemoveFog.wotmod is generated on the player's machine and is never packaged.
        names = self.archive.namelist()
        self.assertNotIn('removefog.wotmod', ' '.join(name.lower() for name in names))
        fog = {name for name in names if '/fog/' in name.lower() or name.lower().endswith('/fog_package.pyc')}
        self.assertEqual(fog, {
            'res/gui/driftkings/fog/Driftkings.FogPackage.exe',
            'res/gui/driftkings/fog/helper.json',
            'res/scripts/client/driftkings/core/fog_package.pyc',
        })

    def test_remove_fog_helper_manifest_matches_the_shipped_executable(self):
        manifest = json.loads(self.archive.read('res/gui/driftkings/fog/helper.json').decode('utf-8'))
        executable = self.archive.read('res/gui/driftkings/fog/Driftkings.FogPackage.exe')
        self.assertEqual(manifest['schema'], 1)
        self.assertEqual(manifest['size'], len(executable))
        self.assertEqual(manifest['sha256'], hashlib.sha256(executable).hexdigest())

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
            for alias in ('dkm', 'DriftkingsFont'):
                self.assertIn(0x115, fonts[alias], '%s: missing rating glyph in %s' % (movie, alias))

    def test_ttf_resources_ship_without_native_registration_package(self):
        names = self.archive.namelist()
        self.assertFalse(any('openwg_packages/driftkings_fonts' in name for name in names))
        for name in ('DriftkingsFont', 'VehicleType', 'DynamicDefault', 'DynamicOutline', 'ZurichCondMono'):
            self.assertGreater(len(self.archive.read('res/gui/fonts/driftkings/' + name + '.ttf')), 0)
