"""Inspect the actual CT artifact; these checks do not claim runtime URL resolution."""
import os
from pathlib import Path
import unittest
import zipfile

from build_tools.generate_ui_catalog import read_catalog, asset_target
TEXT_SUFFIXES = ('.js', '.css', '.json', '.html', '.svg', '.xml', '.py', '.md', '.yml', '.as')


def assert_same_source(testcase, packaged, source, name):
    """Packaged text equals its source modulo line endings: canonical sources are LF (.gitattributes), while an
    older CRLF working copy holds the same text. Binary assets must match byte for byte."""
    if name.endswith(TEXT_SUFFIXES):
        packaged, source = packaged.replace(b'\r\n', b'\n'), source.replace(b'\r\n', b'\n')
    testcase.assertEqual(packaged, source, name)


ROOT = Path(__file__).resolve().parents[2]


class NativeMarksArtifactTests(unittest.TestCase):
    def test_native_resources_and_exclusive_bootstrap(self):
        face = read_catalog()['GAMEFACE']
        with zipfile.ZipFile(os.environ['DK_TEST_WOTMOD']) as archive:
            names = set(archive.namelist())
            self.assertNotIn('res/gui/gameface/js/index.js', names)
            self.assertFalse(any('/tests/' in name for name in names))
            for name in ('DriftkingsHangarClock', 'DriftkingsMarksOnGunHangar'):
                spec = face[name]
                self.assertEqual(spec['transport'], 'native_user_missions')
                for url in [spec['plugin'], spec['layout']] + spec['scripts'] + spec['styles']:
                    target = asset_target(url)
                    self.assertIn(target, names)
                    assert_same_source(self, archive.read(target), (ROOT / 'mod' / target).read_bytes(), target)
            bootstrap = archive.read('res/gui/gameface/mods/driftkings/shared/bootstrap.js').decode('utf-8')
            block = bootstrap.split('/* GENERATED CATALOG START */')[1].split('/* GENERATED CATALOG END */')[0]
            self.assertNotIn('DriftkingsHangarClock', block)
            self.assertNotIn('DriftkingsMarksOnGunHangar', block)
            # The historical expectation of 15 OpenWG-injected consumers is obsolete after the native migration:
            # the catalog declares no OpenWG transport and every owned feature is native or an owned window.
            legacy = [name for name, spec in face.items() if spec['owner'] is not None
                      and spec.get('transport') == 'openwg']
            self.assertEqual(legacy, [])
            native = [name for name, spec in face.items() if spec.get('transport') in
                      ('native_user_missions', 'native_battle_results', 'own_window', 'native_document')]
            self.assertEqual(len(native), 20)
