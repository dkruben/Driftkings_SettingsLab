"""Windows fixtures only: no game tools or distribution packages."""
from contextlib import ExitStack
import ctypes
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from build_tools.build_diagnostics import inventory_tree, native_path, exception_record, record_failure
from build_tools.isolated_output import IsolatedOutput
from build_tools.vehicle_markers import marker_workspace


class CleanupTests(unittest.TestCase):
    def test_short_layout_success_exclusive_and_existing_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); outside=root/'previous';outside.mkdir();(outside/'sentinel').write_bytes(b'old')
            with IsolatedOutput(root,'run') as scope:
                dest=scope.path/'workspace/generated/build/flash/output.fixture'
                names=[]
                for unused in range(2):
                    with marker_workspace(dest) as work:
                        names.append(work)
                        self.assertEqual(work.parent,scope.path/'workspace/tmp')
                        path=work/'markers-0/net/wg/gui/battle/views/vehicleMarkers/statusMarkers/VehicleAnimatedStatusBaseMarker.script.asasm'
                        path.parent.mkdir(parents=True);path.write_bytes(b'fixture')
                        self.assertLess(len(str(path)),250)
                    self.assertFalse(work.exists())
                self.assertNotEqual(*names)
            self.assertEqual((outside/'sentinel').read_bytes(),b'old')

    def test_temporary_creation_failure_preserves_existing_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            with IsolatedOutput(Path(tmp),'run') as scope:
                parent=scope.path/'workspace/tmp';parent.mkdir();old=parent/'old.fixture';old.write_bytes(b'old')
                with patch('build_tools.vehicle_markers.tempfile.TemporaryDirectory',side_effect=PermissionError('fixture denied')):
                    with self.assertRaises(PermissionError):
                        with marker_workspace(scope.path/'workspace/output'):pass
                self.assertEqual(old.read_bytes(),b'old')
                self.assertEqual(list(parent.iterdir()),[old])

    def test_normal_layout_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/'output.fixture'
            with marker_workspace(destination) as work:
                self.assertEqual(work.parent,destination.parent)
                self.assertTrue(work.name.startswith('vehicle-markers-'))
                (work/'file.fixture').write_bytes(b'normal')
            self.assertFalse(work.exists())

    def test_deep_root_and_escapes_rejected_before_temporary_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/('r'*90);root.mkdir()
            with IsolatedOutput(root,'run') as scope:
                with patch('build_tools.vehicle_markers.tempfile.TemporaryDirectory') as factory:
                    for dest in (scope.path/'workspace/output',Path(tmp)/'outside',scope.path/'workspace/../outside'):
                        with self.assertRaises(ValueError):
                            with marker_workspace(dest):pass
                    factory.assert_not_called()
                self.assertFalse((scope.path/'workspace/tmp').exists())

    def test_failure_after_creation_cleaned_and_chained_cleanup_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            with IsolatedOutput(Path(tmp),'run') as scope:
                dest=scope.path/'workspace/output'
                with self.assertRaisesRegex(RuntimeError,'body'):
                    with marker_workspace(dest) as work:
                        (work/'file.fixture').write_bytes(b'own')
                        raise RuntimeError('body')
                self.assertFalse(work.exists())
                def broken_cleanup(path,*a,**kw):
                    raise OSError(145,'injected cleanup',str(path))
                with patch('tempfile.TemporaryDirectory._rmtree',side_effect=broken_cleanup):
                    with self.assertRaises(OSError) as caught:
                        with marker_workspace(dest) as remaining:
                            (remaining/'file.fixture').write_bytes(b'own')
                            raise RuntimeError('original body')
                self.assertIsInstance(caught.exception.__cause__,RuntimeError)
                self.assertTrue(remaining.exists())
                # Only this fixture, after mock is removed and no writer remains.
                scope.unpin_tree(remaining);shutil.rmtree(remaining)

    @unittest.skipUnless(os.name=='nt','Windows APIs')
    def test_real_lengths_creation_attributes_unlink_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            get=ctypes.WinDLL('kernel32',use_last_error=True).GetFileAttributesW
            get.argtypes=[ctypes.c_wchar_p];get.restype=ctypes.c_uint32
            for length in (259,260,263,264):
                with self.subTest(length=length):
                    case=root/str(length);case.mkdir();parent=case/'nested';parent.mkdir()
                    path=parent/('x'*(length-len(str(parent))-1));self.assertEqual(len(str(path)),length)
                    Path(native_path(path)).write_bytes(b'owned')
                    normal_access=get(str(path))!=0xffffffff
                    extended_access=get(native_path(path))!=0xffffffff
                    self.assertTrue(extended_access)
                    try:os.unlink(path)
                    except FileNotFoundError:
                        self.assertFalse(normal_access)
                    else:self.assertTrue(normal_access)
                    Path(native_path(path)).write_bytes(b'owned')
                    try:shutil.rmtree(case)
                    except OSError as error:
                        self.assertEqual(error.winerror,145)
                        self.assertFalse(normal_access)
                        self.assertTrue(os.path.exists(native_path(path)))
                    else:self.assertTrue(normal_access)
                    if os.path.exists(native_path(case)):
                        self.assertTrue(case.is_relative_to(root));shutil.rmtree(native_path(case))

    @unittest.skipUnless(os.name=='nt','Windows APIs')
    def test_open_handle_is_blocking_until_owner_releases_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            with IsolatedOutput(Path(tmp),'run') as scope:
                work_holder=[]
                k=ctypes.WinDLL('kernel32',use_last_error=True);create=k.CreateFileW
                create.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];create.restype=ctypes.c_void_p
                close=k.CloseHandle;close.argtypes=[ctypes.c_void_p]
                handle=None
                try:
                    with self.assertRaises(OSError):
                        with marker_workspace(scope.path/'workspace/out') as work:
                            work_holder.append(work);file=work/'locked.fixture';file.write_bytes(b'own')
                            handle=create(str(file),0x80000000,1,None,3,0,None)
                            self.assertNotEqual(handle,ctypes.c_void_p(-1).value)
                finally:
                    if handle is not None:close(handle)
                work=work_holder[0];self.assertTrue(work.exists())
                scope.unpin_tree(work);shutil.rmtree(work)

    def test_writer_process_waited_before_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            with IsolatedOutput(Path(tmp),'run') as scope:
                with marker_workspace(scope.path/'workspace/out') as work:
                    # Child writes only the owned fixture then exits; no game/compiler.
                    child=subprocess.Popen([sys.executable,'-B','-c',
                        'import sys,time;time.sleep(0.05);open(sys.argv[1],"wb").write(b"own")',str(work/'writer.fixture')],cwd=work)
                    self.assertIsNone(child.poll())
                    child.wait(timeout=10)
                    self.assertEqual(child.returncode,0)
                    self.assertEqual((work/'writer.fixture').read_bytes(),b'own')
                self.assertFalse(work.exists())

    def test_long_inventory_counts_and_unreadable_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);file=root/'known.fixture';file.write_bytes(b'own')
            long=root/('x'*(264-len(str(root))-1))
            if os.name=='nt':Path(native_path(long)).write_bytes(b'long')
            result=inventory_tree(root)
            self.assertTrue(result['complete']);self.assertEqual(result['file_count'],2 if os.name=='nt' else 1)
            self.assertEqual(result['file_count'],result['hashed_count']);self.assertEqual(result['unhashed_count'],0)
            original_open=__import__('builtins').open
            def denied(path,*a,**kw):
                if str(path)==native_path(file):raise PermissionError('fixture denied')
                return original_open(path,*a,**kw)
            with patch('builtins.open',side_effect=denied):result=inventory_tree(root)
            self.assertFalse(result['complete']);self.assertEqual(result['unhashed_count'],1)
            self.assertIsNone(result['entries']['known.fixture']['sha256'])
            self.assertEqual(result['errors'][0]['type'],'PermissionError')
            if os.name=='nt':os.unlink(native_path(long))

    @unittest.skipUnless(os.name=='nt','Windows junction')
    def test_inventory_junction_does_not_follow_external_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);outside=root/'outside';outside.mkdir();(outside/'sentinel').write_bytes(b'old')
            source=root/'source';source.mkdir();junction=source/'junction'
            result=subprocess.run(['cmd','/c','mklink','/J',str(junction),str(outside)],capture_output=True)
            self.assertEqual(result.returncode,0)
            try:
                result=inventory_tree(source)
                self.assertFalse(result['complete']);self.assertEqual(result['file_count'],0)
                self.assertEqual(result['entries']['junction']['kind'],'blocked_link')
                self.assertEqual((outside/'sentinel').read_bytes(),b'old')
            finally:os.rmdir(junction)

    def test_partial_cleanup_is_failure_and_existing_tmp_entries_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            with IsolatedOutput(Path(tmp),'run') as scope:
                parent=scope.path/'workspace/tmp';parent.mkdir()
                sentinel=parent/'previous.fixture';sentinel.write_bytes(b'previous')
                def partial(path,*a,**kw):
                    path=Path(path);(path/'removed.fixture').unlink()
                    raise OSError(145,'partial cleanup',str(path))
                with patch('tempfile.TemporaryDirectory._rmtree',side_effect=partial):
                    with self.assertRaisesRegex(OSError,'partial cleanup'):
                        with marker_workspace(scope.path/'workspace/out') as work:
                            (work/'removed.fixture').write_bytes(b'own')
                            (work/'remaining.fixture').write_bytes(b'own')
                self.assertFalse((work/'removed.fixture').exists())
                self.assertTrue((work/'remaining.fixture').exists())
                self.assertEqual(sentinel.read_bytes(),b'previous')
                scope.unpin_tree(work);shutil.rmtree(work)

    def test_inventory_explicit_missing_metadata_and_path_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);file=root/'vanished.fixture';file.write_bytes(b'own')
            original=os.lstat
            def missing(path,*a,**kw):
                if str(path)==native_path(file):raise FileNotFoundError('simulated disappearance')
                return original(path,*a,**kw)
            with patch('build_tools.build_diagnostics.os.lstat',side_effect=missing):result=inventory_tree(root)
            self.assertFalse(result['complete']);self.assertEqual(result['unknown_count'],1)
            self.assertEqual(result['errors'][0]['type'],'FileNotFoundError')
            with self.assertRaises(ValueError):native_path(root/'../outside')

    @unittest.skipUnless(os.name=='nt','Windows junction')
    def test_marker_tmp_junction_rejected_before_acquisition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);outside=root/'outside';outside.mkdir();(outside/'sentinel').write_bytes(b'old')
            scope=IsolatedOutput(root,'run').reserve()
            link=scope.path/'workspace/tmp'
            try:
                result=subprocess.run(['cmd','/c','mklink','/J',str(link),str(outside)],capture_output=True)
                self.assertEqual(result.returncode,0)
                scope.activate()
                with self.assertRaises(ValueError):
                    with marker_workspace(scope.path/'workspace/output'):pass
            finally:
                scope.close()
                if link.exists():os.rmdir(link)
            self.assertEqual((outside/'sentinel').read_bytes(),b'old')

    def test_traceback_chain_redaction_and_writer_failure_preserves_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            with IsolatedOutput(Path(tmp),'run') as scope:
                scope.phase='generate';scope.component='vehicle_markers_flash'
                try:
                    try:raise ValueError('token=secret-value payload="private-html"')
                    except ValueError as original:raise OSError(145,'cleanup',str(scope.path/'workspace/temp')) from original
                except OSError as error:
                    data=exception_record(error,scope)
                    serialized=json.dumps(data)
                    self.assertNotIn('secret-value',serialized);self.assertNotIn('private-html',serialized)
                    self.assertIn('ValueError',data['traceback']);self.assertIsNotNone(data['exception']['cause'])
                    def denied(*a):raise PermissionError('diagnostics denied')
                    with patch('sys.stderr',new_callable=io.StringIO) as stderr:
                        record_failure(scope,{},error,denied)
                        self.assertIn('original',stderr.getvalue())
                    self.assertTrue(error.__notes__)
                    self.assertEqual(data['component'],'vehicle_markers_flash')
                    self.assertEqual(data['phase'],'generate')


if __name__=='__main__':unittest.main()
