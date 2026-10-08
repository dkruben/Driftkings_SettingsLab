import gc
import sys
import unittest
import weakref
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/scripts/client'))
from Driftkings.views.hangar.common import HangarController, install_card
from Driftkings.core import hooks as hook_module


class HangarCardTests(unittest.TestCase):
    def test_controllers_refresh_only_their_views_and_release_parents(self):
        class Parent(object):
            pass
        parent = Parent()
        first, second = HangarController(), HangarController()
        first.views[parent] = Mock()
        second.views[parent] = Mock()
        first.setVisible(parent, True)
        first.views[parent].refresh.assert_called_once_with()
        second.views[parent].refresh.assert_not_called()
        first.onApplySettings()
        self.assertEqual(first.views[parent].refresh.call_count, 2)
        ref = weakref.ref(parent)
        del parent
        gc.collect()
        self.assertIsNone(ref())
        self.assertFalse(first.views)
        self.assertFalse(first.visible)

    def test_cards_keep_separate_hook_owners_and_native_lifecycle(self):
        calls = []

        class Hangar(object):
            def _getChildComponents(self):
                return {1: 'native'}

            def _onShown(self):
                calls.append('shown')
                return 42

            def _onHidden(self):
                calls.append('hidden')
                return 43

        def install(target, name, getter):
            original = getattr(target, name)
            setattr(target, name, lambda *a, **kw: getter(original, *a, **kw))

        registry = hook_module.HookRegistry()
        resolver = Mock(side_effect=lambda name: {'a': 10, 'b': 20}.get(name, -1))
        stubs = {
            'gui.impl.gen_utils': SimpleNamespace(INVALID_RES_ID=-1),
            'gui.impl.lobby.hangar.random.random_hangar': SimpleNamespace(RandomHangar=Hangar),
            'Driftkings.ui.gameface': SimpleNamespace(resource_id=resolver),
            'Driftkings.common.utils.monkeypatch': SimpleNamespace(override=install),
        }
        a = SimpleNamespace(RESOURCE='a', LOG=Mock(), g_controller=Mock())
        b = SimpleNamespace(RESOURCE='b', LOG=Mock(), g_controller=Mock())
        view_a, view_b = Mock(), Mock()
        with patch.dict(sys.modules, stubs), patch.object(hook_module, 'hooks', registry):
            install_card(lambda: a, view_a, 'card.a')
            install_card(lambda: b, view_b, 'card.b')
            registry.activate('card.a')
            registry.activate('card.b')
            parent = Hangar()
            children = parent._getChildComponents()
            self.assertEqual(set(children), {1, 10, 20})
            children[10]()
            view_a.assert_called_once_with(parent, 10)
            children[20]()
            view_b.assert_called_once_with(parent, 20)
            self.assertEqual(parent._onShown(), 42)
            a.g_controller.setVisible.assert_called_with(parent, True)
            self.assertEqual(parent._onHidden(), 43)
            b.g_controller.setVisible.assert_called_with(parent, False)
            self.assertEqual(calls, ['shown', 'hidden'])
            registry.deactivate('card.a')
            self.assertEqual(set(parent._getChildComponents()), {1, 20})
            b.RESOURCE = 'missing'
            self.assertEqual(parent._getChildComponents(), {1: 'native'})
            b.LOG.warning.assert_called_once()
            resolver.side_effect = RuntimeError('resources unavailable')
            self.assertEqual(parent._getChildComponents(), {1: 'native'})
            b.LOG.exception.assert_called_once()
