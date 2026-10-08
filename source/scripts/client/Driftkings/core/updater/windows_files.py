# -*- coding: utf-8 -*-
"""Bounded Windows file operations without the optional _ctypes extension."""
import base64
import os
import subprocess
import threading

try:
    TEXT = unicode
except NameError:
    TEXT = str

CHECK = """
function CheckPath([string]$path) {
    $current = [System.IO.Path]::GetFullPath($path)
    while ($current) {
        try { $attributes = [System.IO.File]::GetAttributes($current) }
        catch [System.IO.FileNotFoundException] { $attributes = 0 }
        catch [System.IO.DirectoryNotFoundException] { $attributes = 0 }
        if (([int]$attributes -band 1024) -ne 0) { throw 'Reparse path rejected' }
        $parent = [System.IO.Path]::GetDirectoryName($current)
        if ($parent -eq $current) { break }
        $current = $parent
    }
}
"""


def literal(path):
    # Only base64 enters the fixed script; quotes/metacharacters in paths are data.
    path = os.path.abspath(path)
    if not isinstance(path, TEXT):
        path = path.decode('mbcs')
    value = base64.b64encode(path.encode('utf-8')).decode('ascii')
    return "[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('%s'))" % value


def run(script):
    executable = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'),
                              'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
    if not os.path.isfile(executable):
        raise OSError('Windows file validation unavailable')
    encoded = base64.b64encode(("$ErrorActionPreference='Stop'; try { " + script +
                               "; [Console]::Write('OK') } catch { [Console]::Error.Write($_.Exception.Message); exit 1 }").encode('utf-16le')).decode('ascii')
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    process = subprocess.Popen([executable, '-NoLogo', '-NoProfile', '-NonInteractive',
                                '-EncodedCommand', encoded], shell=False,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               startupinfo=startup, creationflags=0x08000000)
    expired = threading.Event()
    def expire():
        if process.poll() is None:
            expired.set()
            try:
                process.kill()
            except OSError:
                pass
    timer = threading.Timer(10.0, expire)
    timer.daemon = True
    timer.start()
    try:
        output, unused = process.communicate()
        if expired.is_set() or process.returncode != 0 or output != b'OK':
            raise OSError('Windows file validation or receipt replacement failed: ' + unused.decode('utf-8', 'replace')[:512])
    finally:
        timer.cancel()


def safe_path(path):
    run(CHECK + '; CheckPath (' + literal(path) + ')')


def replace_receipt(source, destination):
    if os.path.dirname(os.path.abspath(source)) != os.path.dirname(os.path.abspath(destination)):
        raise ValueError('Receipt replacement must stay in the operation directory')
    run(CHECK + '; $source=' + literal(source) + '; $destination=' + literal(destination) +
        '; CheckPath $source; CheckPath $destination; '
        "[System.IO.File].GetMethod('Replace',[type[]]@([string],[string],[string])).Invoke($null,[object[]]@($source,$destination,$null))")
