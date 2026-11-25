# -*- coding: utf-8 -*-
"""Vehicle-marker workspace selection and cleanup (B2), without isolated output.

The workspace is either beside the output (when the path fits the Windows budget) or a unique directory under a
short root. Only directories created by the build are removed; a failure keeps its directory and reports it.
"""
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import vehicle_markers as vm  # noqa: E402

DEEP = Path('E:/' + 'deep-' * 40)  # far beyond the Windows budget, never created by these tests


class PlanTests(unittest.TestCase):
    def test_shallow_destination_keeps_the_workspace_beside_the_output(self):
        tmp = Path(tempfile.mkdtemp(prefix='plan-'))
        self.addCleanup(shutil.rmtree, str(tmp), True)
        self.assertEqual(vm.plan_marker_workspace(tmp, None), ('temporary', tmp))

    def test_deep_destination_uses_the_short_root(self):
        short = Path(tempfile.gettempdir()) / 'dk-short-root'
        self.assertEqual(vm.plan_marker_workspace(DEEP, short), ('short', short))

    def test_deep_destination_without_a_short_root_is_refused(self):
        with self.assertRaises(ValueError) as context:
            vm.plan_marker_workspace(DEEP, None)
        self.assertIn('DK_MARKER_WORKSPACE', str(context.exception))


class OwnedShortWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='short-root-'))
        self.addCleanup(shutil.rmtree, str(self.root), True)
        self.sibling = self.root / 'unrelated-build'
        self.sibling.mkdir()
        (self.sibling / 'keep.txt').write_text('keep', encoding='utf-8')

    def test_success_removes_only_the_directory_it_created(self):
        with vm.owned_short_workspace(self.root) as work:
            self.assertTrue(work.is_dir())
            self.assertEqual(work.parent, self.root)
            self.assertTrue(work.name.startswith('vm-'))
            (work / 'file.bin').write_bytes(b'x')
        self.assertFalse(work.exists())
        self.assertEqual((self.sibling / 'keep.txt').read_text(encoding='utf-8'), 'keep')

    def test_concurrent_workspaces_never_collide(self):
        with vm.owned_short_workspace(self.root) as first:
            with vm.owned_short_workspace(self.root) as second:
                self.assertNotEqual(first, second)
                self.assertTrue(first.is_dir() and second.is_dir())

    def test_failure_propagates_keeps_the_directory_and_reports_it(self):
        captured = io.StringIO()
        work_path = []
        with self.assertRaises(RuntimeError):
            with contextlib.redirect_stdout(captured):
                with vm.owned_short_workspace(self.root) as work:
                    work_path.append(work)
                    raise RuntimeError('simulated marker failure')
        self.assertTrue(work_path[0].is_dir(), 'evidence must be kept')
        self.assertIn('kept for diagnosis: ' + str(work_path[0]), captured.getvalue())
        self.assertEqual((self.sibling / 'keep.txt').read_text(encoding='utf-8'), 'keep')

    def test_too_deep_short_root_is_refused_before_anything_is_created(self):
        with self.assertRaises(ValueError):
            with vm.owned_short_workspace(DEEP):
                pass
        self.assertFalse(DEEP.exists())


class MarkerWorkspaceNonIsolatedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='marker-'))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.short = self.tmp / 'DK_TMP'
        self.keep = self.short / 'other-build'
        self.keep.mkdir(parents=True)
        (self.keep / 'keep.txt').write_text('keep', encoding='utf-8')

    def test_shallow_destination_uses_a_temporary_directory_that_is_removed(self):
        destination = self.tmp / 'output' / 'file.swf'
        destination.parent.mkdir()
        with vm.marker_workspace(destination, self.short) as work:
            self.assertEqual(work.parent, destination.parent)
            self.assertTrue(work.is_dir())
        self.assertFalse(work.exists())

    def test_deep_destination_uses_the_short_root_and_removes_only_its_directory(self):
        destination = DEEP / 'file.swf'
        with vm.marker_workspace(destination, self.short) as work:
            self.assertEqual(work.parent, self.short)
            (work / 'markers-0').mkdir()
        self.assertFalse(work.exists())
        self.assertEqual((self.keep / 'keep.txt').read_text(encoding='utf-8'), 'keep')


if __name__ == '__main__':
    unittest.main()
