# -*- coding: utf-8 -*-
"""L1 clean-source Results.scan with explicitly controlled fixture Windows calls."""
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


@command('dkreceipts', [], '', norepo=True)
def run(ui, **opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.dont_write_bytecode = True
    level = int(os.environ['DK_RECEIPT_LEVEL'])
    if level not in (1, 2): raise ValueError('Only reviewed L1/L2 are currently implemented')
    folder = os.path.abspath('build/diagnostics/receipt-chain/receipt-l%d' % level)
    root = os.path.join(folder, 'fixture')
    os.makedirs(root)
    def record(event, **values):
        values.update(event=event, timestampUTC=datetime.datetime.utcnow().isoformat() + 'Z', hostPid=os.getpid())
        with open(os.path.join(folder, 'process-events.jsonl' if level == 2 else 'events.jsonl'), 'ab') as stream:
            stream.write((json.dumps(values) + '\n').encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
    record('host-start', python=sys.version, executable=sys.executable, argv=sys.argv, cwd=os.getcwd(), level=level)
    sys.path.insert(0, os.path.abspath('source/scripts/client'))
    import Driftkings.core.updater.results as results
    from Driftkings.core.updater.manifest import Manifest
    from Driftkings.core.updater.installer import write_new
    import Driftkings.core.updater.windows_files as windows
    def package(version):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
            archive.writestr('meta.xml', '<root><id>driftkings.unified</id><version>%s</version></root>' % version)
            archive.writestr('res/scripts/client/gui/mods/mod_Driftkings.pyc', b'\x03\xf3\x0d\x0a' + b'\0' * 20)
        return output.getvalue()
    def fixture_hashes():
        hashes = {}
        for directory, unused, files in os.walk(root):
            for name in files:
                path = os.path.join(directory, name)
                with open(path, 'rb') as stream: hashes[os.path.relpath(path, root)] = hashlib.sha256(stream.read()).hexdigest()
        return hashes
    stage = os.path.join(root, 'mods/configs/Driftkings/cache/update/download-receipt')
    os.makedirs(stage)
    old, new = package('0.1.0'), package('1.0.0')
    meta = Manifest(dict(schema=1, version='1.0.0', channel='stable', gameVersion='2.4.0.2',
                        file='Driftkings.wotmod', size=len(new), sha256=hashlib.sha256(new).hexdigest(),
                        download='https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v1.0.0/Driftkings.wotmod'))
    ticket = dict(schema=1, gameVersion='2.4.0.2', version='1.0.0', size=len(new), sha256=meta.sha256,
                  installedVersion='0.1.0', installedSize=len(old), installedSha256=hashlib.sha256(old).hexdigest())
    write_new(os.path.join(stage, 'install.json'), ticket)
    write_new(os.path.join(stage, 'release.json'), meta.document())
    write_new(os.path.join(stage, 'result.json'), dict(schema=1, status='installed', helperPid=123, error=None))
    target = os.path.join(root, 'mods/2.4.0.2/Driftkings.wotmod')
    os.makedirs(os.path.dirname(target))
    with open(target, 'wb') as stream: stream.write(new)
    unicode_path = os.path.join(stage, u'path-\u00e1')
    if level == 2: os.mkdir(unicode_path)
    reader = results.Results(root, loaded_version='1.0.0')
    original_path = results.safe_path
    original_matches = reader._package_matches
    def controlled_path(path):
        absolute = os.path.abspath(path)
        if absolute != root and not absolute.startswith(root + os.sep): raise ValueError('Fixture boundary violated')
        record('controlled-windows-path', path=absolute, note='L1 fixture adapter; not native validation')
        return path
    def controlled_matches(ticket, old=False):
        record('controlled-package-validation', note='L1 known fixture; package validation deferred to L4')
        assert not old and ticket['sha256'] == hashlib.sha256(new).hexdigest()
    if level == 1: results.safe_path = controlled_path
    reader._package_matches = controlled_matches
    native_path, popen = windows.safe_path, windows.subprocess.Popen
    state = {'expectedInvalid': False, 'calls': 0}
    class StopDiagnostic(BaseException): pass
    def category(path):
        return {reader.cache: 'cache', stage: 'download-directory',
                os.path.join(stage, 'install.json'): 'ticket',
                os.path.join(stage, 'release.json'): 'manifest',
                os.path.join(stage, 'result.json'): 'result',
                os.path.join(stage, 'Driftkings.wotmod.ready'): 'ready-and-expected-missing',
                unicode_path: 'unicode'}.get(path, 'controlled-invalid')
    def observed_path(path):
        state['calls'] += 1
        record('safe-path-start', path=path, category=category(path), expectedInvalid=state['expectedInvalid'])
        try:
            value = native_path(path)
            record('safe-path-end', path=path, category=category(path), accepted=True)
            return value
        except Exception as error:
            record('safe-path-error', path=path, category=category(path), error=repr(error),
                   winerror=getattr(error, 'winerror', None), stackTrace=traceback.format_exc())
            if state['expectedInvalid'] and getattr(error, 'winerror', None) != 5: raise
            raise StopDiagnostic('Unexpected native path error: ' + repr(error))
    def observed_popen(argv, *args, **kwargs):
        record('before-child-launch', requestedExecutable=argv[0], argv=argv,
               creationflags=kwargs.get('creationflags'), expectedInvalid=state['expectedInvalid'])
        try: process = popen(argv, *args, **kwargs)
        except Exception as error:
            record('child-launch-error', requestedExecutable=argv[0], argv=argv, error=repr(error),
                   winerror=getattr(error, 'winerror', None), executableExists=os.path.isfile(argv[0]),
                   stackTrace=traceback.format_exc())
            raise StopDiagnostic('Child launch failed: ' + repr(error))
        record('child-created', requestedExecutable=argv[0], argv=argv, childPid=process.pid, parentPid=os.getpid())
        communicate, kill = process.communicate, process.kill
        child_state = {'timeout': False}
        def observed_kill(*args, **kwargs):
            child_state['timeout'] = True
            record('child-timeout', childPid=process.pid)
            return kill(*args, **kwargs)
        def observed_communicate(*args, **kwargs):
            output = communicate(*args, **kwargs)
            record('child-finished', childPid=process.pid, exitCode=process.returncode,
                   timeout=child_state['timeout'], stdout=output[0].decode('utf-8', 'replace'),
                   stderr=output[1].decode('utf-8', 'replace'))
            if child_state['timeout'] or process.returncode != 0 and not state['expectedInvalid']:
                raise StopDiagnostic('Unexpected child exit/timeout')
            return output
        process.communicate, process.kill = observed_communicate, observed_kill
        return process
    if level == 2:
        windows.safe_path, windows.subprocess.Popen = observed_path, observed_popen
    def fixture_metadata():
        return {os.path.relpath(os.path.join(directory, name), root):
                tuple(getattr(os.stat(os.path.join(directory, name)), field, None) for field in
                      ('st_size', 'st_mtime', 'st_ctime', 'st_ino', 'st_file_attributes'))
                for directory, dirs, files in os.walk(root) for name in dirs + files}
    before = fixture_hashes()
    metadata_before = fixture_metadata()
    record('fixture-created', fixturePath=root, hashes=before)
    try:
        record('scan-start')
        reports = reader.scan('2.4.0.2')
        record('scan-end', reports=reports)
        assert len(reports) == 1 and reports[0]['status'] == 'installed' and reports[0]['error'] is None
        if level == 2:
            windows.safe_path(os.path.join(stage, 'Driftkings.wotmod.ready'))
            windows.safe_path(unicode_path)
            state['expectedInvalid'] = True
            try:
                windows.safe_path(os.path.join(stage, 'invalid\x00path'))
            except (ValueError, OSError):
                record('invalid-path-rejected-as-expected')
            else: raise StopDiagnostic('Controlled invalid path accepted')
            finally: state['expectedInvalid'] = False
        assert fixture_hashes() == before, 'L1 scan must be read only'
        assert fixture_metadata() == metadata_before, 'Fixture metadata changed'
        output = dict(status='PASS', level=level, python=sys.version, hostPid=os.getpid(),
                      reports=reports, fixtureHashes=before, fixtureUnchanged=True,
                      fixtureAdapters=['results.safe_path', 'reader._package_matches'] if level == 1 else ['reader._package_matches'],
                      fixtureMetadataBefore=metadata_before, fixtureMetadataAfter=fixture_metadata(),
                      safePathCalls=state['calls'],
                      receiptAcknowledgement=False, nativeWindowsValidation=level == 2)
        with open(os.path.join(folder, 'operation-completed.json'), 'wb') as stream:
            stream.write(json.dumps(output, indent=2).encode('utf-8'))
        record('operation-completed')
    except BaseException as error:
        record('operation-error', error=repr(error), winerror=getattr(error, 'winerror', None), stackTrace=traceback.format_exc())
        raise
    finally:
        results.safe_path = original_path
        reader._package_matches = original_matches
        windows.safe_path, windows.subprocess.Popen = native_path, popen
    return 0
