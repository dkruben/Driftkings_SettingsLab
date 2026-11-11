"""Actual PoC artifact versus the preserved 3D build; no client modification."""
import hashlib
import os
import struct
import zlib
from pathlib import Path
import unittest
import zipfile
from build_tools.generate_ui_catalog import asset_target, read_catalog
ROOT = Path(__file__).resolve().parents[2]


def swf_tags(raw):
    data = raw[:8] + zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw
    if data[:3] not in (b'CWS', b'FWS'):
        raise ValueError('Unsupported SWF format')
    rect_bits = data[8] >> 3
    offset = 8 + (5 + 4 * rect_bits + 7) // 8 + 4
    result = []
    while offset < len(data):
        header = struct.unpack_from('<H', data, offset)[0]
        offset += 2
        code, size = header >> 6, header & 63
        if size == 63:
            size = struct.unpack_from('<I', data, offset)[0]
            offset += 4
        payload = data[offset:offset + size]
        # ProductInfo's final uint64 is the compiler timestamp, not ABC/resources.
        result.append((code, payload[:-8] if code == 41 else payload))
        offset += size
        if code == 0:
            break
    return result


class NativeCarouselPackageTests(unittest.TestCase):
    def test_native_carousel_package_and_protected_baseline(self):
        reference = ROOT / 'build/debug/beta/0.1.8-beta.2/driftkings.wotmod'
        self.assertEqual(hashlib.sha256(reference.read_bytes()).hexdigest(), '7c50836f5f53eaf97a8c3a63433cc71e6889089b4d50b8fd98770888477ad89c')
        face = read_catalog()['GAMEFACE']
        with zipfile.ZipFile(os.environ['DK_TEST_WOTMOD']) as current, zipfile.ZipFile(reference) as old:
            spec = face['DriftkingsCarouselStats']
            for url in [spec['plugin'], spec['layout']] + spec['scripts'] + spec['styles'] + ['coui://gui/gameface/mods/driftkings/shared/fonts.css']:
                target = asset_target(url)
                self.assertEqual(current.read(target), (ROOT / 'mod' / target).read_bytes(), target)
            for name in old.namelist():
                if any(token in name for token in ('/main/clock', '/hangar_marks_of_excellence/', '/mono/driftkings/hangar_marks/',
                    '/crew_progression/', '/crew_details/', '/launcher/', '/maps/driftkings/carroucel/')) or name in (
                    'res/gui/gameface/_dist/production/mono/hangar/main/bundle.js',
                    'res/gui/gameface/_dist/production/mono/hangar/tooltips/bundle.js'):
                    self.assertEqual(current.read(name), old.read(name), name)
            expected = {'res/gui/gameface/_dist/production/mono/hangar/main/bundle.js': '0ad03065a96418af626a78b8ee2f8954fbc1accb899f5f328e9946cf0518eec3',
                        'res/gui/gameface/_dist/production/mono/hangar/tooltips/bundle.js': '190534383748a3daac3d8097a15d6436174dbcf12648540cb1f06aa0eef9a498'}
            for name, digest in expected.items():
                self.assertEqual(hashlib.sha256(current.read(name)).hexdigest(), digest)
            for name in ('res/gui/flash/driftkingsbattle.swf', 'res/gui/flash/driftkingspanels.swf'):
                self.assertEqual(swf_tags(current.read(name)), swf_tags(old.read(name)), name)
            for name in ('gameface/lobby/main', 'gameface/lobby/hangar_marks_of_excellence',
                         'gameface/lobby/crew_progression', 'gameface/lobby/crew_details'):
                target = 'res/scripts/client/driftkings/' + name + '.pyc'
                self.assertEqual(current.read(target)[8:], old.read(target)[8:], target)
            self.assertNotIn('res/gui/gameface/js/index.js', current.namelist())
            self.assertFalse(any('/tests/' in name or 'fault_injection' in name for name in current.namelist()))
            block = current.read('res/gui/gameface/mods/driftkings/shared/bootstrap.js').decode().split('/* GENERATED CATALOG START */')[1].split('/* GENERATED CATALOG END */')[0]
            self.assertNotIn('DriftkingsCarouselStats', block)
            for name in ('DriftkingsCrewDetails', 'DriftkingsFooterLauncher'):
                self.assertIn(name, block)
