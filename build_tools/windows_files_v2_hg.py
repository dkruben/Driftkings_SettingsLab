# -*- coding: utf-8 -*-
"""One-shot L2-v2b: diagnostic Unicode only, unchanged scan fixture/backend."""
from mercurial import registrar
import datetime
import hashlib
import io
import json
import os
import sys
import traceback
import zipfile

cmdtable = {}
command = registrar.command(cmdtable)


@command('dkwindowsv2', [], '', norepo=True)
def run(ui, **opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.dont_write_bytecode = True
    workspace = os.path.abspath('.')
    sys.path.insert(0, os.path.join(workspace, 'build_tools'))
    from windows_files_diagnostic_json import _to_json_unicode, json_bytes
    folder = os.path.join(workspace, 'build/diagnostics/windows-files-v2/receipt-l2-v2b')
    if os.environ.get('DK_WINDOWS_FILES_ATTEMPT') != 'receipt-l2-v2b':
        raise ValueError('Launch only through the gated one-shot launcher')
    root = os.path.join(folder, 'fixture')
    os.makedirs(root)
    def record(event, **values):
        values.update(event=event, timestampUTC=datetime.datetime.utcnow().isoformat()+'Z', hostPid=os.getpid())
        with open(os.path.join(folder, 'process-events.jsonl'), 'ab') as stream:
            stream.write(json_bytes(values)+b'\n')
            stream.flush(); os.fsync(stream.fileno())
    record('host-start', python=sys.version, executable=sys.executable, argv=sys.argv)
    assert sys.version_info[:3] == (2, 7, 15)
    sys.path.insert(0, os.path.join(workspace, 'source/scripts/client'))
    import Driftkings.core.updater.results as results
    import Driftkings.core.updater.windows_files as windows
    from Driftkings.core.updater.manifest import Manifest
    from Driftkings.core.updater.installer import write_new
    def package(version):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
            archive.writestr('meta.xml', '<root><id>driftkings.unified</id><version>%s</version></root>' % version)
            archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc', b'\x03\xf3\x0d\x0a'+b'\0'*20)
        return output.getvalue()
    def snapshot():
        hashes, metadata = {}, {}
        for directory, dirs, files in os.walk(root):
            for name in dirs+files:
                path = os.path.join(directory, name)
                key = _to_json_unicode(os.path.relpath(path, root))
                value = os.stat(path)
                metadata[key] = [getattr(value, field, None) for field in
                                 ('st_size', 'st_mtime', 'st_ctime', 'st_ino', 'st_file_attributes')]
                if name in files:
                    with open(path, 'rb') as stream: hashes[key] = hashlib.sha256(stream.read()).hexdigest()
        return dict(hashes=hashes, metadata=metadata)
    stage = os.path.join(root, 'mods/configs/Driftkings/cache/update/download-receipt')
    os.makedirs(stage)
    old, new = package('0.1.0'), package('1.0.0')
    manifest = Manifest(dict(schema=1, version='1.0.0', channel='stable', gameVersion='2.4.0.2',
        file='Driftkings.wotmod', size=len(new), sha256=hashlib.sha256(new).hexdigest(),
        download='https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v1.0.0/Driftkings.wotmod'))
    ticket = dict(schema=1, gameVersion='2.4.0.2', version='1.0.0', size=len(new), sha256=manifest.sha256,
        installedVersion='0.1.0', installedSize=len(old), installedSha256=hashlib.sha256(old).hexdigest())
    write_new(os.path.join(stage, 'install.json'), ticket)
    write_new(os.path.join(stage, 'release.json'), manifest.document())
    write_new(os.path.join(stage, 'result.json'), dict(schema=1, status='installed', helperPid=123, error=None))
    target = os.path.join(root, 'mods/2.4.0.2/Driftkings.wotmod')
    os.makedirs(os.path.dirname(target))
    with open(target, 'wb') as stream: stream.write(new)
    unicode_path = os.path.join(stage, u'path-\u00e1')
    os.mkdir(unicode_path)
    before = snapshot()
    with open(os.path.join(folder, 'fixture-before.json'), 'wb') as stream:
        stream.write(json_bytes(before, indent=2))
    reader = results.Results(root, loaded_version='1.0.0')
    def fixture_package(ticket, old=False):
        assert not old and ticket['sha256'] == hashlib.sha256(new).hexdigest()
        record('controlled-package-validation', note='Same known package adapter as old L2; no receipt acknowledgement')
    reader._package_matches = fixture_package
    popen, native_path = windows.subprocess.Popen, windows.safe_path
    processes, calls, responses = [], [], []
    counts = {'V': 0, 'R': 0}
    original_request = windows.WindowsPathValidator.request
    original_response = windows.WindowsPathValidator.response
    original_close = windows.WindowsPathValidator.close
    def observed_response(client):
        try:
            value = original_response(client)
            responses.append(value)
            record('ipc-response', response=value, helperPid=client.process.pid)
            return value
        except Exception as error:
            record('ipc-response-error', error=repr(error), helperPid=client.process.pid,
                   timeout='timeout' in str(error).lower(), prematureEOF='without response' in str(error).lower())
            raise
    def observed_request(client, operation, *paths):
        counts[operation] += 1
        record('ipc-request', operation=operation, paths=paths)
        try:
            value = original_request(client, operation, *paths)
            record('ipc-request-completed', operation=operation, helperPid=client.process.pid)
            return value
        except Exception as error:
            record('ipc-request-error', operation=operation, error=repr(error), winerror=getattr(error, 'winerror', None))
            raise
    def observed_close(client):
        record('stdin-eof-requested', helperPid=client.process.pid if client.process else None)
        original_close(client)
        record('session-closed', helperPid=client.process.pid if client.process else None,
               exitCode=client.process.returncode if client.process else None)
    def observed_popen(argv, *args, **kwargs):
        record('before-child-launch', argv=argv, creationflags=kwargs.get('creationflags'))
        process = popen(argv, *args, **kwargs)
        processes.append(process)
        record('child-created', childPid=process.pid, parentPid=os.getpid(), argv=argv)
        return process
    def observed_path(path):
        calls.append(path)
        record('safe-path-start', path=path)
        try:
            value = native_path(path)
            record('safe-path-end', path=path, accepted=True)
            return value
        except Exception as error:
            record('safe-path-error', path=path, error=repr(error), winerror=getattr(error, 'winerror', None))
            raise
    windows.subprocess.Popen, windows.safe_path = observed_popen, observed_path
    windows.WindowsPathValidator.request = observed_request
    windows.WindowsPathValidator.response = observed_response
    windows.WindowsPathValidator.close = observed_close
    def resource(name):
        mapping = {windows.HELPER_RESOURCE:'Driftkings.WindowsFiles.exe', windows.INFO_RESOURCE:'helper.json'}
        with open(os.path.join(workspace, 'build/windows-files', mapping[name]), 'rb') as stream: return stream.read()
    try:
        windows.initialize(resource, workspace, os.path.join(folder, 'client-cache'))
        record('scan-start')
        reports = reader.scan('2.4.0.2')
        record('scan-end', reports=reports)
        assert len(reports) == 1 and reports[0]['status'] == 'installed' and reports[0]['error'] is None
        windows.safe_path(os.path.join(stage, 'Driftkings.wotmod.ready'))
        windows.safe_path(unicode_path)
        try: windows.safe_path(os.path.join(stage, 'invalid\x00path'))
        except OSError: record('invalid-path-rejected-as-expected')
        else: raise AssertionError('Invalid path accepted')
        after = snapshot()
        assert before == after, 'Read-only fixture changed'
        assert len(processes) == 1, 'One reusable native process required'
        assert responses[0] == b'READY\t1', 'Required handshake absent'
        assert counts['V'] == len(calls) and counts['V'] >= 8 and counts['R'] == 0
        assert len(responses) == counts['V'] + 1
        assert responses[-1].startswith(b'ERR\t1001\t'), 'Invalid path must be rejected explicitly'
        windows.close()
        assert processes[0].returncode == 0
        record('child-finished', childPid=processes[0].pid, exitCode=processes[0].returncode)
        output = dict(status='PASS', python=sys.version, hostPid=os.getpid(), reports=reports,
            safePathCalls=len(calls), nativeWindowsValidation=True, fixtureUnchanged=True,
            fixtureBefore=before, fixtureAfter=after, fixtureAdapters=['reader._package_matches'],
            receiptAcknowledgement=False, helperProcesses=1, handshake='READY\t1',
            requests=counts, responses=responses, timeout=False, prematureEOF=False)
        with open(os.path.join(folder, 'operation-completed.json'), 'wb') as stream:
            stream.write(json_bytes(output, indent=2))
        record('operation-completed')
    except BaseException as error:
        record('operation-error', error=repr(error), stackTrace=traceback.format_exc())
        raise
    finally:
        windows.close()
        windows.subprocess.Popen, windows.safe_path = popen, native_path
        windows.WindowsPathValidator.request = original_request
        windows.WindowsPathValidator.response = original_response
        windows.WindowsPathValidator.close = original_close
    return 0
