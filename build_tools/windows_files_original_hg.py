# -*- coding: utf-8 -*-
"""Run one unchanged original test, with observation-only native IPC logging."""
from mercurial import registrar
import datetime
import hashlib
import imp
import json
import os
import shutil
import sys
import traceback
import unittest

cmdtable = {}
command = registrar.command(cmdtable)
TEST = 'test_post_restart_receipt_python27_windows_paths_and_deduplication'


@command('dkwindowsoriginal', [], '', norepo=True)
def run(ui, **opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.dont_write_bytecode = True
    assert sys.version_info[:3] == (2, 7, 15)
    workspace = os.path.abspath('.')
    folder = os.path.join(workspace, 'build/diagnostics/windows-files-v2/original-smoke-v2')
    if os.environ.get('DK_WINDOWS_FILES_ATTEMPT') != 'original-smoke-v2':
        raise ValueError('Use the gated one-shot launcher')
    sys.path.insert(0, os.path.join(workspace, 'build_tools'))
    from windows_files_diagnostic_json import json_bytes
    def record(event, **values):
        values.update(event=event, timestampUTC=datetime.datetime.utcnow().isoformat()+'Z', hostPid=os.getpid())
        with open(os.path.join(folder, 'process-events.jsonl'), 'ab') as stream:
            stream.write(json_bytes(values)+b'\n'); stream.flush(); os.fsync(stream.fileno())
    record('host-start', python=sys.version, executable=sys.executable, argv=sys.argv)
    tests = imp.load_source('dk_original_smoke', os.path.join(workspace, 'build_tools/tests/test_updater_smoke.py'))
    from Driftkings.core.updater import windows_files as windows
    from Driftkings.core.updater.results import Results
    processes, responses, scans, acknowledgements, replacements = [], [], [], [], []
    counts = {'V':0, 'R':0}
    snapshots = {}
    original = dict(popen=windows.subprocess.Popen, request=windows.WindowsPathValidator.request,
                    response=windows.WindowsPathValidator.response, close=windows.WindowsPathValidator.close,
                    scan=Results.scan, acknowledge=Results.acknowledge, rmtree=shutil.rmtree)
    def snapshot(root):
        output = {}
        for directory, unused, files in os.walk(root):
            for name in files:
                path = os.path.join(directory, name)
                with open(path, 'rb') as stream: data = stream.read()
                value = dict(size=len(data), sha256=hashlib.sha256(data).hexdigest())
                if name.endswith('.json'): value['json'] = json.loads(data.decode('utf-8'))
                output[os.path.relpath(path, root)] = value
        return output
    def observed_popen(argv, *args, **kwargs):
        record('before-child-launch', argv=argv, shell=kwargs.get('shell', False), creationflags=kwargs.get('creationflags'))
        process = original['popen'](argv, *args, **kwargs)
        processes.append(process)
        record('child-created', argv=argv, childPid=process.pid, parentPid=os.getpid())
        return process
    def observed_response(client):
        try:
            value = original['response'](client)
            responses.append(value)
            record('ipc-response', response=value, helperPid=client.process.pid)
            return value
        except Exception as error:
            record('ipc-response-error', error=repr(error), timeout='timeout' in str(error).lower(),
                   prematureEOF='without response' in str(error).lower())
            raise
    def observed_request(client, operation, *paths):
        counts[operation] += 1
        record('ipc-request', operation=operation, paths=paths)
        evidence = None
        if operation == 'R':
            source, target = paths
            with open(source,'rb') as stream: source_hash = hashlib.sha256(stream.read()).hexdigest()
            with open(target,'rb') as stream: target_hash = hashlib.sha256(stream.read()).hexdigest()
            evidence = dict(source=source, target=target, sameDirectory=os.path.dirname(source)==os.path.dirname(target),
                sourceRegular=os.path.isfile(source) and not os.path.islink(source), targetExists=os.path.isfile(target),
                sourceSha256=source_hash, targetBeforeSha256=target_hash)
            record('replacement-before', **evidence)
        try:
            value = original['request'](client, operation, *paths)
            record('ipc-request-completed', operation=operation, helperPid=client.process.pid)
            if evidence is not None:
                with open(paths[1], 'rb') as stream: actual = hashlib.sha256(stream.read()).hexdigest()
                evidence.update(sourceConsumed=not os.path.exists(paths[0]), targetAfterSha256=actual)
                replacements.append(evidence)
                record('replacement-after', **evidence)
            return value
        except Exception as error:
            record('ipc-request-error', operation=operation, error=repr(error), winerror=getattr(error,'winerror',None))
            raise
    def observed_close(client):
        record('stdin-eof-requested', helperPid=client.process.pid if client.process else None)
        original['close'](client)
        record('session-closed', helperPid=client.process.pid if client.process else None,
               exitCode=client.process.returncode if client.process else None)
    def observed_scan(reader, *args, **kwargs):
        if 'root' not in snapshots:
            snapshots['root'] = reader.root
            snapshots['before'] = snapshot(reader.root)
            record('fixture-before', root=reader.root, files=snapshots['before'])
        record('scan-start', root=reader.root)
        value = original['scan'](reader, *args, **kwargs)
        scans.append(value)
        record('scan-end', reports=value)
        return value
    def observed_acknowledge(reader, *args, **kwargs):
        record('acknowledge-start', report=args[0])
        value = original['acknowledge'](reader, *args, **kwargs)
        acknowledgements.append(args[0])
        record('acknowledge-end', report=args[0], files=snapshot(reader.root))
        return value
    def observed_rmtree(path, *args, **kwargs):
        if path == snapshots.get('root'):
            assert os.path.abspath(path).startswith(workspace+os.sep), 'Fixture cleanup escapes workspace'
            snapshots['after'] = snapshot(path)
            record('fixture-before-original-cleanup', root=path, files=snapshots['after'])
        value = original['rmtree'](path, *args, **kwargs)
        if path == snapshots.get('root'):
            snapshots['cleanupComplete'] = not os.path.exists(path)
            record('fixture-original-cleanup-end', removed=snapshots['cleanupComplete'])
        return value
    windows.subprocess.Popen = observed_popen
    windows.WindowsPathValidator.request, windows.WindowsPathValidator.response = observed_request, observed_response
    windows.WindowsPathValidator.close = observed_close
    Results.scan, Results.acknowledge, shutil.rmtree = observed_scan, observed_acknowledge, observed_rmtree
    def resource(name):
        mapping = {windows.HELPER_RESOURCE:'Driftkings.WindowsFiles.exe', windows.INFO_RESOURCE:'helper.json'}
        with open(os.path.join(workspace,'build/windows-files',mapping[name]),'rb') as stream: return stream.read()
    try:
        windows.initialize(resource, workspace, os.path.join(folder, 'client-cache'))
        result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([tests.UpdaterSmokeTests(TEST)]))
        record('original-test-result', successful=result.wasSuccessful(), testsRun=result.testsRun,
               failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
        assert result.wasSuccessful() and result.testsRun == 1 and not result.skipped
        assert len(acknowledgements) == 2 and len(scans) == 4
        assert scans[0][0]['status'] == 'installed' and scans[1] == []
        assert scans[2][0]['status'] == 'failed' and scans[3] == []
        assert len(processes) == 1 and responses[0] == b'READY\t1'
        assert counts['R'] == 1 and len(replacements) == 1
        assert all(value == b'OK\tV' or value == b'OK\tR' for value in responses[1:])
        assert len(responses) == counts['V'] + counts['R'] + 1
        assert replacements[0]['sourceConsumed'] and replacements[0]['sameDirectory']
        assert replacements[0]['sourceSha256'] == replacements[0]['targetAfterSha256']
        assert snapshots['cleanupComplete']
        windows.close()
        assert processes[0].returncode == 0
        output = dict(status='PASS', python=sys.version, hostPid=os.getpid(), test=TEST, originalTestUnchanged=True,
            testsRun=1, requests=counts, handshake='READY\t1', responses=responses, helperProcesses=1,
            scans=scans, acknowledgements=acknowledgements, replacements=replacements, fixture=snapshots,
            timeout=False, prematureEOF=False, functionalAdapters=[])
        with open(os.path.join(folder,'operation-completed.json'),'wb') as stream: stream.write(json_bytes(output,indent=2))
        record('operation-completed')
    except BaseException as error:
        record('operation-error', error=repr(error), stackTrace=traceback.format_exc())
        raise
    finally:
        windows.close()
        windows.subprocess.Popen = original['popen']
        windows.WindowsPathValidator.request, windows.WindowsPathValidator.response = original['request'], original['response']
        windows.WindowsPathValidator.close = original['close']
        Results.scan, Results.acknowledge, shutil.rmtree = original['scan'], original['acknowledge'], original['rmtree']
    return 0
