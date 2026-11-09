"""Four native contracts, preserved calculations and isolated carousel transport."""
import ast
import hashlib
import subprocess
import unittest
from pathlib import Path
from build_tools import generate_ui_catalog as catalog
from build_tools.validate_build_data import build_plan

ROOT = catalog.ROOT
BASE = '501aec366fa3ef51e895a745cf9735ccf5a1db38'


def previous(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=str(ROOT)).decode('utf-8').replace('\r\n', '\n')


class NativeCarouselCatalogTests(unittest.TestCase):
    def test_only_carousel_changes_and_four_resources_are_distinct(self):
        data = catalog.read_catalog()['GAMEFACE']
        tree = ast.parse(previous(catalog.SOURCE))
        old = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'GAMEFACE' for t in n.targets))
        self.assertEqual([n for n in data if data[n] != old[n]], ['DriftkingsCarouselStats'])
        native = [s for s in data.values() if s.get('transport') == 'native_user_missions']
        self.assertEqual(len(native), 4)
        self.assertEqual(len(set(s['resource'] for s in native)), 4)
        identities = [(s['plugin'].split('mono/')[1] if 'mono/' in s['plugin'] else '') or 'unknown' for s in native]
        self.assertEqual(len(set(identities)), 4)
        self.assertIn('driftkings/vehicle_carousel/carousel_plugin.js', identities)
        block = catalog.outputs()[catalog.BOOTSTRAP].split(catalog.START)[1].split(catalog.END)[0]
        for n, s in data.items():
            if s['owner'] is not None:
                self.assertEqual(n in block, s.get('transport', 'openwg') == 'openwg')
        self.assertEqual(sum(s['owner'] is not None and s.get('transport', 'openwg') == 'openwg' for s in data.values()), 16)
        plan = build_plan(ROOT)
        self.assertIn(catalog.asset_target(data['DriftkingsCarouselStats']['plugin']), {a['target'] for a in plan['assets']})
        self.assertEqual(len(plan['dependencies']), 2)

    def test_protected_sources_and_calculations_are_preserved(self):
        paths = ['mod/res/scripts/client/driftkings/lobby/vehicle_carousel.py',
                 'build_data/patches/carousel_2.4.2_ct.json', 'build_data/patches/crew_tooltip_2.4.2_ct.json',
                 'mod/res/scripts/client/driftkings/gameface/lobby/crew_progression.py',
                 'mod/res/scripts/client/driftkings/gameface/lobby/crew_details.py',
                 'mod/res/scripts/client/driftkings/gameface/lobby/main.py',
                 'mod/res/scripts/client/driftkings/gameface/lobby/hangar_marks_of_excellence.py',
                 'mod/res/gui/gameface/mods/driftkings/mono/driftkings/crew_progression/crew_plugin.js',
                 'mod/res/gui/gameface/mods/driftkings/mono/driftkings/hangar_marks/marks_plugin.js',
                 'mod/res/gui/gameface/mods/driftkings/main/clock_plugin.js',
                 'mod/res/gui/gameface/mods/driftkings/launcher/launcher.js',
                 'mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel.css',
                 'mod/res/gui/gameface/mods/driftkings/vehicle_carousel/model.html', 'build_data/build_config.json']
        for path in paths:
            self.assertEqual(previous(path), (ROOT / path).read_text(encoding='utf-8'), path)
        path = 'mod/res/scripts/client/driftkings/gameface/lobby/vehicle_carousel.py'
        old, new = ast.parse(previous(path)), ast.parse((ROOT / path).read_text())
        for name in ('get_view_config', 'CarouselController', 'install_carousel_layout', 'restore_carousel_layout'):
            select = lambda tree: ast.dump(next(n for n in tree.body if getattr(n, 'name', None) == name))
            self.assertEqual(select(old), select(new), name)
        path = 'mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel_native.js'
        math = lambda s: s.split('    function config()')[1].split('    function setData')[0]
        self.assertEqual(math(previous(path)), math((ROOT / path).read_text()))
