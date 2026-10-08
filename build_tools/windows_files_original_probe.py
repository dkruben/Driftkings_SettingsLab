"""One original receipt test. A fresh marker and another human AV gate required."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo

from windows_files_v2_probe import ROOT, BASE, HG, HG_SHA, HELPER_SHA, digest, validate_baseline

FOLDER = BASE/'original-smoke-v2'
EXPECTED = {
    'source/updater/WindowsFiles.cs':'f8723f20839aa0fdfb25afc7ac7dee317af28d512087099906a154b7ce5b58f1',
    'source/scripts/client/Driftkings/core/updater/windows_files.py':'10c8a55da9ae0e4fa60b41f812dcaa03a576de7dccf593bedd8c9def60a408c2',
    'build/windows-files/Driftkings.WindowsFiles.exe':HELPER_SHA,
}


def preflight():
    baseline, unused = validate_baseline()
    gate = json.loads((BASE/'gates/receipt-l2-v2b-human.json').read_text())
    previous = json.loads((BASE/'receipt-l2-v2b/result.json').read_text())
    if gate['result'] != 'NO_ALERT' or previous['status'] != 'PASS':
        raise RuntimeError('Previous technical PASS and explicit NO_ALERT required')
    for name,value in previous['sourceHashes'].items():
        if digest(ROOT/name) != value: raise RuntimeError('L2-v2b baseline changed: '+name)
    for name,value in EXPECTED.items():
        if digest(ROOT/name) != value: raise RuntimeError('Explicit functional hash changed: '+name)
    if digest(HG) != HG_SHA: raise RuntimeError('Host identity changed')
    return baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', required=True, choices=['original-smoke-v2'])
    args = parser.parse_args()
    baseline = preflight()
    if FOLDER.exists(): raise RuntimeError('Attempt exists; no overwrite/retry permitted')
    paths = [ROOT/name for name in baseline['functionalHashes']]
    paths += [ROOT/name for name in ('build_tools/tests/test_updater_smoke.py',
        'build_tools/windows_files_original_hg.py','build_tools/windows_files_original_probe.py',
        'build_tools/windows_files_diagnostic_json.py')]
    hashes = {p.relative_to(ROOT).as_posix():digest(p) for p in paths}
    previous = BASE/'receipt-l2-v2b'
    preserved = {p.relative_to(previous).as_posix():digest(p) for p in previous.rglob('*') if p.is_file()}
    argv = [str(HG), '--config', 'extensions.dkwindowsoriginal=build_tools/windows_files_original_hg.py', 'dkwindowsoriginal']
    start = datetime.now(timezone.utc)
    report = dict(runId=args.attempt, status='STARTING', bitdefenderResult='UNKNOWN',
        startUTC=start.isoformat(), startLocal=start.astimezone(ZoneInfo('Europe/Lisbon')).isoformat(),
        launcherPid=os.getpid(), launcherParentPid=os.getppid(), launcherExecutable=sys.executable,
        launcherArgv=sys.argv, argv=argv, sourceHashes=hashes, hgSha256=HG_SHA, helperSha256=HELPER_SHA,
        previousAttemptHashes=preserved, previousGate='NO_ALERT', timeout=False, prematureEOF=False)
    FOLDER.mkdir(parents=True, exist_ok=False)
    with (FOLDER/'attempt.json').open('x',encoding='utf-8') as stream: json.dump(report,stream,indent=2)
    process = None
    try:
        with (FOLDER/'stdout.log').open('wb') as out, (FOLDER/'stderr.log').open('wb') as err:
            process = subprocess.Popen(argv, cwd=str(ROOT), stdout=out, stderr=err,
                env=dict(os.environ, DK_WINDOWS_FILES_ATTEMPT=args.attempt, PYTHONDONTWRITEBYTECODE='1'), shell=False)
            report.update(hostPid=process.pid, hostParentPid=os.getpid())
            (FOLDER/'launch.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            report['hostExitCode'] = process.wait(timeout=55)
        completion = FOLDER/'operation-completed.json'
        report['finalReportPresent'] = completion.is_file()
        if completion.is_file(): report['operation'] = json.loads(completion.read_text())
        operation = report.get('operation',{})
        report['status'] = 'PASS' if (process.returncode == 0 and completion.is_file() and
            operation.get('status') == 'PASS' and operation.get('testsRun') == 1 and
            operation.get('handshake') == 'READY\t1' and operation.get('requests',{}).get('R') == 1 and
            operation.get('fixture',{}).get('cleanupComplete') is True) else 'ABNORMAL_TERMINATION'
    except subprocess.TimeoutExpired:
        process.kill(); process.wait()
        report.update(status='TIMEOUT',timeout=True,hostExitCode=process.returncode)
    except Exception as error:
        report.update(status='ERROR',error=repr(error),winerror=getattr(error,'winerror',None))
    finally:
        end = datetime.now(timezone.utc)
        report.update(endUTC=end.isoformat(),endLocal=end.astimezone(ZoneInfo('Europe/Lisbon')).isoformat())
        report['sourceUnchanged'] = all(digest(ROOT/name) == value for name,value in hashes.items())
        actual = {p.relative_to(previous).as_posix():digest(p) for p in previous.rglob('*') if p.is_file()}
        report['previousAttemptPreserved'] = actual == preserved
        events = FOLDER/'process-events.jsonl'
        report['events'] = [json.loads(line) for line in events.read_text(encoding='utf-8').splitlines()] if events.exists() else []
        children = [e for e in report['events'] if e['event'] == 'child-created']
        report['helperPids'] = [e['childPid'] for e in children]
        report['powershellCount'] = sum('powershell' in Path(e['argv'][0]).name.lower() for e in children)
        report['cmdCount'] = sum(Path(e['argv'][0]).name.lower() == 'cmd.exe' for e in children)
        report['shellTrueCount'] = sum(e['event'] == 'before-child-launch' and e.get('shell') is True for e in report['events'])
        report['requests'] = {op:sum(e['event'] == 'ipc-request' and e['operation'] == op for e in report['events']) for op in ('V','R')}
        report['timeout'] = report['timeout'] or any(e.get('timeout') is True for e in report['events'])
        report['prematureEOF'] = any(e.get('prematureEOF') is True for e in report['events'])
        report['winerror5Count'] = sum(e.get('winerror') == 5 for e in report['events'])
        if (not report['sourceUnchanged'] or not report['previousAttemptPreserved'] or report['powershellCount'] or
                report['cmdCount'] or report['shellTrueCount'] or report['timeout'] or report['prematureEOF'] or report['winerror5Count']):
            report['status'] = 'ABORT'
        if report['status'] == 'PASS' and len(children) != 1: report['status'] = 'ABORT_INCOMPLETE_PROTOCOL'
        (FOLDER/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({key:report.get(key) for key in ('status','startLocal','endLocal','launcherPid','hostPid',
        'helperPids','requests','hostExitCode','finalReportPresent','sourceUnchanged','previousAttemptPreserved',
        'powershellCount','cmdCount','shellTrueCount','timeout','prematureEOF','winerror5Count')},indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
