"""Per-build native marker movie locks and the native contract gate; no game files or compilers are used."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.vehicle_markers_patch import (PROTECTED, marker_lock_for_build, patch_marker, verify_manager_contract,
                                               verify_marker_contract, verify_native_movie)

CONFIG = json.loads((ROOT / 'build_data/build_config.json').read_text(encoding='utf-8'))
SPEC = next(spec for spec in CONFIG['generators'].values() if spec.get('kind') == 'vehicle_markers')
LOCKS = {build: json.loads((ROOT / path).read_text(encoding='utf-8')) for build, path in SPEC['locks'].items()}
PINNED = {'995': '34d92354f1c755313b99fd4e268bb78dc130ece24797a271aece5f0a7346537e',
          '996': '52c5906b04998132efb7a70422999b5dd225d89fb29c49c89d41ba8a59f090b6'}


def method(name, parameters=(), namespace='PackageNamespace("")', result='void'):
    lines = ['  trait method QName(%s, "%s")' % (namespace, name), '   method']
    lines += ['    param QName(PackageNamespace(""), "%s")' % kind for kind in parameters]
    lines += ['    returns QName(PackageNamespace(""), "%s")' % result, '    body', '     maxstack 1', '     code',
              '      getlocal0', '      pushscope', '      returnvoid', '     end ; code', '    end ; body',
              '   end ; method', '  end ; trait']
    return '\n'.join(lines) + '\n'


def marker(update_health=('int', 'uint', 'String', 'int'), model='VehicleMarkerVO', skip=()):
    members = [('draw', ()), ('setHealth', ('int',)), ('updateHealth', update_health), ('updateMarkerSettings', ()),
               ('updateState', ('String', 'Boolean')), ('updateCriticalLayout', ()),
               ('showHitLabelAnim', ('int', 'String', 'uint')), ('onBeforeDispose', ())]
    text = ''.join(method(name, parameters) for name, parameters in members if name not in skip)
    text += ('  trait getter QName(PackageNamespace(""), "markerSettings")\n   method\n'
             '    returns QName(PackageNamespace(""), "Object")\n    body\n     maxstack 1\n     code\n'
             '      getlocal0\n      pushscope\n      returnvalue\n     end ; code\n    end ; body\n'
             '   end ; method\n  end ; trait\n')
    for name, kind in (('model', model), ('vehicleDestroyed', 'Boolean'), ('isStickyAndOutOfScreen', 'Boolean')):
        text += '  trait slot QName(%s, "%s") type QName(PackageNamespace("x"), "%s") end\n' % (PROTECTED, name, kind)
    return text


class MarkerLockTests(unittest.TestCase):
    def test_each_build_has_its_own_exact_lock(self):
        self.assertEqual(set(LOCKS), set(CONFIG['reference']['ct_builds']))
        for build, digest in PINNED.items():
            lock = marker_lock_for_build(LOCKS, build)
            self.assertEqual(lock['sha256'], digest)
            self.assertEqual(lock['resource'], 'gui/flash/battleVehicleMarkersApp.swf')
        self.assertNotIn('clientBuild', LOCKS['995'])
        self.assertEqual((LOCKS['996']['clientBuild'], LOCKS['996']['clientRevision']),
                         ('996', CONFIG['reference']['ct_builds']['996']))

    def test_historical_995_lock_file_is_untouched(self):
        self.assertEqual(json.loads((ROOT / SPEC['locks']['995']).read_text(encoding='utf-8')),
                         dict(gameVersion='2.4.2.0', package='gui-part2.pkg',
                              resource='gui/flash/battleVehicleMarkersApp.swf', sha256=PINNED['995']))

    def test_unknown_build_and_foreign_locks_are_refused(self):
        with self.assertRaises(ValueError):
            marker_lock_for_build(LOCKS, '997')
        with self.assertRaises(ValueError):
            marker_lock_for_build({'996': LOCKS['995']}, '996')
        with self.assertRaises(ValueError):
            marker_lock_for_build({'995': LOCKS['996']}, '995')

    def test_unknown_or_other_build_movie_is_refused(self):
        movie = b'FWS not the pinned movie'
        for build in PINNED:
            with self.assertRaises(ValueError):
                verify_native_movie(movie, LOCKS[build])
        accepted = dict(LOCKS['996'], sha256=hashlib.sha256(movie).hexdigest())
        self.assertEqual(verify_native_movie(movie, accepted), movie)
        # A movie that satisfies one build's pin never satisfies the other build's lock.
        with self.assertRaises(ValueError):
            verify_native_movie(movie, LOCKS['995'])


class NativeContractTests(unittest.TestCase):
    def test_compatible_native_classes_pass_and_patch_completely(self):
        verify_marker_contract(marker())
        verify_manager_contract(method('as_setMarkerSettings', ('Object',)) + method('as_setColorBlind', ('Boolean',)))
        patched = patch_marker(marker())
        self.assertEqual(patched.count('"restoreIcons"), 1'), 6)
        self.assertEqual(patched.count('"nativeSettings"), 3'), 1)

    def test_missing_or_duplicated_native_member_is_refused(self):
        for text in (marker(skip=('updateHealth',)), marker() + method('draw'),
                     marker().replace('"vehicleDestroyed"', '"vehicleGone"')):
            with self.assertRaises(ValueError):
                verify_marker_contract(text)
        with self.assertRaises(ValueError):
            patch_marker(marker(skip=('onBeforeDispose',)))
        with self.assertRaises(ValueError):
            verify_manager_contract(method('as_setMarkerSettings', ('Object',)))

    def test_incompatible_signature_is_refused(self):
        for text in (marker(update_health=('int', 'String', 'uint')), marker(update_health=('int',)),
                     marker(model='Object'), marker().replace('"Object")\n    body', '"String")\n    body')):
            with self.assertRaises(ValueError):
                verify_marker_contract(text)
        with self.assertRaises(ValueError):
            verify_manager_contract(method('as_setMarkerSettings', ('String',))
                                    + method('as_setColorBlind', ('Boolean',)))
        with self.assertRaises(ValueError):
            verify_manager_contract(method('as_setMarkerSettings', ('Object',))
                                    + method('as_setColorBlind', ('Boolean',), result='Boolean'))


if __name__ == '__main__':
    unittest.main()
