"""The native getter and event guards must be patched once with correct stack budgets."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.vehicle_markers_patch import helper_fonts, inject_helper, make_tag, patch_manager, patch_marker, swf_parts, tag_payload


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


class EmbeddedFontPatchTests(unittest.TestCase):
    def tags(self, definitions):
        return [(kind, make_tag(kind, payload)) for kind, payload in definitions]

    def movie(self, definitions):
        # Minimal zero RECT, frame rate and frame count header.
        body = b'\x08\x00\x00\x1e\x01\x00' + b''.join(tag for _, tag in self.tags(definitions))
        return b'FWS\x0d' + struct.pack('<I', len(body) + 8) + body

    def test_font_ids_metadata_and_symbols_are_remapped_without_native_collisions(self):
        native = self.tags([(75, b'\x01\x00native font'), (76, b'\x01\x00\x02\x00NativeClass\x00')])
        helper = self.tags([(75, b'\x01\x00font'), (73, b'\x01\x00zones'),
                            (88, b'\x01\x00name'),
                            (76, b'\x02\x00\x00\x00HelperRoot\x00\x01\x00FontFace\x00')])
        original = list(native)
        result = helper_fonts(native, helper)
        self.assertEqual(native, original)
        identifiers = [struct.unpack('<H', tag_payload(tag)[:2])[0] for tag in result[:3]]
        self.assertEqual(identifiers, [3, 3, 3])
        self.assertEqual(tag_payload(result[3]), b'\x01\x00\x03\x00FontFace\x00')

    def test_injected_fonts_precede_both_abcs_and_native_tags_are_preserved(self):
        native = self.movie([(75, b'\x01\x00native'), (82, b'\x00' * 4 + b'frame1\x00native abc'), (0, b'')])
        helper = self.movie([(75, b'\x01\x00font'), (76, b'\x01\x00\x01\x00FontFace\x00'),
                             (82, b'\x00' * 4 + b'frame1\x00helper abc'), (0, b'')])
        _, result = swf_parts(inject_helper(native, helper))
        self.assertEqual([kind for kind, _ in result], [75, 75, 82, 82, 76, 0])
        self.assertEqual(tag_payload(result[0][1]), b'\x01\x00native')
        self.assertEqual(tag_payload(result[1][1]), b'\x02\x00font')
        self.assertIn(b'driftkings_vehicle_markers\x00', tag_payload(result[3][1]))

    def test_unknown_assets_and_unbound_font_metadata_are_rejected(self):
        for helper in ([(2, b'\x01\x00shape')], [(88, b'\x01\x00name')],
                       [(75, b'\x01\x00font'), (75, b'\x01\x00duplicate')],
                       [(76, b'\x01\x00\x01\x00MissingFont\x00')]):
            with self.assertRaises(ValueError):
                helper_fonts([], self.tags(helper))
