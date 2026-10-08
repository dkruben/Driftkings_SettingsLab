"""Observe PJOrion CLI only in the local POC sandbox, with a bounded wait."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / 'build/obfuscation/poc'


def window_text(pid):
    user = ctypes.WinDLL('user32', use_last_error=True)
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.EnumWindows.argtypes = [callback, wintypes.LPARAM]
    user.EnumChildWindows.argtypes = [wintypes.HWND, callback, wintypes.LPARAM]
    user.SendMessageTimeoutW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                         ctypes.c_void_p, wintypes.UINT, wintypes.UINT,
                                         ctypes.POINTER(ctypes.c_size_t)]
    texts = []
    def read(handle):
        buffer = ctypes.create_unicode_buffer(4096)
        user.GetWindowTextW(handle, buffer, len(buffer))
        if not buffer.value:
            count = ctypes.c_size_t()
            user.SendMessageTimeoutW(handle, 0x000D, len(buffer), ctypes.cast(buffer, ctypes.c_void_p),
                                     2, 100, ctypes.byref(count))
        if buffer.value: texts.append(buffer.value)
    @callback
    def child(handle, unused):
        read(handle)
        return True
    @callback
    def window(handle, unused):
        owner = wintypes.DWORD()
        user.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value == pid:
            read(handle)
            user.EnumChildWindows(handle, child, 0)
        return True
    user.EnumWindows(window, 0)
    return texts


def probe(name, arguments, target, timeout=12, sandbox=None):
    sandbox = Path(sandbox or POC).resolve()
    sandbox.relative_to((ROOT / 'build/obfuscation').resolve())
    target = Path(target).resolve()
    target.relative_to(sandbox)
    permitted = []
    for action in ('protect-bytecode-file', 'obfuscate-bytecode-file', 'compile-file'):
        permitted.extend([['/' + action, str(target), '/exit'], ['--' + action + '=' + str(target), '/exit']])
    if arguments not in permitted:
        raise ValueError('Only the exact sandbox file may be passed to a POC action')
    executable = sandbox / 'tool/PjOrion.exe'
    argv = [str(executable)] + arguments
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    before = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
    started = time.monotonic()
    process = subprocess.Popen(argv, cwd=str(executable.parent), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, startupinfo=startup, creationflags=0x08000000)
    expired, texts = False, []
    try:
        output, error = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        expired = True
        texts = window_text(process.pid)
        process.kill()  # Only this sandbox process, never a game/tool instance.
        output, error = process.communicate()
    report = dict(argv=argv, exitCode=process.returncode, timeout=expired,
                  seconds=time.monotonic() - started, windows=texts, inputSha256=before,
                  stdout=output.decode('utf-8', 'replace'), stderr=error.decode('utf-8', 'replace'),
                  outputs={p.name: dict(size=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                           for p in target.parent.iterdir() if p.is_file()})
    (sandbox / (name + '.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('target')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    print(json.dumps(probe(args.name, args.arguments, args.target), indent=2))
