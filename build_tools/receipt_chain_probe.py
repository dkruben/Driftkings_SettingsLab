"""Incremental one-shot receipt diagnostics; each level requires a human AV gate."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/diagnostics/receipt-chain'
HG = Path('C:/Users/Ruben/AppData/Local/Atlassian/SourceTree/hg_local/hg.exe')
HG_SHA = 'ac78054d2d998e22b872b4caa231009fcfff9da7793532cc8a5af8cbce4022d2'
WINDOWS_SHA = '212e2a8679d2baf9a60c4637f875dd0314329fea75e9aa25969560acfdd5df1d'


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level', type=int, choices=range(1, 7), required=True)
    args = parser.parse_args()
    # Verify trusted baseline before consuming an attempt or launching a process.
    windows = ROOT / 'source/scripts/client/Driftkings/core/updater/windows_files.py'
    if digest(HG) != HG_SHA or digest(windows) != WINDOWS_SHA:
        raise RuntimeError('ABORT: host or windows_files baseline changed')
    for number in range(1, args.level):
        previous = FOLDER / ('receipt-l%d' % number)
        result = json.loads((previous / 'result.json').read_text())
        human = json.loads((previous / 'human.json').read_text())
        if result['status'] != 'PASS' or human['result'] != 'NO_ALERT':
            raise RuntimeError('STOP: every previous level needs technical PASS and human NO_ALERT')
        if any(digest(ROOT / name) != value for name, value in result['sourceHashes'].items()):
            raise RuntimeError('ABORT: prior level source changed')
        fixture = previous / 'fixture'
        actual = {str(path.relative_to(fixture)): digest(path) for path in fixture.rglob('*') if path.is_file()}
        if actual != result['operation']['fixtureHashes']:
            raise RuntimeError('ABORT: prior level fixture changed')
    if args.level not in (1, 2):
        raise RuntimeError('Next level must be reviewed and implemented after the preceding human gate')
    folder = FOLDER / ('receipt-l%d' % args.level)
    folder.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        local = start.astimezone(ZoneInfo('Europe/Lisbon'))
    except Exception:
        local = start.astimezone(timezone(timedelta(hours=1)))
    argv = [str(HG), '--config', 'extensions.dkreceipts=build_tools/receipt_chain_hg.py', 'dkreceipts']
    sources = {path.relative_to(ROOT).as_posix(): digest(path) for path in
               (ROOT / 'source/scripts/client/Driftkings/core/updater').glob('*.py')}
    report = dict(level=args.level, runId=folder.name, startUTC=start.isoformat(), startLocal=local.isoformat(),
                  timezone='Europe/Lisbon', launcherPid=os.getpid(), launcherExecutable=sys.executable,
                  launcherPython=sys.version, argv=argv, cwd=str(ROOT), sourceHashes=sources,
                  hgSha256=digest(HG), bitdefenderResult='UNKNOWN', status='STARTING', timeout=False)
    with (folder / 'attempt.json').open('x', encoding='utf-8') as stream: json.dump(report, stream, indent=2)
    env = dict(os.environ, DK_RECEIPT_LEVEL=str(args.level))
    process = None
    try:
        with (folder / 'stdout.log').open('wb') as output, (folder / 'stderr.log').open('wb') as error:
            process = subprocess.Popen(argv, cwd=str(ROOT), env=env, stdout=output, stderr=error)
            report['hostPid'] = process.pid
            (folder / 'launch.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            report['hostExitCode'] = process.wait(timeout=60)
        report['resultFilePresent'] = (folder / 'operation-completed.json').is_file()
        if report['resultFilePresent'] and report['hostExitCode'] == 0:
            report['operation'] = json.loads((folder / 'operation-completed.json').read_text())
            report['status'] = 'PASS'
        else:
            report['status'] = 'ABNORMAL_TERMINATION'
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        report.update(status='TIMEOUT', timeout=True, hostExitCode=process.returncode)
    except Exception as error:
        report.update(status='ACCESS_DENIED' if getattr(error, 'winerror', None) == 5 else 'UNKNOWN',
                      winerror=getattr(error, 'winerror', None), error=repr(error), stackTrace=traceback.format_exc(),
                      hostExists=HG.exists(), hostSha256=digest(HG) if HG.exists() else None)
    finally:
        report['endUTC'] = datetime.now(timezone.utc).isoformat()
        report['sourceUnchanged'] = all(digest(ROOT / name) == value for name, value in sources.items())
        if not report['sourceUnchanged']: report['status'] = 'ABORT_SOURCE_CHANGED'
        events = folder / ('process-events.jsonl' if args.level == 2 else 'events.jsonl')
        report['events'] = [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
        report['childPids'] = [event['childPid'] for event in report['events'] if event['event'] == 'child-created']
        report['powershellCount'] = sum(event['event'] == 'child-created' and 'powershell' in event['requestedExecutable'].lower() for event in report['events'])
        report.setdefault('resultFilePresent', (folder / 'operation-completed.json').is_file())
        report['endLocal'] = datetime.fromisoformat(report['endUTC']).astimezone(local.tzinfo).isoformat()
        report['safePathCalls'] = sum(event['event'] == 'safe-path-start' for event in report['events'])
        for event in report['events']:
            if event.get('winerror') == 5:
                report.update(status='ACCESS_DENIED', winerror=5, failedOperation=event)
        (folder / 'analysis.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        if args.level == 1 or report['resultFilePresent']:
            (folder / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
