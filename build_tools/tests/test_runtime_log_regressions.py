import ast
import copy
import json
import re
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS, ModuleType
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client/Driftkings'
sys.path.insert(0, str(CLIENT.parent))
from Driftkings._constants import GLOBAL, INFO_PANEL, MARKS_ON_GUN_BATTLE
from Driftkings.core.overlay import Align, ElementType, OverlayScene
from Driftkings.settings.loader import SettingsLoader
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults
from Driftkings.settings.store import merge


class RuntimeLogRegressions(unittest.TestCase):
    def test_component_common_imports_and_initialization_need_no_removed_analytics(self):
        # Reproduce the failing import/initializer without loading game APIs.
        common = ModuleType('Driftkings.common')
        for name in ('getPlayer', 'getEntity', 'replaceMacros', 'logError',
                     'getComparisonColor', 'remDups', 'events', 'curCV'):
            setattr(common, name, Mock())
        for relative in ('battle/battle_stat.py', 'components/sound_banks.py'):
            with self.subTest(component=relative):
                tree = ast.parse((CLIENT / relative).read_text(encoding='utf-8-sig'))
                tree.body = [node for node in tree.body if
                             isinstance(node, ast.ImportFrom) and node.module == 'Driftkings.common' or
                             isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'statistic_mod' for t in node.targets)]
                with patch.dict(sys.modules, {'Driftkings.common': common}):
                    exec(compile(tree, relative, 'exec'), {'config': NS(ID='test', version='0.1.0'),
                                                        '_config': NS(ID='test', version='0.1.0')})

    def test_existing_alignment_survives_actual_smart_update_without_rewriting_profile(self):
        tree = ast.parse((CLIENT / 'common/config/utils.py').read_text(encoding='utf-8-sig'))
        tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'smart_update']
        namespace = {'unicode': str}
        exec(compile(tree, 'smart_update', 'exec'), namespace)
        for component, key in (('InfoPanel', 'textPosition'), ('MarksOnGunBattle', 'panel')):
            with self.subTest(component=component), tempfile.TemporaryDirectory() as folder:
                loader = SettingsLoader(folder)
                directory = Path(loader.directory('default'))
                directory.mkdir()
                path = Path(loader.path(component))
                original = json.dumps({key: {'alignX': 'right', 'alignY': 'top', 'x': -123, 'y': 45}}).encode('utf-8')
                path.write_bytes(original)
                live = defaults(component)
                namespace['smart_update'](live, loader.load(component, defaults(component)))
                # smart_update encodes Python 2 unicode to UTF-8 byte strings.
                self.assertEqual(live[key]['alignX'], b'right')
                self.assertEqual(live[key]['alignY'], b'top')
                self.assertEqual((live[key]['x'], live[key]['y']), (-123, 45))
                self.assertEqual(path.read_bytes(), original)

    def view(self, component, relative):
        config = NS(ID=component, data=defaults(component))
        config.onApplySettings = lambda changes: config.data.update(merge(config.data, changes))
        service = SettingsService(SettingsData())
        scene, resetters = OverlayScene(), set()
        owner = NS(config=config, worker=NS(altMode=False))
        tree = ast.parse((CLIENT / relative).read_text(encoding='utf-8-sig'))
        tree.body = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Flash']
        namespace = dict(_component=lambda: owner, settings_service=service, overlays=scene,
                         ElementType=ElementType, Align=Align, GLOBAL=GLOBAL, INFO_PANEL=INFO_PANEL,
                         MARKS_ON_GUN_BATTLE=MARKS_ON_GUN_BATTLE, g_guiResetters=resetters,
                         GUI=NS(screenResolution=lambda: (1920, 1080)),
                         BattleReplay=NS(isPlaying=lambda: False), dependency=NS(descriptor=lambda _: None),
                         ISettingsCore=object())
        exec(compile(tree, relative, 'exec'), namespace)
        view = namespace['Flash']()
        view.settingsCore = NS(interfaceScale=NS(get=lambda: 1))
        return view, config, scene, resetters, service

    def test_marks_start_position_callback_and_resize_all_display_modes(self):
        for mode in (0, 1, 2, 3):
            with self.subTest(mode=mode):
                view, config, scene, resetters, service = self.view('MarksOnGunBattle', 'views/battle/gun_marks.py')
                config.data.update(displayMode=mode, showInBattle=True)
                view.startBattle()
                self.assertTrue(view.active)
                self.assertIn('MarksOnGunBattle', scene.elements)
                view.screenResize()
                scene.updated.emit('MarksOnGunBattle', {'x': 260, 'y': -180})
                self.assertEqual(config.data['panel']['x'], 260)
                view.stopBattle()
                self.assertFalse(resetters)
                self.assertFalse(scene.updated.listeners)
                self.assertFalse(scene.elements)

    def test_info_panel_resize_honors_each_alignment_and_keeps_config_keys(self):
        view, config, scene, resetters, service = self.view('InfoPanel', 'views/battle/info_panel.py')
        view.startBattle()
        for horizontal, vertical, x, y in (('left', 'top', 50, 60), ('right', 'bottom', -50, -60), ('center', 'center', -50, 60)):
            position = config.data['textPosition']
            position.update(alignX=horizontal, alignY=vertical, x=x, y=y)
            before = copy.deepcopy(position)
            view.applyConfig()
            view.screenResize()
            props = scene.elements['InfoPanel'][1]
            self.assertEqual((props['alignX'], props['alignY']), (horizontal, vertical))
            self.assertEqual((props['x'], props['y']), (x, y))
            self.assertEqual(position, before)
        view.stopBattle()
        self.assertFalse(resetters)
        self.assertFalse(scene.elements)

    def test_marks_text_render_after_hotkey_uses_configured_font_and_scale(self):
        for mode in (0, 1, 2, 3):
            with self.subTest(mode=mode):
                view, config, scene, resetters, service = self.view('MarksOnGunBattle', 'views/battle/gun_marks.py')
                config.data.update(displayMode=mode, showInBattle=True, font='CustomFont')
                config.data[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] = 150
                view.startBattle()
                for text in ('<font size="14">85.20%</font>', '<font size="20">86.00%</font>'):
                    view.set_text(text)
                    rendered = scene.elements['MarksOnGunBattle'][1]['text']
                    self.assertIn('face="CustomFont"', rendered)
                    self.assertEqual(float(re.search(r'size="([\d.]+)"', rendered).group(1)), 21 if '14' in text else 30)
                view.stopBattle()
