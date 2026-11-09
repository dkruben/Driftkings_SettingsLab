"""Native crew transport and protected consumer contracts."""
import ast
import subprocess
import unittest

from build_tools import generate_ui_catalog as catalog
from build_tools.validate_build_data import build_plan


class NativeCrewCatalogTests(unittest.TestCase):
    def test_three_distinct_identities_and_only_crew_changes_transport(self):
        data = catalog.read_catalog()['GAMEFACE']
        baseline = subprocess.check_output(['git', 'show', 'fa8c6990:' + catalog.SOURCE], cwd=str(catalog.ROOT))
        tree = ast.parse(baseline.decode('utf-8'))
        old = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'GAMEFACE' for t in n.targets))
        self.assertEqual([name for name in data if data[name] != old[name]], ['DriftkingsCrewProgression'])
        names = ('DriftkingsHangarClock', 'DriftkingsMarksOnGunHangar', 'DriftkingsCrewProgression')
        native = [data[name] for name in names]
        self.assertTrue(all(x.get('transport') == 'native_user_missions' for x in native))
        urls = [x['plugin'] for x in native]
        identities = [(url.split('mono/')[1] if 'mono/' in url else '') or 'unknown' for url in urls]
        self.assertEqual(identities, ['unknown', 'driftkings/hangar_marks/marks_plugin.js',
                                      'driftkings/crew_progression/crew_plugin.js'])
        self.assertEqual(len(set(urls)), 3)
        self.assertEqual(len(set(x['resource'] for x in native)), 3)
        target = catalog.asset_target(native[-1]['plugin'])
        self.assertIn(target, {item['target'] for item in build_plan(catalog.ROOT)['assets']})
        self.assertTrue((catalog.ROOT / 'mod' / target).is_file())
        block = catalog.outputs()[catalog.BOOTSTRAP].split(catalog.START)[1].split(catalog.END)[0]
        for name in names:
            self.assertNotIn(name, block)
        legacy = [name for name, spec in data.items() if spec['owner'] is not None
                  and spec.get('transport', 'openwg') == 'openwg']
        self.assertEqual(len(legacy), 17)
        for name in legacy:
            self.assertIn(name, block)

    def test_calculations_patches_and_existing_integrations_preserved(self):
        paths = [
            'mod/res/scripts/client/driftkings/lobby/crew_management.py',
            'mod/res/scripts/client/driftkings/lobby/crew_progression.py',
            'mod/res/scripts/client/driftkings/core/crew_progression.py',
            'mod/res/scripts/client/driftkings/views/crew_progression_model.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/crew_details.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/common.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/main.py',
            'mod/res/scripts/client/driftkings/gameface/lobby/hangar_marks_of_excellence.py',
            'mod/res/gui/gameface/mods/driftkings/main/clock_plugin.js',
            'mod/res/gui/gameface/mods/driftkings/mono/driftkings/hangar_marks/marks_plugin.js',
            'mod/res/gui/gameface/mods/driftkings/crew_progression/model.html',
            'mod/res/gui/gameface/mods/driftkings/vehicle_carousel/carousel_native.js',
            'build_data/patches/carousel_2.4.2_ct.json', 'build_data/patches/crew_tooltip_2.4.2_ct.json',
            'build_data/build_config.json']
        for path in paths:
            before = subprocess.check_output(['git', 'show', 'fa8c6990:' + path], cwd=str(catalog.ROOT))
            self.assertEqual(before.replace(b'\r\n', b'\n'),
                             (catalog.ROOT / path).read_bytes().replace(b'\r\n', b'\n'), path)
