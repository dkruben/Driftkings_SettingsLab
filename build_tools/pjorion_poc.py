"""Phase 9 only: isolate PJOrion and protect one pure module; never deploy/publish."""
import argparse
import base64
import configparser
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

from pjorion_probe import POC, ROOT, probe

MODULE = 'res/scripts/client/Driftkings/core/marks_calculator.pyc'
SOURCE = ROOT / 'source/scripts/client/Driftkings/core/marks_calculator.py'
TOOL_FILES = ('PjOrion.exe', 'PjOrion.ini', 'python27.dll', 'python27.zip', 'dispack.zip', 'dcpack.zip')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def file_version(path):
    library = ctypes.WinDLL('version')
    library.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    library.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    library.VerQueryValueW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR,
                                      ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
    unused = wintypes.DWORD()
    size = library.GetFileVersionInfoSizeW(str(path), ctypes.byref(unused))
    if not size: raise RuntimeError('Version resource unavailable')
    buffer = ctypes.create_string_buffer(size)
    if not library.GetFileVersionInfoW(str(path), 0, size, buffer): raise RuntimeError('Version read failed')
    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    if not library.VerQueryValueW(buffer, '\\', ctypes.byref(pointer), ctypes.byref(length)):
        raise RuntimeError('Version query failed')
    value = ctypes.cast(pointer, ctypes.POINTER(wintypes.DWORD * 13)).contents
    return '.'.join(str(n) for n in (value[2] >> 16, value[2] & 65535, value[3] >> 16, value[3] & 65535))


def package(base, protected, output):
    with zipfile.ZipFile(base) as original:
        if original.testzip() is not None or len(original.namelist()) != len(set(original.namelist())):
            raise ValueError('Invalid baseline package')
        if MODULE not in original.namelist(): raise ValueError('Calculator absent from baseline')
        with zipfile.ZipFile(output, 'w') as result:
            for entry in original.infolist():
                result.writestr(entry, protected.read_bytes() if entry.filename == MODULE else original.read(entry))
    with zipfile.ZipFile(base) as original, zipfile.ZipFile(output) as result:
        if result.testzip() is not None or original.namelist() != result.namelist():
            raise ValueError('Experimental package structure changed')
        changed = [name for name in original.namelist() if original.read(name) != result.read(name)]
        if changed != [MODULE]: raise ValueError('POC must change exactly one module')
        meta = ET.fromstring(result.read('meta.xml'))
        return dict(changed=changed, entries=len(result.namelist()), version=meta.findtext('version'),
                    size=output.stat().st_size, sha256=sha(output), published=False, deployed=False)


def run_checked(argv, name, timeout=60):
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    result = subprocess.run(argv, cwd=str(ROOT), capture_output=True, timeout=timeout,
                            startupinfo=startup, creationflags=0x08000000)
    (POC / (name + '.stdout.log')).write_bytes(result.stdout)
    (POC / (name + '.stderr.log')).write_bytes(result.stderr)
    if result.returncode != 0:
        raise RuntimeError('%s failed with exit code %s; see sandbox logs' % (name, result.returncode))


