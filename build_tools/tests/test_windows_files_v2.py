"""Real Windows fixtures for owned IPC, Win32 reparse checks and atomic receipts."""
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/scripts/client'))
from Driftkings.core.updater import windows_files as windows
FOLDER=ROOT/'build/diagnostics/windows-files-v2'


def initialize():
    FOLDER.mkdir(parents=True,exist_ok=True)
    files={windows.HELPER_RESOURCE:(ROOT/'build/windows-files/Driftkings.WindowsFiles.exe').read_bytes(),
           windows.INFO_RESOURCE:(ROOT/'build/windows-files/helper.json').read_bytes()}
    windows.initialize(files.__getitem__,str(ROOT),str(FOLDER/'client-cache'))


def kernel():
    native=ctypes.WinDLL('kernel32',use_last_error=True)
    native.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    native.CreateFileW.restype=wintypes.HANDLE
    native.CloseHandle.argtypes=[wintypes.HANDLE]
    native.DeviceIoControl.argtypes=[wintypes.HANDLE,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
    return native


def junction(link,target):
    link.mkdir()
    api=kernel()
    handle=api.CreateFileW(str(link),0x40000000,7,None,3,0x02200000,None)
    if handle==ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
    substitute=('\\??\\'+str(target)).encode('utf-16le')
    printable=str(target).encode('utf-16le')
    data=struct.pack('<HHHH',0,len(substitute),len(substitute)+2,len(printable))+substitute+b'\0\0'+printable+b'\0\0'
    buffer=ctypes.create_string_buffer(struct.pack('<IHH',0xA0000003,len(data),0)+data)
    returned=wintypes.DWORD()
    try:
        if not api.DeviceIoControl(handle,0x900A4,buffer,len(buffer)-1,None,0,ctypes.byref(returned),None):
            raise ctypes.WinError(ctypes.get_last_error())
    finally: api.CloseHandle(handle)


@unittest.skipUnless(os.name=='nt','Real Windows only')
class WindowsFilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): initialize()

    @classmethod
    def tearDownClass(cls): windows.close()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=FOLDER)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.stage=self.root/'mods/configs/Driftkings/cache/update/download-test'
        self.stage.mkdir(parents=True)

    def files(self):
        source,target=self.stage/'notice-test',self.stage/'notified.json'
        source.write_bytes(b'{"new":true}')
        target.write_bytes(b'{"old":true}')
        return source,target

    def test_paths_unicode_spaces_missing_mixed_and_one_process(self):
        directory=self.root/'Unicode-\u00e1 spaces'
        directory.mkdir()
        file=directory/'file.json'; file.write_bytes(b'data')
        paths=[directory,file,directory/'missing.json',directory/'missing-parent/missing.json']
        pid=None
        for path in paths:
            windows.safe_path(str(path))
            current=windows._client.process.pid
            if pid is None: pid=current
            self.assertEqual(current,pid)
        windows.safe_path(str(directory).replace('\\','/')+'/')
        windows.safe_path(str(directory).swapcase())
        self.assertEqual(windows._client.process.pid,pid)

    def test_rejects_unc_devices_traversal_ads_invalid_drive_and_escape(self):
        for path in ('\\\\server\\share\\file','\\\\?\\C:\\file',str(self.root/'../escape'),
                     str(self.root/'file:stream'),str(self.root/'invalid<>file'),str(self.root/'NUL'),
                     'Z:\\not-our-root','C:\\outside-owned-root','relative\\file'):
            with self.subTest(path=path),self.assertRaises(OSError): windows.safe_path(path)

    def test_real_junction_and_ancestor_reparse(self):
        target=self.root/'target'; target.mkdir()
        link=self.root/'junction'
        junction(link,target)
        self.addCleanup(link.rmdir)
        self.assertTrue(link.stat(follow_symlinks=False).st_file_attributes&0x400)
        for path in (link,link/'missing.json',link/'sub/missing.json'):
            with self.assertRaises(OSError): windows.safe_path(str(path))

    def test_symlink_file_and_directory(self):
        target=self.root/'file';target.write_bytes(b'owned')
        link=self.root/'symlink'
        try: link.symlink_to(target)
        except OSError as error:
            raise
        self.addCleanup(link.unlink)
        with self.assertRaises(OSError): windows.safe_path(str(link))
        directory=self.root/'dir';directory.mkdir()
        other=self.root/'dir-link';other.symlink_to(directory,target_is_directory=True)
        self.addCleanup(other.unlink)
        with self.assertRaises(OSError): windows.safe_path(str(other/'missing'))

    def test_access_denied_real_directory_acl(self):
        directory=self.root/'denied';directory.mkdir()
        api=ctypes.WinDLL('advapi32',use_last_error=True)
        api.GetFileSecurityW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
        api.SetFileSecurityW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.c_void_p]
        api.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(wintypes.DWORD)]
        needed=wintypes.DWORD()
        api.GetFileSecurityW(str(directory),4,None,0,ctypes.byref(needed))
        original=ctypes.create_string_buffer(needed.value)
        self.assertTrue(api.GetFileSecurityW(str(directory),4,original,len(original),ctypes.byref(needed)))
        descriptor=ctypes.c_void_p()
        self.assertTrue(api.ConvertStringSecurityDescriptorToSecurityDescriptorW('D:(D;;FA;;;WD)',1,ctypes.byref(descriptor),None))
        try:
            self.assertTrue(api.SetFileSecurityW(str(directory),4,descriptor))
            with self.assertRaises(OSError) as caught: windows.safe_path(str(directory/'missing.json'))
            self.assertEqual(caught.exception.winerror,5)
        finally:
            self.assertTrue(api.SetFileSecurityW(str(directory),4,original))
            native=kernel();native.LocalFree.argtypes=[ctypes.c_void_p];native.LocalFree(descriptor)

    def test_atomic_ancestor_junction_preserves_real_target(self):
        source,target=self.files()
        link=self.root/'transaction-link'
        junction(link,self.stage)
        self.addCleanup(link.rmdir)
        with self.assertRaises(OSError): windows.replace_receipt(str(link/source.name),str(link/target.name))
        self.assertEqual(target.read_bytes(),b'{"old":true}')
        self.assertEqual(source.read_bytes(),b'{"new":true}')

    def test_atomic_success_no_backup_no_truncation(self):
        source,target=self.files()
        windows.replace_receipt(str(source),str(target))
        self.assertEqual(target.read_bytes(),b'{"new":true}')
        self.assertFalse(source.exists())
        self.assertEqual(sorted(p.name for p in self.stage.iterdir()),['notified.json'])

    def test_atomic_missing_target_and_invalid_source_preserve_files(self):
        source,target=self.files()
        target.unlink()
        with self.assertRaises(OSError): windows.replace_receipt(str(source),str(target))
        self.assertFalse(target.exists());self.assertEqual(source.read_bytes(),b'{"new":true}')
        target.write_bytes(b'old')
        with self.assertRaises(OSError): windows.replace_receipt(str(self.stage/'notice-missing'),str(target))
        self.assertEqual(target.read_bytes(),b'old')

    def test_atomic_rejects_readonly_and_locked_target(self):
        source,target=self.files()
        target.chmod(0o444)
        try:
            with self.assertRaises(OSError): windows.replace_receipt(str(source),str(target))
            self.assertEqual(target.read_bytes(),b'{"old":true}')
        finally: target.chmod(0o666)
        api=kernel();handle=api.CreateFileW(str(target),0x80000000,0,None,3,0,None)
        self.assertNotEqual(handle,ctypes.c_void_p(-1).value)
        try:
            with self.assertRaises(OSError): windows.replace_receipt(str(source),str(target))
        finally:api.CloseHandle(handle)
        self.assertEqual(target.read_bytes(),b'{"old":true}')

    def test_atomic_rejects_other_dir_volume_and_arbitrary_target(self):
        source,target=self.files()
        for src,dst in ((str(source),str(self.root/'notified.json')),(str(source),'Z:\\notified.json'),
                        (str(source),str(self.stage/'user.json')),(str(self.stage/'notified.json'),str(target))):
            with self.assertRaises(OSError): windows.replace_receipt(src,dst)
        self.assertEqual(target.read_bytes(),b'{"old":true}')

    def test_hash_mismatch_and_missing_helper_fail_closed(self):
        client=windows._client
        with patch.object(client,'sha256','0'*64),self.assertRaises(OSError): windows.safe_path(str(self.root))
        with patch.object(client,'binary',str(self.root/'missing.exe')),self.assertRaises(OSError): windows.safe_path(str(self.root))

    def test_injected_transport_failure_preserves_target(self):
        source,target=self.files()
        with patch.object(windows._client,'request',side_effect=OSError('injected')),self.assertRaises(OSError):
            windows.replace_receipt(str(source),str(target))
        self.assertEqual(target.read_bytes(),b'{"old":true}')
        self.assertTrue(source.exists())

    def isolated_client(self):
        original=windows._client
        client=windows.WindowsPathValidator(original.binary,original.root,original.sha256)
        self.addCleanup(client.close)
        return client

    def test_invalid_handshake_fails_closed_with_owned_process(self):
        client=self.isolated_client()
        with patch.object(client,'response',return_value=b'INVALID'),self.assertRaises(OSError): client.start()
        self.assertTrue(client.failed)
        with self.assertRaises(OSError): client.request('V',str(self.root))

    def test_eof_after_real_helper_exit_fails_closed(self):
        client=self.isolated_client();client.start()
        client.process.kill();client.process.wait()
        with self.assertRaises(OSError): client.response()
        self.assertTrue(client.failed)

    def test_timeout_kills_owned_helper_and_prevents_retry(self):
        client=self.isolated_client();client.start()
        with patch.object(client.responses,'get',side_effect=windows.queue.Empty),self.assertRaises(OSError): client.response()
        client.process.wait()
        self.assertTrue(client.failed)
        with self.assertRaises(OSError): client.request('V',str(self.root))
