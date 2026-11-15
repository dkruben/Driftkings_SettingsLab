"""Short run-owned marker workspace for deep repositories; fixtures only, no game tools."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.isolated_output import IsolatedOutput
from build_tools.vehicle_markers import (DISASSEMBLY_BUDGET, PATH_MARGIN, marker_workspace, short_workspace_root,
                                         too_deep)

DEEPEST = 'markers-0/net/wg/gui/battle/views/vehicleMarkers/statusMarkers/VehicleAnimatedStatusBaseMarker.script.asasm'


class ShortMarkerWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.deep = self.base / ('r' * 90)
        self.deep.mkdir()
        self.short = self.base / 's'

    def test_budget_and_limit_are_unchanged(self):
        self.assertEqual((DISASSEMBLY_BUDGET, PATH_MARGIN), (120, 8))
        fits = 'C:\\' + 'a' * (260 - 129 - 3 - 1)
        self.assertEqual(len(fits) + 129, 259)
        self.assertFalse(too_deep(fits))
        self.assertTrue(too_deep(fits + 'a'))

    def test_default_short_root_is_on_the_repository_drive_and_overridable(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DK_MARKER_WORKSPACE', None)
            self.assertEqual(short_workspace_root(ROOT), Path(ROOT.anchor) / 'DK_TMP')
            os.environ['DK_MARKER_WORKSPACE'] = str(self.short)
            self.assertEqual(short_workspace_root(ROOT), self.short)

    def test_deep_run_uses_owned_short_workspace_and_removes_only_it(self):
        self.short.mkdir()
        other = self.short / 'vm_other-run'
        other.mkdir()
        (other / 'sentinel').write_bytes(b'other')
        with IsolatedOutput(self.deep, 'run-a') as scope:
            destination = scope.path / 'workspace/generated/build/flash/output.fixture'
            with marker_workspace(destination, self.short) as work:
                self.assertEqual(work, self.short / 'vm_run-a')
                self.assertFalse(work.is_relative_to(scope.path))
                path = work / DEEPEST
                path.parent.mkdir(parents=True)
                path.write_bytes(b'fixture')
                self.assertLess(len(str(path)), 260 - PATH_MARGIN)
                self.assertEqual((scope.path / 'workspace/marker_workspace.txt').read_text(encoding='utf-8'), str(work))
                # The final output still belongs to the isolated run folder.
                destination.parent.mkdir(parents=True)
                destination.write_bytes(b'output')
                with self.assertRaises(ValueError):
                    (self.short / 'stray.fixture').write_bytes(b'outside both owned trees')
                with self.assertRaises(ValueError):
                    (other / 'sentinel').write_bytes(b'tampered')
            self.assertFalse(work.exists())
            self.assertIsNone(scope.external)
            self.assertEqual(destination.read_bytes(), b'output')
            with self.assertRaises(ValueError):
                (work / 'late.fixture').parent.mkdir()
        self.assertEqual((other / 'sentinel').read_bytes(), b'other')
        self.assertEqual(sorted(p.name for p in self.short.iterdir()), ['vm_other-run'])

    def test_shallow_run_keeps_the_in_run_workspace(self):
        with IsolatedOutput(self.base, 'run-a') as scope:
            with marker_workspace(scope.path / 'workspace/out', self.short) as work:
                self.assertEqual(work.parent, scope.path / 'workspace/tmp')
            self.assertFalse(self.short.exists())

    def test_deep_run_without_short_root_or_with_deep_short_root_is_rejected(self):
        with IsolatedOutput(self.deep, 'run-a') as scope:
            destination = scope.path / 'workspace/out'
            with self.assertRaisesRegex(ValueError, 'too deep'):
                with marker_workspace(destination):
                    pass
            long_root = self.base / ('s' * 120)
            with self.assertRaisesRegex(ValueError, 'too deep'):
                with marker_workspace(destination, long_root):
                    pass
            self.assertFalse(long_root.exists())
            self.assertIsNone(scope.external)

    def test_runs_do_not_collide_and_an_existing_directory_is_never_reused(self):
        seen = []
        for run in ('run-a', 'run-b'):
            with IsolatedOutput(self.deep, run) as scope:
                with marker_workspace(scope.path / 'workspace/out', self.short) as work:
                    seen.append(work)
        self.assertEqual([p.name for p in seen], ['vm_run-a', 'vm_run-b'])
        stale = self.short / 'vm_run-c'
        stale.mkdir()
        (stale / 'old.fixture').write_bytes(b'old')
        with IsolatedOutput(self.deep, 'run-c') as scope:
            with self.assertRaises(FileExistsError):
                with marker_workspace(scope.path / 'workspace/out', self.short):
                    pass
            self.assertIsNone(scope.external)
        self.assertEqual((stale / 'old.fixture').read_bytes(), b'old')

    def test_creation_failure_is_reported_and_nothing_is_owned(self):
        blocker = self.base / 'file-not-folder'
        blocker.write_bytes(b'x')
        with IsolatedOutput(self.deep, 'run-a') as scope:
            with self.assertRaises((ValueError, OSError)):
                with marker_workspace(scope.path / 'workspace/out', blocker):
                    pass
            self.assertIsNone(scope.external)
        self.assertEqual(blocker.read_bytes(), b'x')

    def test_protected_and_repository_locations_are_refused(self):
        game = self.base / 'game'
        game.mkdir()
        with IsolatedOutput(self.deep, 'run-a') as scope:
            destination = scope.path / 'workspace/out'
            inner = self.short / 'vm_run-a' / 'inner'
            for short_root, protected in ((game / 'tmp', (game,)), (self.short, (inner,))):
                with self.assertRaisesRegex(ValueError, 'protected'):
                    with marker_workspace(destination, short_root, protected):
                        pass
            with self.assertRaisesRegex(ValueError, 'protected'):
                scope.adopt(scope.root / 'vm_run-a')  # never inside the repository itself
            self.assertFalse((scope.root / 'vm_run-a').exists())
            self.assertIsNone(scope.external)
        self.assertEqual(list(game.iterdir()), [])

    def test_body_failure_cleans_the_owned_workspace_and_propagates(self):
        with IsolatedOutput(self.deep, 'run-a') as scope:
            with self.assertRaisesRegex(RuntimeError, 'body'):
                with marker_workspace(scope.path / 'workspace/out', self.short) as work:
                    (work / 'file.fixture').write_bytes(b'own')
                    raise RuntimeError('body')
            self.assertFalse(work.exists())
            self.assertIsNone(scope.external)

    def test_foreign_release_and_second_adoption_are_refused(self):
        with IsolatedOutput(self.deep, 'run-a') as scope:
            with marker_workspace(scope.path / 'workspace/out', self.short) as work:
                with self.assertRaises(ValueError):
                    scope.adopt(self.short / 'vm_run-a-second')
                with self.assertRaises(ValueError):
                    scope.release(self.short)
                self.assertTrue(work.is_dir())
            with self.assertRaises(ValueError):
                scope.adopt(self.short / 'unrelated-name')

    @unittest.skipUnless(os.name == 'nt', 'Windows junction')
    def test_junction_short_root_is_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'sentinel').write_bytes(b'old')
        result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(self.short), str(outside)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        try:
            with IsolatedOutput(self.deep, 'run-a') as scope:
                with self.assertRaises(ValueError):
                    with marker_workspace(scope.path / 'workspace/out', self.short):
                        pass
                self.assertIsNone(scope.external)
        finally:
            os.rmdir(self.short)
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ['sentinel'])


if __name__ == '__main__':
    unittest.main()
