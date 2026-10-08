"""Consume one fresh L2-v2b attempt; stop for a human Bitdefender gate."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/diagnostics/windows-files-v2'
FOLDER = BASE/'receipt-l2-v2b'
HG = Path('C:/Users/Ruben/AppData/Local/Atlassian/SourceTree/hg_local/hg.exe')
HG_SHA = 'ac78054d2d998e22b872b4caa231009fcfff9da7793532cc8a5af8cbce4022d2'
HELPER_SHA = '8fb6ecc64c05ec1c8ddff4eaa7cfc463d24e5cbe33bd95aa6bc6f245a3a1afd0'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_template(path):
    """Compare fixture construction AST to preserved pre-edit diagnostic."""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run')
    package = next(node for node in run.body if isinstance(node, ast.FunctionDef) and node.name == 'package')
    construction, active = [], False
    for node in run.body:
        if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id == 'stage' for t in node.targets):
            active = True
        if active: construction.append(ast.dump(node, include_attributes=False))
        if (active and isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and
                isinstance(node.value.func,ast.Attribute) and node.value.func.attr == 'mkdir' and
                len(node.value.args) == 1 and isinstance(node.value.args[0],ast.Name) and node.value.args[0].id == 'unicode_path'):
            break
    if not active or len(construction) < 10: raise RuntimeError('Fixture template incomplete')
    return hashlib.sha256(('\n'.join([ast.dump(package, include_attributes=False)]+construction)).encode('utf-8')).hexdigest()


def validate_baseline():
    gate = json.loads((BASE/'gates/receipt-l2-v2-human.json').read_text())
    if gate['runId'] != 'receipt-l2-v2' or gate['result'] != 'NO_ALERT':
        raise RuntimeError('STOP: explicit NO_ALERT for previous attempt required')
    baseline = json.loads((BASE/'unicode-baseline.json').read_text())
    for name,value in baseline['functionalHashes'].items():
        if digest(ROOT/name) != value: raise RuntimeError('ABORT: functional file changed: '+name)
    old = BASE/'receipt-l2-v2'
    old_hashes = {p.relative_to(old).as_posix():digest(p) for p in old.rglob('*') if p.is_file()}
    if old_hashes != baseline['preservedPreviousAttempt']: raise RuntimeError('ABORT: old attempt changed')
    template = fixture_template(ROOT/'build_tools/windows_files_v2_hg.py')
    if template != fixture_template(BASE/'unicode-before/windows_files_v2_hg.py'):
        raise RuntimeError('ABORT: fixture semantics changed')
    return baseline, template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', required=True, choices=['receipt-l2-v2b'])
    args = parser.parse_args()
    baseline, template = validate_baseline()
    tests = json.loads((BASE/'unicode-tests/result.json').read_text())
    if tests['status'] != 'PASS' or any(digest(ROOT/name) != value for name,value in tests['testHashes'].items()):
        raise RuntimeError('Unicode tests absent/failed/stale')
    if digest(HG) != HG_SHA: raise RuntimeError('Host identity changed')
    helper = ROOT/'build/windows-files/Driftkings.WindowsFiles.exe'
    metadata = json.loads((helper.parent/'helper.json').read_text())
    if digest(helper) != HELPER_SHA or metadata['sha256'] != HELPER_SHA: raise RuntimeError('Helper identity changed')
    if FOLDER.exists(): raise RuntimeError('Attempt directory already exists; no retry/overwrite')
    FOLDER.mkdir(parents=True, exist_ok=True)
    paths = list((ROOT/'source/scripts/client/Driftkings/core/updater').glob('*.py'))
    paths += [ROOT/'source/updater/WindowsFiles.cs', ROOT/'build_tools/windows_files_v2_hg.py',
              ROOT/'build_tools/windows_files_v2_probe.py', helper, helper.parent/'helper.json',
              ROOT/'build_tools/windows_files_diagnostic_json.py', ROOT/'build_tools/build_lab.py',
              ROOT/'build_tools/build_unified.py', ROOT/'build_tools/build_windows_files.py']
    hashes = {p.relative_to(ROOT).as_posix():digest(p) for p in paths}
    argv = [str(HG), '--config', 'extensions.dkwindowsv2=build_tools/windows_files_v2_hg.py', 'dkwindowsv2']
    start = datetime.now(timezone.utc)
    report = dict(runId=args.attempt, startUTC=start.isoformat(),
        startLocal=start.astimezone(ZoneInfo('Europe/Lisbon')).isoformat(),
        launcherPid=os.getpid(), launcherExecutable=sys.executable, argv=argv, sourceHashes=hashes,
        fixtureTemplateSha256=template, previousGate='NO_ALERT', functionalHashes=baseline['functionalHashes'],
        hgSha256=HG_SHA, helperSha256=metadata['sha256'], status='STARTING', bitdefenderResult='UNKNOWN')
    with (FOLDER/'attempt.json').open('x', encoding='utf-8') as stream: json.dump(report, stream, indent=2)
    process = None
    try:
        with (FOLDER/'stdout.log').open('wb') as out, (FOLDER/'stderr.log').open('wb') as err:
            process = subprocess.Popen(argv, cwd=str(ROOT), stdout=out, stderr=err,
                                       env=dict(os.environ, DK_WINDOWS_FILES_ATTEMPT=args.attempt, PYTHONDONTWRITEBYTECODE='1'))
            report['hostPid'] = process.pid
            (FOLDER/'launch.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            report['hostExitCode'] = process.wait(timeout=55)
        completion = FOLDER/'operation-completed.json'
        report['finalReportPresent'] = completion.is_file()
        if completion.is_file(): report['operation'] = json.loads(completion.read_text())
        operation = report.get('operation', {})
        report['status'] = 'PASS' if (process.returncode == 0 and completion.is_file() and operation.get('status') == 'PASS'
            and operation.get('handshake') == 'READY\t1' and operation.get('fixtureUnchanged') is True
            and operation.get('requests', {}).get('V', 0) >= 8 and operation.get('requests', {}).get('R') == 0
            and operation.get('timeout') is False and operation.get('prematureEOF') is False) else 'ABNORMAL_TERMINATION'
    except subprocess.TimeoutExpired:
        process.kill(); process.wait()
        report.update(status='TIMEOUT', hostExitCode=process.returncode)
    except Exception as error:
        report.update(status='ERROR', error=repr(error), winerror=getattr(error, 'winerror', None))
    finally:
        end = datetime.now(timezone.utc)
        report.update(endUTC=end.isoformat(), endLocal=end.astimezone(ZoneInfo('Europe/Lisbon')).isoformat())
        report['sourceUnchanged'] = all(digest(ROOT/name) == value for name,value in hashes.items())
        events = FOLDER/'process-events.jsonl'
        report['events'] = [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
        children = [event for event in report['events'] if event['event'] == 'child-created']
        report['helperProcesses'] = len(children)
        report['powershellCount'] = sum('powershell' in Path(event['argv'][0]).name.lower() for event in children)
        report['cmdCount'] = sum(Path(event['argv'][0]).name.lower() == 'cmd.exe' for event in children)
        report['timeout'] = any(event.get('timeout') is True for event in report['events']) or report['status'] == 'TIMEOUT'
        report['prematureEOF'] = any(event.get('prematureEOF') is True for event in report['events'])
        report['handshakeResponses'] = [e['response'] for e in report['events'] if e['event'] == 'ipc-response' and e['response'] == 'READY\t1']
        report['requests'] = {operation:sum(e['event'] == 'ipc-request' and e['operation'] == operation for e in report['events']) for operation in ('V', 'R')}
        report['helperPids'] = [e['childPid'] for e in children]
        try: validate_baseline(); report['functionalBaselineUnchanged'] = True
        except Exception as error: report.update(functionalBaselineUnchanged=False, baselineError=str(error))
        if report['status'] == 'PASS' and (len(children) != 1 or len(report['handshakeResponses']) != 1 or report['timeout'] or report['prematureEOF']):
            report['status'] = 'ABORT_INCOMPLETE_PROTOCOL'
        if not report['sourceUnchanged'] or not report['functionalBaselineUnchanged'] or report['powershellCount'] or report['cmdCount']:
            report['status'] = 'ABORT'
        (FOLDER/'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key:report.get(key) for key in ('status','startLocal','endLocal','launcherPid','hostPid','hostExitCode','finalReportPresent','helperProcesses','helperPids','handshakeResponses','requests','powershellCount','cmdCount','sourceUnchanged','functionalBaselineUnchanged','timeout','prematureEOF')}, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
