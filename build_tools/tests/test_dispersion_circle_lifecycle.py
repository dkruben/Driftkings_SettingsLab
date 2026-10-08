import ast
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock

from settings_support import settings_globals

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings._constants import DISPERSION_CIRCLE, MINIMAP_PLUGINS
from Driftkings.settings.service import SettingsService
from Driftkings.settings.settings_data import SettingsData, defaults


class Event:
    def __init__(self): self.listeners = []
    def __iadd__(self, callback): self.listeners.append(callback); return self
    def __isub__(self, callback): self.listeners.remove(callback); return self
    def emit(self):
        for callback in tuple(self.listeners): callback()


class Tracked:
    def __init__(self, **values):
        self.__dict__.update(values)
        self.__dict__['writes'] = []

    def __setattr__(self, name, value):
        self.writes.append(name)
        self.__dict__[name] = value


class ReticleLifecycleTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'source/scripts/client/Driftkings/battle/dispersion_circle.py'
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ReticleState']
        self.config = NS(ID=DISPERSION_CIRCLE.ID, data=defaults(DISPERSION_CIRCLE.ID))
        self.config.data['showClientAndServerReticleBeta'] = True
        self.native = {'client': 'native'}
        self.factory = Tracked(_GUN_MARKER_LINKAGES=self.native)
        self.aih = Tracked(GUN_MARKER_MIN_SIZE=5)
        self.cache = NS(isSynced=Mock(return_value=False), onSyncCompleted=Event())
        self.service = SettingsService(SettingsData())
        self.enable = Mock()
        self.ns = dict(aih_constants=self.aih, gm_factory=self.factory,
                       CUSTOM_GUN_MARKER_LINKAGES={'server': 'custom'},
                       dependency=NS(instance=lambda key: self.cache), ISettingsCache=object(),
                       enableServerAiming=self.enable)
        settings_globals(self.ns, 'battle.dispersion_circle')
        self.ns['settings_service'] = self.service
        exec(compile(tree, str(path), 'exec'), self.ns)
        self.state = self.ns['ReticleState'](self.config)
        self.addCleanup(self.state.stop)

    def apply(self, values):
        self.service.apply(self.config, values, persist=False)

    def test_construction_is_inert_and_start_stop_restore_exact_originals(self):
        self.assertEqual(self.aih.writes, [])
        self.assertEqual(self.factory.writes, [])
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        before = deepcopy(self.config.data)
        self.state.start(); self.state.start()
        self.assertEqual(self.aih.GUN_MARKER_MIN_SIZE, 0)
        self.assertEqual(self.state.reticleScaleFactor, 1.71)
        self.assertEqual(self.factory._GUN_MARKER_LINKAGES, {'client': 'native', 'server': 'custom'})
        self.assertEqual(self.native, {'client': 'native'})
        self.assertEqual(len(self.service.onModSettingsChanged._listeners), 1)
        self.state.stop(); self.state.stop()
        self.assertIs(self.factory._GUN_MARKER_LINKAGES, self.native)
        self.assertEqual(self.aih.GUN_MARKER_MIN_SIZE, 5)
        self.assertEqual(self.state.reticleScaleFactor, 1)
        self.assertFalse(self.state.showClientAndServerReticle)
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        self.assertEqual(self.config.data, before)

    def test_restart_captures_current_baseline_and_current_preferences(self):
        self.state.start(); self.state.stop()
        replacement = {'other': 'marker'}
        self.factory._GUN_MARKER_LINKAGES = replacement
        self.aih.GUN_MARKER_MIN_SIZE = 9
        self.apply({'percentCorrection': 50})
        self.state.start()
        self.assertEqual(self.state.reticleScaleFactor, 1.355)
        self.assertIn('other', self.factory._GUN_MARKER_LINKAGES)
        self.state.stop()
        self.assertIs(self.factory._GUN_MARKER_LINKAGES, replacement)
        self.assertEqual(self.aih.GUN_MARKER_MIN_SIZE, 9)

    def test_visual_changes_do_not_rewrite_marker_registry_or_minimum_size(self):
        self.state.start()
        self.aih.writes[:] = []
        self.factory.writes[:] = []
        settings_ref = self.state.customServerReticleSettings
        self.apply({'serverReticleGunMarkerOpacity': 25})
        self.assertIs(self.state.customServerReticleSettings, settings_ref)
        self.assertEqual(settings_ref['gunTag'], 25)
        self.assertEqual(settings_ref['mixing'], 50)
        self.apply({'percentCorrection': 50})
        self.assertEqual(self.state.reticleScaleFactor, 1.355)
        self.service.onModSettingsChanged.emit(MINIMAP_PLUGINS.NAME, {'enabled': False})
        self.service.onModSettingsChanged.emit(DISPERSION_CIRCLE.NAME, {'unrelated': True})
        self.assertEqual(self.aih.writes, [])
        self.assertEqual(self.factory.writes, [])
        self.apply({'gunMarkerMinimumSize': 4})
        self.assertEqual(self.aih.writes, ['GUN_MARKER_MIN_SIZE'])
        self.assertEqual(self.factory.writes, [])

    def test_disabling_cancels_pending_aim_and_restores_native_values(self):
        self.state.start()
        self.state.ensureServerAiming(); self.state.ensureServerAiming()
        self.assertEqual(len(self.cache.onSyncCompleted.listeners), 1)
        stale = self.cache.onSyncCompleted.listeners[0]
        self.apply({'enabled': False})
        self.assertFalse(self.cache.onSyncCompleted.listeners)
        self.assertIs(self.factory._GUN_MARKER_LINKAGES, self.native)
        self.assertEqual(self.aih.GUN_MARKER_MIN_SIZE, 5)
        stale()
        self.enable.assert_not_called()
        self.apply({'enabled': True})
        self.assertTrue(self.state.showClientAndServerReticle)

    def test_sync_runs_once_and_stop_disconnects_from_original_cache(self):
        self.state.start()
        self.state.ensureServerAiming()
        self.cache.onSyncCompleted.emit()
        self.enable.assert_called_once_with()
        self.assertFalse(self.cache.onSyncCompleted.listeners)
        self.state.ensureServerAiming()
        original_cache = self.cache
        stale = original_cache.onSyncCompleted.listeners[0]
        self.cache = NS(isSynced=Mock(return_value=False), onSyncCompleted=Event())
        self.state.stop()
        self.assertFalse(original_cache.onSyncCompleted.listeners)
        stale()
        self.state.ensureServerAiming()
        self.enable.assert_called_once()
        self.assertFalse(self.cache.onSyncCompleted.listeners)

    def test_ready_cache_activates_immediately_and_dual_reticle_toggle_cancels_wait(self):
        self.state.start()
        self.cache.isSynced.return_value = True
        self.state.ensureServerAiming()
        self.enable.assert_called_once()
        self.assertFalse(self.cache.onSyncCompleted.listeners)
        self.cache.isSynced.return_value = False
        self.state.ensureServerAiming()
        self.apply({'showClientAndServerReticleBeta': False})
        self.assertFalse(self.cache.onSyncCompleted.listeners)
        self.state.ensureServerAiming()
        self.enable.assert_called_once()

    def test_failed_start_restores_native_values_and_can_retry(self):
        self.config.data['percentCorrection'] = None
        with self.assertRaises(TypeError): self.state.start()
        self.assertFalse(self.state.active)
        self.assertEqual(self.aih.GUN_MARKER_MIN_SIZE, 5)
        self.assertIs(self.factory._GUN_MARKER_LINKAGES, self.native)
        self.assertFalse(self.service.onModSettingsChanged._listeners)
        self.config.data['percentCorrection'] = 50
        self.state.start()
        self.assertEqual(self.state.reticleScaleFactor, 1.355)


if __name__ == '__main__':
    unittest.main()
