"""Exercise the results child lifecycle without loading the WoT client."""
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/scripts/client'))
from Driftkings.views.hangar import battle_efficiency as integration


class Model:
    def __init__(self, **kwargs):
        self.values = []
        self._initialize()

    def _initialize(self): pass
    def _addStringProperty(self, key, value): self.values.append(value)
    def _setString(self, index, value): self.values[index] = value
    def transaction(self): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass


class Component:
    def __init__(self, layoutID, model): self.model = model()
    def getViewModel(self): return self.model
    def _onLoading(self, *args, **kwargs): pass
    def _finalize(self): pass


class Parent:
    arenaUniqueID = 42


class ResultsGamefaceTests(unittest.TestCase):
    def setUp(self):
        self.hooks = {}
        def override(cls, name):
            def register(handler):
                self.hooks[name] = handler
                return handler
            return register
        self.service = Mock()
        self.service.getStatsCtrl.return_value.getResults.return_value = object()
        self.component = NS(config=NS(data={'enabled': True, 'battleResultsWindow': True}),
                            _results_views={}, LOG=Mock(),
                            make_results_payload=Mock(return_value={'enabled': True, 'html': 'WN8: 1234'}))
        modules = {
            'frameworks.wulf': NS(ViewModel=Model),
            'gui.impl.pub.view_component': NS(ViewComponent=Component),
            'gui.impl.gen_utils': NS(INVALID_RES_ID=-1),
            'gui.impl.lobby.battle_results.random_battle_results_view': NS(RandomBattleResultsView=Parent),
            'helpers': NS(dependency=NS(instance=lambda kind: self.service)),
            'skeletons.gui.battle_results': NS(IBattleResultsService=object),
            'Driftkings.ui.gameface': NS(attach_assets=lambda *a, **kw: None, resource_id=lambda key: 123),
        }
        self.patchers = [patch.dict(sys.modules, modules),
                         patch.object(integration, 'override', override),
                         patch.object(integration, '_component', lambda: self.component)]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        integration.install_results_gameface()
        self.parent = Parent()

    def child(self):
        native = {77: object}
        factories = self.hooks['_getChildComponents'](lambda view: native, self.parent)
        self.assertEqual(native, {77: object})
        self.assertIs(factories[77], object)
        return factories[123]()

    def test_child_publishes_after_own_loading_and_disposes(self):
        child = self.child()
        child.refresh(42)
        self.service.getStatsCtrl.assert_not_called()
        child._onLoading()
        self.service.getStatsCtrl.assert_called_once_with(42)
        self.assertEqual(json.loads(child.model.values[0]), {'enabled': True, 'html': 'WN8: 1234'})
        self.assertIs(self.component._results_views[self.parent], child)
        child._finalize()
        self.assertFalse(self.component._results_views)
        self.service.reset_mock()
        child.refresh(42)
        self.service.getStatsCtrl.assert_not_called()

    def test_settings_toggle_and_reopen_do_not_keep_old_view(self):
        first = self.child()
        first._onLoading()
        self.component.config.data['battleResultsWindow'] = False
        first.refresh(42)
        self.assertEqual(json.loads(first.model.values[0]), {'enabled': False})
        self.component.config.data['battleResultsWindow'] = True
        replacement = self.child()
        first._finalize()
        self.assertIs(self.component._results_views[self.parent], replacement)
        replacement._onLoading()
        self.assertTrue(json.loads(replacement.model.values[0])['enabled'])

    def test_missing_results_and_calculation_errors_preserve_native_screen(self):
        child = self.child()
        self.service.getStatsCtrl.return_value.getResults.return_value = None
        child._onLoading()
        self.component.LOG.warning.assert_called_once()
        self.assertEqual(json.loads(child.model.values[0]), {'enabled': False})
        self.service.getStatsCtrl.side_effect = RuntimeError('unavailable')
        child.refresh(42)
        self.component.LOG.exception.assert_called_once()
