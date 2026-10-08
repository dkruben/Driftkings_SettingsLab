import ast
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

from settings_support import settings_globals

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings._constants import MARKS_ON_GUN_TECH_TREE, MINIMAP_PLUGINS
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults


class Transaction:
    def __init__(self):
        self.values = []
        self.fail = False

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.fail:
            raise RuntimeError('transaction failed')

    def _setString(self, index, value):
        self.values.append(value)


class ViewBase:
    def __init__(self, settings):
        self.model = Transaction()

    def getViewModel(self):
        return self.model


class MarksTreeSettingsTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'source/scripts/client/Driftkings/lobby/gun_marks_tree.py'
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body = [node for node in tree.body
                     if isinstance(node, ast.ClassDef) and node.name == 'TechTreeController'
                     or isinstance(node, ast.FunctionDef) and node.name == 'make_payload']
        self.config = NS(ID='MarksOnGunTechTree', data=defaults('MarksOnGunTechTree'))
        self.service = SettingsService(SettingsData())
        self.records = {1: {'percent': 65, 'tier': 8, 'mastery': 3},
                        2: {'percent': 90, 'tier': 10, 'mastery': 4}}
        self.read = Mock(side_effect=lambda vehicle_id: dict(self.records[vehicle_id]))
        self.views = {}
        self.ns = dict(json=json, config=self.config, LOG=Mock(), _views=self.views,
                       vehicle_marks=self.read,
                       getStatisticColor=lambda metric, value, scale: '#%06d' % scale)
        settings_globals(self.ns, 'lobby.gun_marks_tree')
        self.ns['settings_service'] = self.service
        exec(compile(tree, str(path), 'exec'), self.ns)
        self.controller = self.ns['TechTreeController']()
        self.controller.start()
        self.addCleanup(self.controller.stop)

        path = ROOT / 'source/scripts/client/Driftkings/views/hangar/gun_marks_tree.py'
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        view = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef) and node.name == 'MarksView')
        tree.body = [view]
        namespace = dict(ViewImpl=ViewBase, MarksModel=lambda: None,
                         ViewSettings=lambda *args, **kwargs: None,
                         _component=lambda: NS(make_payload=self.ns['make_payload']))
        exec(compile(tree, str(path), 'exec'), namespace)
        self.view_type = namespace['MarksView']
        self.view = self.view_type(1)
        self.views['open'] = self.view

    def payload(self, view=None):
        return json.loads((view or self.view).model.values[-1])

    def test_visual_changes_reuse_dossiers_and_color_follows_selected_scale(self):
        self.view.refresh([1, 2])
        self.assertEqual(self.read.call_count, 2)
        self.service.apply(self.config, {'badgeOffsetX': 12, 'showInTechTreeMastery': False}, persist=False)
        self.assertEqual(self.read.call_count, 2)
        payload = self.payload()
        self.assertEqual(payload['offsetX'], 12)
        self.assertFalse(payload['showMastery'])
        self.service.apply(self.config, {'colorRating': 2}, persist=False)
        self.assertEqual(self.read.call_count, 2)
        self.assertEqual(self.payload()['vehicles']['1']['color'], '#000002')
        self.assertEqual(self.payload()['vehicles']['1']['percent'], 65)
        self.assertNotIn('color', self.view._records[1])

    def test_native_update_and_nation_switch_renew_records(self):
        self.view.refresh([1, 2])
        self.records[1]['percent'] = 70
        self.view.refresh()
        self.assertEqual(self.read.call_count, 4)
        self.assertEqual(self.payload()['vehicles']['1']['percent'], 70)
        self.view.refresh([2])
        self.assertEqual(self.read.call_count, 5)
        self.assertEqual(set(self.payload()['vehicles']), {'2'})
        self.assertEqual(set(self.view._records), {2})

    def test_disabled_tree_does_not_read_and_native_updates_invalidate_old_values(self):
        self.view.refresh([1])
        self.service.apply(self.config, {'enabled': False}, persist=False)
        self.assertFalse(self.payload()['enabled'])
        self.assertEqual(self.payload()['vehicles'], {})
        self.records[1]['percent'] = 80
        self.view.refresh()
        self.assertEqual(self.read.call_count, 1)
        self.service.apply(self.config, {'enabled': True}, persist=False)
        self.assertEqual(self.read.call_count, 2)
        self.assertEqual(self.payload()['vehicles']['1']['percent'], 80)

    def test_missing_dossier_is_retried_without_discarding_other_records(self):
        second = self.records.pop(2)
        self.view.refresh([1, 2])
        self.assertEqual(set(self.payload()['vehicles']), {'1'})
        self.records[2] = second
        self.view.refresh(reload=False)
        self.assertEqual(self.read.call_count, 3)
        self.assertEqual(set(self.payload()['vehicles']), {'1', '2'})

    def test_identical_payload_is_not_published_and_failed_transaction_can_retry(self):
        self.view.refresh([1, 2])
        self.view.refresh([2, 1])
        self.assertEqual(len(self.view.model.values), 1)
        self.config.data['badgeOffsetX'] = 77
        self.view.model.fail = True
        with self.assertRaises(RuntimeError):
            self.view.refresh(reload=False)
        self.view.model.fail = False
        self.view.refresh(reload=False)
        self.assertEqual(len(self.view.model.values), 3)
        self.assertEqual(self.payload()['offsetX'], 77)

    def test_closed_and_reopened_views_do_not_reuse_stale_records(self):
        self.view.refresh([1])
        del self.views['open']
        self.records[1]['percent'] = 91
        self.service.apply(self.config, {'badgeOffsetY': 18}, persist=False)
        self.assertEqual(self.read.call_count, 1)
        reopened = self.view_type(2)
        self.views['open'] = reopened
        reopened.refresh([1])
        self.assertEqual(self.read.call_count, 2)
        self.assertEqual(self.payload(reopened)['vehicles']['1']['percent'], 91)
        self.assertEqual(self.payload(reopened)['offsetY'], 18)

    def test_scoped_subscription_lifecycle_and_fault_isolation(self):
        self.views.clear()
        broken, good = Mock(), Mock()
        broken.refresh.side_effect = RuntimeError('disposed')
        self.views.update(broken=broken, good=good)
        self.controller.start()
        signal = self.service.onModSettingsChanged
        self.assertEqual(len(signal._listeners), 1)
        signal.emit(MINIMAP_PLUGINS.NAME, {'enabled': False})
        signal.emit(MARKS_ON_GUN_TECH_TREE.NAME, {'unrelated': 10})
        good.refresh.assert_not_called()
        signal.emit(MARKS_ON_GUN_TECH_TREE.NAME, {'badgeFontSize': 20})
        good.refresh.assert_called_once_with(reload=False)
        self.ns['LOG'].exception.assert_called_once()
        self.controller.stop()
        self.controller.stop()
        self.assertFalse(signal._listeners)
        signal.emit(MARKS_ON_GUN_TECH_TREE.NAME, {'enabled': True})
        good.refresh.assert_called_once()
        self.controller.start()
        self.assertEqual(len(signal._listeners), 1)


if __name__ == '__main__':
    unittest.main()
