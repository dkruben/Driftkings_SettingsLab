"""Native marks identity and packaging contracts; no client installation."""
import copy
import unittest
from unittest.mock import patch

from build_tools import generate_ui_catalog as catalog
from build_tools.validate_build_data import build_plan
from support.baselines import baseline, file_hash, text_hash

# Content baseline recorded from commit 57881e7b (native hangar clock plugin).
BASE = baseline('native_clock')


class NativeHangarMarksTests(unittest.TestCase):
    def test_identity_transport_and_physical_url(self):
        face = catalog.read_catalog()['GAMEFACE']
        clock = face['DriftkingsHangarClock']
        marks = face['DriftkingsMarksOnGunHangar']
        self.assertEqual(marks.get('transport'), 'native_user_missions')
        identity = lambda url: (url.split('mono/')[1] if 'mono/' in url else '') or 'unknown'
        self.assertEqual(identity(clock['plugin']), 'unknown')
        self.assertEqual(identity(marks['plugin']), 'driftkings/hangar_marks/marks_plugin.js')
        self.assertNotEqual(clock['plugin'], marks['plugin'])
        self.assertNotEqual(clock['resource'], marks['resource'])
        self.assertNotEqual(identity(clock['plugin']), identity(marks['plugin']))
        legacy = [name for name, spec in face.items() if spec['owner'] is not None
                  and spec.get('transport', 'openwg') == 'openwg']
        self.assertEqual(len(legacy), 15)
        block = catalog.outputs()[catalog.BOOTSTRAP].split(catalog.START)[1].split(catalog.END)[0]
        self.assertNotIn('DriftkingsMarksOnGunHangar', block)
        for name in legacy:
            self.assertIn(name, block)
        target = catalog.asset_target(marks['plugin'])
        plan = build_plan(catalog.ROOT)
        self.assertIn(target, {item['target'] for item in plan['assets']})
        self.assertTrue((catalog.ROOT / 'mod' / target).is_file())
        self.assertEqual(len(plan['dependencies']), 2)
        bad = copy.deepcopy(catalog.read_catalog())
        bad['GAMEFACE']['DriftkingsMarksOnGunHangar']['plugin'] = clock['plugin']
        with patch.object(catalog, 'read_catalog', return_value=bad):
            with self.assertRaisesRegex(ValueError, 'Duplicate native SDK identity'):
                catalog.validate()

    def test_validated_clock_and_unrelated_marks_are_byte_preserved(self):
        paths = ['mod/res/scripts/client/driftkings/gameface/lobby/main.py',
                 'mod/res/gui/gameface/mods/driftkings/main/clock_plugin.js',
                 'mod/res/gui/gameface/mods/driftkings/main/clock.js',
                 'mod/res/gui/gameface/mods/driftkings/shared/marks_panel.js',
                 'mod/res/gui/gameface/mods/driftkings/hangar_marks_of_excellence/model.html',
                 'mod/res/gui/gameface/mods/driftkings/hangar_marks_of_excellence/marks.css',
                 'mod/res/scripts/client/driftkings/lobby/hangar_marks_of_excellence.py']
        for path in paths:
            self.assertEqual(BASE['files'][path], file_hash(path), path)

    def test_visual_renderer_body_is_preserved(self):
        path = 'mod/res/gui/gameface/mods/driftkings/hangar_marks_of_excellence/marks.js'
        after = (catalog.ROOT / path).read_text(encoding='utf-8')
        visual = lambda value: value.split('    function render(data, resized) {')[1].split('    function unit()')[0]
        self.assertEqual(BASE['sections']['marks_visual_renderer'], text_hash(visual(after)))