def run(tool, python, baseline):
    POC.mkdir(parents=True, exist_ok=True)
    experimental = POC / 'Driftkings-PJOrion-POC.wotmod'
    if experimental.exists(): experimental.unlink()
    installed = {name: sha(tool / name) for name in TOOL_FILES}
    original_source = sha(SOURCE)
    report = dict(status='running', decision='NO-GO pending real WoT test', phase=9,
                  pjOrionVersion=file_version(tool / 'PjOrion.exe'),
                  bundledPythonNumericVersion=file_version(tool / 'python27.dll'),
                  originalToolHashes=installed, sourceSha256=original_source, processed=[MODULE],
                  failed=[], profile='poc-public-names-standalone', realWoT='not tested', published=False)
    started = time.monotonic()
    try:
        sandbox = POC / 'tool'
        sandbox.mkdir(exist_ok=True)
        for name in TOOL_FILES: shutil.copyfile(tool / name, sandbox / name)
        shutil.copytree(tool / 'DLLs', sandbox / 'DLLs', dirs_exist_ok=True)
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(sandbox / 'PjOrion.ini')
        settings = {'GENERAL': {'CheckWebUpdate': '0', 'AutoConnect': '1'},
                    'PATHS': {'Python': base64.b64encode(str(sandbox / 'python27.dll').encode()).decode()},
                    'FILEASSOCIATIONS': {'RegisterApplication': '0', 'PY': '0', 'PYC': '0'},
                    'CONTEXTMENU': {'Integrate': '0'},
                    'WOTTRANSMISSION': {'SearchWOT': '0', 'WOT': ''},
                    'OBFUSCATE': {'AllNamesIsPublic': '1', 'DetailedAnalysis': '1'},
                    'PROTECT': {'ExecOnlyInWOT': '0', 'LockAttributesReview': '0',
                                'UseWOTInjector': '0', 'CreateBackupFile': '0'}}
        for section, values in settings.items():
            for name, value in values.items(): config.set(section, name, value)
        inputs, outputs = POC / 'input', POC / 'protected'
        inputs.mkdir(exist_ok=True)
        outputs.mkdir(exist_ok=True)
        config.set('PATHS', 'SelectedDir', base64.b64encode(str(inputs).encode()).decode())
        with (sandbox / 'PjOrion.ini').open('w', encoding='utf-8') as handle:
            config.write(handle, space_around_delimiters=False)
        shutil.copy2(SOURCE, inputs / 'marks_calculator.py')
        input_file = inputs / 'marks_calculator.pyc'
        run_checked([str(python), '-B', '-c',
                     'import py_compile,sys;py_compile.compile(sys.argv[1],sys.argv[2],dfile="Driftkings/core/marks_calculator.py",doraise=True)',
                     str(inputs / 'marks_calculator.py'), str(input_file)], 'compile')
        protected = outputs / 'marks_calculator.pyc'
        shutil.copyfile(input_file, protected)
        configuration_before = sha(sandbox / 'PjOrion.ini')
        action = probe('protect', ['--protect-bytecode-file=' + str(protected), '/exit'], protected, timeout=45)
        report.update(configuration=settings, input=dict(path=str(input_file), size=input_file.stat().st_size, sha256=sha(input_file)),
                      cli=action, configurationSha256Before=configuration_before,
                      configurationSha256After=sha(sandbox / 'PjOrion.ini'))
        if action['timeout'] or action['exitCode'] != 0:
            raise RuntimeError('PJOrion failed or timed out; no diagnostic fallback')
        data = protected.read_bytes()
        if len(data) < 8 or data[:4] != b'\x03\xf3\x0d\x0a' or sha(protected) == sha(input_file):
            raise ValueError('PJOrion output missing, unchanged or wrong bytecode format')
        report['output'] = dict(path=str(protected), size=len(data), sha256=sha(protected))
        runtime = ROOT / 'build_tools/pjorion_poc_runtime.py'
        common = [str(python), '-B', str(runtime), '--original', str(SOURCE), '--protected', str(protected)]
        run_checked(common + ['--output', str(POC / 'runtime-python2718.json')], 'python2718')
        report['package'] = package(baseline, protected, experimental)
        run_checked(common + ['--output', str(POC / 'runtime-python2718-package.json'), '--package', str(experimental)], 'python2718-package')
        hg = Path(os.environ.get('LOCALAPPDATA', '')) / 'Atlassian/SourceTree/hg_local/hg.exe'
        run_checked([str(hg), '--config', 'extensions.dkorionpoc=build_tools/pjorion_poc_hg.py', 'dkorionpoc'], 'build-python')
        report['runtimeTests'] = {name: json.loads((POC / (name + '.json')).read_text()) for name in
                                  ('runtime-python2718', 'runtime-python2718-package', 'runtime-build', 'runtime-build-package')}
        report['status'] = 'local checks passed; real WoT approval pending'
        return report
    except Exception as error:
        report['status'] = 'failed'
        report['failed'].append(str(error))
        if experimental.exists(): experimental.unlink()
        raise
    finally:
        report['originalToolUnchanged'] = all(sha(tool / name) == value for name, value in installed.items())
        report['sourceUnchanged'] = sha(SOURCE) == original_source
        report['seconds'] = time.monotonic() - started
        if not report['sourceUnchanged'] or not report['originalToolUnchanged']:
            report['status'] = 'failed'
            report['failed'].append('Original source/tool changed')
            if experimental.exists(): experimental.unlink()
        (POC / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        if report['status'] == 'failed' and not report['failed']: report['failed'].append('Validation failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', type=Path, default=Path('F:/Programas/PJOrion'))
    parser.add_argument('--python', type=Path, default=Path('F:/Python27/python.exe'))
    parser.add_argument('--baseline', type=Path, default=ROOT / 'build/release/Driftkings.wotmod')
    args = parser.parse_args()
    result = run(args.tool.resolve(), args.python.resolve(), args.baseline.resolve())
    if result['status'] == 'failed': raise SystemExit(1)
    print(json.dumps({key: result[key] for key in ('status', 'decision', 'pjOrionVersion', 'input', 'output', 'package')}, indent=2))
