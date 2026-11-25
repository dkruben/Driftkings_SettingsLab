"""Actual package checks; no installation or claim of CT JS execution."""
import os
from pathlib import Path
import unittest
import zipfile

from build_tools.generate_ui_catalog import asset_target, read_catalog
TEXT_SUFFIXES = ('.js', '.css', '.json', '.html', '.svg', '.xml', '.py', '.md', '.yml', '.as')


def assert_same_source(testcase, packaged, source, name):
    """Packaged text equals its source modulo line endings: canonical sources are LF (.gitattributes), while an
    older CRLF working copy holds the same text. Binary assets must match byte for byte."""
    if name.endswith(TEXT_SUFFIXES):
        packaged, source = packaged.replace(b'\r\n', b'\n'), source.replace(b'\r\n', b'\n')
    testcase.assertEqual(packaged, source, name)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'build/reference/fase3c-09b70a3b4a48194514393fa1f7cae1b7281a42434d1cbae9b78ce064cf4c9bec.wotmod'


class NativeCrewPackageTests(unittest.TestCase):
    def test_native_crew_and_protected_resources_in_actual_package(self):
        # Historical fase3c reference package is not retained in this workspace; never substitute another package.
        if not REFERENCE.is_file():
            self.skipTest('Historical reference unavailable: build/reference/fase3c-*.wotmod')
        face = read_catalog()['GAMEFACE']
        with zipfile.ZipFile(os.environ['DK_TEST_WOTMOD']) as current, zipfile.ZipFile(REFERENCE) as before:
            spec = face['DriftkingsCrewProgression']
            self.assertEqual(spec['transport'], 'native_user_missions')
            for url in [spec['plugin'], spec['layout']] + spec['scripts']:
                target = asset_target(url)
                assert_same_source(self, current.read(target), (ROOT / 'mod' / target).read_bytes(), target)
            for target in before.namelist():
                if any(token in target for token in ('/main/clock', '/hangar_marks_of_excellence/',
                        '/mono/driftkings/hangar_marks/', '/crew_details/')) or target in (
                        'res/gui/gameface/_dist/production/mono/hangar/main/bundle.js',
                        'res/gui/gameface/_dist/production/mono/hangar/tooltips/bundle.js'):
                    self.assertEqual(current.read(target), before.read(target), target)
            self.assertNotIn('res/gui/gameface/js/index.js', current.namelist())
            self.assertFalse(any('/tests/' in target for target in current.namelist()))
            block = current.read('res/gui/gameface/mods/driftkings/shared/bootstrap.js').decode('utf-8').split('/* GENERATED CATALOG START */')[1].split('/* GENERATED CATALOG END */')[0]
            self.assertNotIn('DriftkingsCrewProgression', block)
            self.assertNotIn('DriftkingsCarouselStats', block)
            for name in ('DriftkingsCrewDetails', 'DriftkingsFooterLauncher'):
                self.assertIn(name, block)
