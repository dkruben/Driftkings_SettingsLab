import ast
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
import weakref

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'
sys.path.insert(0, str(CLIENT))
from Driftkings._constants import GLOBAL, MINIMAP_PLUGINS
from Driftkings.core import minimap as policy
from Driftkings.core.keyboard import KeyboardService
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults
from Driftkings.settings.store import merge


def load_class(path, name, namespace):
    tree = ast.parse((CLIENT / 'Driftkings' / path).read_text(encoding='utf-8-sig'))
    tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
    exec(compile(tree, path, 'exec'), namespace)
    return namespace[name]


class Event:
    def __init__(self):
        self.listeners = []
        self.values = []

    def __iadd__(self, callback):
        self.listeners.append(callback)
        return self

    def __isub__(self, callback):
        self.listeners.remove(callback)
        return self

    def __call__(self, value):
        self.values.append(value)
        for listener in list(self.listeners):
            listener(value)


class MinimapControllerTests(unittest.TestCase):
    def setUp(self):
        self.config = NS(ID=MINIMAP_PLUGINS.ID, data=defaults(MINIMAP_PLUGINS.ID))
        self.service = SettingsService(SettingsData())
        self.keyboard = KeyboardService(blocked=lambda:False)
        self.alt = Event()
        self.keys = Mock(return_value=True)
        self.personal, self.vehicles = Mock(), Mock()
        self.component = NS(config=self.config, VIEWS=weakref.WeakSet(),
                            PERSONAL=[self.personal], VEHICLES=[self.vehicles])
        provider = NS(arenaVisitor=NS(gui=NS(isInEpicRange=lambda:False),
                                     type=NS(getBoundingBox=lambda:((0, 0), (1000, 800)))),
                      getArenaDP=lambda:NS(getVehicleInfo=lambda:NS(vehicleType=NS(classTag='SPG'))))
        self.ns = dict(settings_service=self.service, GLOBAL=GLOBAL, MINIMAP_PLUGINS=MINIMAP_PLUGINS,
                       keyboard=self.keyboard, g_events=NS(onAltKey=self.alt), checkKeys=self.keys,
                       dependency=NS(descriptor=lambda _:provider), IBattleSessionProvider=object,
                       PERSONAL=self.component.PERSONAL, VEHICLES=self.component.VEHICLES,
                       VIEWS=self.component.VIEWS)
        cls = load_class('battle/minimap.py', 'MinimapController', self.ns)
        self.controller = self.component.controller = cls(self.config)
        self.addCleanup(self.controller.dispose)

    def test_hotkey_lifecycle_keeps_settings_unchanged_and_resets_between_battles(self):
        before = deepcopy(self.config.data)
        self.controller.onHotkeyPressed(None)
        self.assertEqual(self.alt.values, [])
        self.controller.activate(); self.controller.activate()
        self.assertEqual(self.keyboard.callbacks, [self.controller.onHotkeyPressed])
        self.controller.onHotkeyPressed(None); self.controller.onHotkeyPressed(None)
        self.assertEqual(self.alt.values, [True])
        self.vehicles.refreshLabels.assert_called_once()
        self.assertEqual(self.config.data, before)
        self.assertFalse(hasattr(self.config, 'minimapZoom'))
        self.controller.deactivate(); self.controller.deactivate()
        self.assertFalse(self.controller.minimapZoom)
        self.assertEqual(self.keyboard.callbacks, [])
        self.controller.onHotkeyPressed(None)
        self.assertEqual(self.alt.values, [True])
        self.controller.activate(); self.controller.onHotkeyPressed(None)
        self.assertEqual(self.alt.values, [True, True])

    def test_settings_event_is_scoped_live_and_disconnected_on_disposal(self):
        self.controller.activate(); self.controller.setAlternative(True)
        self.personal.reset_mock(); self.vehicles.reset_mock()
        self.service.onModSettingsChanged.emit('own_health', {'enabled':False})
        self.assertTrue(self.controller.minimapZoom)
        self.personal.refreshPresentation.assert_not_called()
        self.vehicles.refreshLabels.assert_not_called()
        self.service.apply(self.config, {'presentation':{'alternativeEnabled':False}}, persist=False)
        self.assertFalse(self.controller.minimapZoom)
        self.assertEqual(self.alt.values, [True, False])
        self.personal.refreshPresentation.assert_not_called()
        calls = self.vehicles.refreshLabels.call_count
        self.service.apply(self.config, {'presentation':{'alternativeEnabled':False}}, persist=False)
        self.assertEqual(self.vehicles.refreshLabels.call_count, calls)
        self.controller.onHotkeyPressed(None)
        self.assertFalse(self.controller.minimapZoom)
        self.controller.dispose()
        self.service.apply(self.config, {'enabled':False}, persist=False)
        self.personal.refreshPresentation.assert_not_called()
        self.assertEqual(self.vehicles.refreshLabels.call_count, calls)

    def view_class(self):
        class Meta:
            def __init__(self, alias): self.payloads = []
            def _populate(self): pass
            def _dispose(self): pass
            def as_minimapPresentationS(self, payload): self.payloads.append(payload)

        self.cancelled = []
        self.scheduled = []
        def schedule(delay, function):
            self.scheduled.append((delay, function))
            return len(self.scheduled)
        self.component.PERSONAL[:] = []
        self.component.VEHICLES[:] = []
        ns = dict(MinimapMeta=Meta, _component=lambda:self.component, g_events=NS(onAltKey=self.alt),
                  settings_service=self.service, GLOBAL=GLOBAL, MINIMAP_PLUGINS=MINIMAP_PLUGINS,
                  callback=schedule, cancelCallback=self.cancelled.append, checkKeys=self.keys,
                  xvmInstalled=False)
        return load_class('views/battle/minimap.py', 'MinimapCentredView', ns)

    def test_view_recreation_preserves_alternative_until_last_view_is_closed(self):
        view_type = self.view_class()
        first = view_type(); first._populate()
        self.controller.onHotkeyPressed(None)
        self.assertTrue(first.payloads[-1]['alternative'])
        second = view_type(); second._populate()
        self.assertTrue(second.payloads[-1]['alternative'])
        self.assertEqual(second.payloads[-1]['mapWidth'], 1000)
        self.assertEqual(second.payloads[-1]['mapHeight'], 800)
        self.assertEqual(second.payloads[-1]['vehicleClass'], 'SPG')
        first._dispose()
        self.assertTrue(self.controller._active)
        self.assertTrue(self.controller.minimapZoom)
        second._dispose()
        self.assertFalse(self.controller._active)
        self.assertFalse(self.controller.minimapZoom)
        self.assertEqual(self.keyboard.callbacks, [])
        self.assertEqual(self.alt.listeners, [])
        self.assertEqual(len(self.cancelled), 2)
        third = view_type(); third._populate()
        self.assertFalse(third.payloads[-1]['alternative'])
        third._dispose()

    def test_release_poll_restores_map_when_settings_panel_blocks_keyboard(self):
        view = self.view_class()(); view._populate()
        self.controller.onHotkeyPressed(None)
        registry = NS(registry=NS(isOpen=True))
        with patch.dict(sys.modules, {'Driftkings.settings.registry':registry}):
            view._checkRelease()
        self.assertFalse(self.controller.minimapZoom)
        self.assertFalse(view.payloads[-1]['alternative'])
        self.assertIsNone(view._releaseCallback)
        # Epic maps keep native positioning but still receive alternative labels.
        self.controller.sessionProvider.arenaVisitor.gui.isInEpicRange = lambda:True
        view.onAltKey(True)
        self.assertFalse(view.payloads[-1]['zoom'])
        self.assertTrue(view.payloads[-1]['alternative'])
        view._dispose()

    def test_settings_owner_validates_before_saving_and_preserves_legacy_migration(self):
        saves = []
        class Storage:
            def readData(self, quiet=True): pass
            def onApplySettings(self, values):
                saves.append(deepcopy(values))
                self.data = merge(self.data, values)
        ns = dict(ComponentSettings=Storage, MINIMAP_PLUGINS=MINIMAP_PLUGINS,
                  GLOBAL=GLOBAL, json=json, merge=merge, policy=policy)
        cls = load_class('settings/templates/battle/minimap.py', 'MinimapPluginsSettings', ns)
        owner = cls(); owner.ID = MINIMAP_PLUGINS.ID; owner.data = deepcopy(self.config.data)
        owner.data['minimapSchema'] = 0
        owner.data['artilleryAim']['color'] = 'FFFFFF'
        owner.readData()
        self.assertNotIn('color', owner.data['artilleryAim'])
        self.assertTrue(owner.data['minimapSchema'])
        self.assertTrue(all(c['alpha'] == owner.data['alpha'] for c in owner.data['circles'].values()))
        before = deepcopy(owner.data)
        for invalid in ({'extraCircles':'not json'}, {'zoomFactor':999}, {'health':{'visibility':'invalid'}}):
            with self.assertRaises(ValueError):
                self.service.apply(owner, invalid)
            self.assertEqual(owner.data, before)
        self.assertEqual(saves, [])
        circle = dict(radius=100, color='FFFFFF', alpha=70, thickness=1, dash=0, gap=5, vehicleClass='SPG')
        self.service.apply(owner, {'extraCircles':json.dumps([circle])})
        self.assertEqual(owner.data['extraCircles'], [circle])
        self.assertEqual(saves, [{'extraCircles':[circle]}])


if __name__ == '__main__':
    unittest.main()
