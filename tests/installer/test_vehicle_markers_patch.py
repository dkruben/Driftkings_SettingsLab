"""The native getter and event guards must be patched once with correct stack budgets."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.vehicle_markers_patch import patch_manager, patch_marker


def trait(kind, name, result='returnvoid'):
    return ('  trait %s QName(PackageNamespace(""), "%s")\n'
            '    method\n      body\n        maxstack 1\n'
            '      getlocal0\n      pushscope\n'
            '      pushstring "native"\n      pop\n'
            '      %s\n      end\n    end\n  end ; trait\n') % (kind, name, result)


class VehicleMarkerPatchTests(unittest.TestCase):
    def movie(self):
        methods = ('draw', 'setHealth', 'updateHealth', 'updateMarkerSettings', 'updateState', 'updateCriticalLayout', 'showHitLabelAnim', 'onBeforeDispose')
        return ''.join(trait('method', name) for name in methods) + trait('getter', 'markerSettings', 'returnvalue')

    def test_getter_selects_per_marker_and_restore_precedes_native_updates(self):
        patched = patch_marker(self.movie())
        self.assertEqual(patched.count('"nativeSettings"), 3'), 1)
        self.assertEqual(patched.count('"restoreIcons"), 1'), 6)
        self.assertIn('"damageEnabled"), 2', patched)
        damage_capture = patched[patched.index('  trait method QName(PackageNamespace(""), "updateHealth")'):]
        damage_capture = damage_capture[:damage_capture.index('  end ; trait')]
        self.assertIn('"damage"), 5', damage_capture)
        self.assertIn('getlocal3', damage_capture)
        self.assertIn('maxstack 6', damage_capture)
        damage_guard = patched[patched.index('  trait method QName(PackageNamespace(""), "showHitLabelAnim")'):]
        damage_guard = damage_guard[:damage_guard.index('  end ; trait')]
        self.assertIn('"currHealth"', damage_guard)
        self.assertNotIn('"vehicleDestroyed"', damage_guard)
        getter = patched[patched.index('  trait getter'):]
        self.assertIn('maxstack 4', getter)
        self.assertLess(getter.index('"nativeSettings"'), getter.index('returnvalue'))
        draw = patched[:patched.index('  trait method QName(PackageNamespace(""), "setHealth")')]
        self.assertLess(draw.index('"restoreIcons"'), draw.index('pushstring "native"'))

    def test_missing_or_ambiguous_native_getter_is_rejected(self):
        getter = trait('getter', 'markerSettings', 'returnvalue')
        with self.assertRaises(ValueError):
            patch_marker(self.movie().replace(getter, ''))
        with self.assertRaises(ValueError):
            patch_marker(self.movie() + getter)

    def test_configuration_and_colorblind_state_are_set_before_native_events(self):
        result = patch_manager(trait('method', 'as_setMarkerSettings') + trait('method', 'as_setColorBlind'))
        configured, blind = result.split('  trait method QName(PackageNamespace(""), "as_setColorBlind")')
        self.assertLess(configured.index('"receiveStats"'), configured.index('"configure"'))
        self.assertIn('VM_RATINGS_NATIVE_SETTINGS', configured)
        self.assertLess(configured.index('"configure"'), configured.index('pushstring "native"'))
        self.assertLess(blind.index('"setColorBlind"'), blind.index('pushstring "native"'))
