import ast
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings._constants import GLOBAL, MARKS_ON_GUN_HANGAR, MINIMAP_PLUGINS
from Driftkings.settings.service import SettingsService, SettingsChanges, affects
from Driftkings.settings.settings_data import SettingsData, defaults
from Driftkings.views.hangar.common import HangarController, card_payload


def load(path, name, namespace):
    tree = ast.parse((CLIENT / 'Driftkings' / path).read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if getattr(node, 'name', None) == name]
    exec(compile(tree, path, 'exec'), namespace)
    return namespace[name]


class MarksHangarSettingsTests(unittest.TestCase):
    def setUp(self):
        self.service = SettingsService(SettingsData())
        self.config = NS(ID=MARKS_ON_GUN_HANGAR.ID, data=defaults(MARKS_ON_GUN_HANGAR.ID))
        self.ns = dict(settings_service=self.service, MARKS_ON_GUN_HANGAR=MARKS_ON_GUN_HANGAR,
                       GLOBAL=GLOBAL, affects=affects, HangarController=HangarController)

    def test_visual_options_use_current_scale_without_mutating_settings_or_rebuilding_vehicle(self):
        color = Mock(side_effect=lambda rating, value, scale: '%s:%s' % (scale, value))
        self.ns['getStatisticColor'] = color
        build_config = load('views/hangar/gun_marks.py', 'get_view_config', self.ns)
        self.config.data.update(compactMode=True, colorRating=2)
        before = deepcopy(self.config.data)
        panel = build_config(self.config)
        self.assertEqual(panel['height'], 194.0)
        self.assertEqual(panel['starColor85'], '2:85')
        self.assertEqual(panel['backgroundColor'], before['card']['backgroundColor'])
        self.assertEqual(self.config.data, before)
        previous = {'config':dict(panel, visible=True), 'vehicle':'T-34', 'average':'1500'}
        build_vehicle = Mock()
        self.config.data['panel']['x'] = 100
        moved = card_payload(previous, True, True, lambda:build_config(self.config), build_vehicle)
        self.assertEqual(moved['config']['x'], 100)
        self.assertEqual(moved['vehicle'], 'T-34')
        build_vehicle.assert_not_called()
        self.config.data.update(compactMode=False, enabled=False)
        self.assertGreaterEqual(build_config(self.config)['height'], 260)
        self.assertFalse(build_config(self.config)['visible'])

    def test_scoped_notifications_are_selective_and_disconnect_on_stop(self):
        cls = load('views/hangar/gun_marks.py', 'MarksOnGunHangarController', self.ns)
        controller = cls()
        class Parent: pass
        parent = Parent()
        child = NS(refreshSettings=Mock())
        controller.views[parent] = child
        controller.start()
        controller.start()
        signal = self.service.onModSettingsChanged
        changes = SettingsChanges({'panel':{'x':80}}, [('panel','x')])
        signal.emit(MINIMAP_PLUGINS.NAME, changes)
        signal.emit(MARKS_ON_GUN_HANGAR.NAME, SettingsChanges({'showInStatistic':False}))
        child.refreshSettings.assert_not_called()
        signal.emit(MARKS_ON_GUN_HANGAR.NAME, changes)
        child.refreshSettings.assert_called_once_with(changes)
        self.assertEqual(child.refreshSettings.call_args[0][0].paths, changes.paths)
        controller.stop()
        controller.stop()
        signal.emit(MARKS_ON_GUN_HANGAR.NAME, changes)
        child.refreshSettings.assert_called_once()

    def test_legacy_position_controls_normalize_without_mutating_input_or_preferences(self):
        saved = Mock()
        class Storage:
            def onApplySettings(self, values): saved(values)
        self.ns['ComponentSettings'] = Storage
        cls = load('settings/templates/lobby/gun_marks.py', 'MarksOnGunHangarSettings', self.ns)
        owner = cls()
        owner.data = deepcopy(self.config.data)
        values = {'positionX':'42', 'positionY':'-80'}
        owner.onApplySettings(values)
        panel = dict(self.config.data['panel'], x=42.0, y=-80.0)
        saved.assert_called_once_with({'panel':panel})
        self.assertEqual(values, {'positionX':'42', 'positionY':'-80'})
        self.assertEqual(owner.data, self.config.data)
        saved.reset_mock()
        with self.assertRaises(ValueError): owner.onApplySettings({'positionX':'invalid'})
        saved.assert_not_called()


if __name__ == '__main__':
    unittest.main()
