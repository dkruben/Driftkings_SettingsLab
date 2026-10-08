"""Minimal clean-source safe_path call under the existing build Python host."""
from mercurial import registrar
import datetime
import imp
import json
import os
import sys

cmdtable = {}
command = registrar.command(cmdtable)


@command('dkfileprobe', [], '', norepo=True)
def run(ui, **opts):
    import hgdemandimport
    hgdemandimport.disable()
    sys.dont_write_bytecode = True
    folder = os.path.abspath('build/diagnostics/host-interference')
    fixture = os.path.join(folder, 'fixture')
    if not os.path.isdir(fixture): os.makedirs(fixture)
    windows = imp.load_source('clean_windows_files_probe',
                             os.path.abspath('source/scripts/client/Driftkings/core/updater/windows_files.py'))
    original = windows.subprocess.Popen
    def record(event):
        event.update(timestampUTC=datetime.datetime.utcnow().isoformat() + 'Z', hostPid=os.getpid())
        with open(os.path.join(folder, 'process-events.jsonl'), 'ab') as stream:
            stream.write((json.dumps(event) + '\n').encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
    def observed(argv, *args, **kwargs):
        record(dict(event='before-child-launch', childExecutable=argv[0], plannedArgv=argv,
                    encodedCommand='-EncodedCommand' in argv,
                    creationflags=kwargs.get('creationflags'), timeoutSeconds=10))
        process = original(argv, *args, **kwargs)
        record(dict(event='child-created', childPid=process.pid, childExecutable=argv[0], argv=argv))
        communicate, kill = process.communicate, process.kill
        state = {'timeout': False}
        def observed_kill(*args, **kwargs):
            state['timeout'] = True
            record(dict(event='child-timeout-kill-requested', childPid=process.pid))
            return kill(*args, **kwargs)
        def observed_communicate(*args, **kwargs):
            result = communicate(*args, **kwargs)
            record(dict(event='child-finished', childPid=process.pid, returnCode=process.returncode,
                        timeout=state['timeout']))
            return result
        process.kill = observed_kill
        process.communicate = observed_communicate
        return process
    windows.subprocess.Popen = observed
    try:
        record(dict(event='before-operation', operation='safe_path', path=fixture,
                    python=sys.version, executable=sys.executable, cwd=os.getcwd(), argv=sys.argv))
        windows.safe_path(fixture)
        record(dict(event='operation-completed'))
        with open(os.path.join(folder, 'operation-completed.json'), 'wb') as stream:
            stream.write(json.dumps(dict(status='completed', python=sys.version)).encode('utf-8'))
    except Exception as error:
        record(dict(event='operation-error', error=repr(error)))
        raise
    finally:
        windows.subprocess.Popen = original
    return 0
