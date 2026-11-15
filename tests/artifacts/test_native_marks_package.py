"""Inspect the actual CT artifact; these checks do not claim runtime URL resolution."""
import os
from pathlib import Path
import unittest
import zipfile

from build_tools.generate_ui_catalog import read_catalog, asset_target

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
                    self.assertEqual(archive.read(target), (ROOT / 'mod' / target).read_bytes())
            bootstrap = archive.read('res/gui/gameface/mods/driftkings/shared/bootstrap.js').decode('utf-8')
            block = bootstrap.split('/* GENERATED CATALOG START */')[1].split('/* GENERATED CATALOG END */')[0]
            self.assertNotIn('DriftkingsHangarClock', block)
            self.assertNotIn('DriftkingsMarksOnGunHangar', block)
            legacy = [name for name, spec in face.items() if spec['owner'] is not None
                      and spec.get('transport', 'openwg') == 'openwg']
            self.assertEqual(len(legacy), 15)
            for name in legacy:
                self.assertIn(name, block)
