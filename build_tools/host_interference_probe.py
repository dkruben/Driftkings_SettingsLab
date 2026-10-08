"""Single authorized clean-source windows_files reproduction; no AV changes."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/diagnostics/host-interference'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-once', action='store_true', required=True)
    parser.add_argument('--hg', type=Path, default=Path(os.environ.get('LOCALAPPDATA', '')) / 'Atlassian/SourceTree/hg_local/hg.exe')
    args = parser.parse_args()
    FOLDER.mkdir(parents=True, exist_ok=True)
    fixture = FOLDER / 'fixture'
    fixture.mkdir(exist_ok=True)
    fixture.resolve().relative_to(ROOT.resolve())
    if fixture.is_symlink() or fixture.is_junction(): raise ValueError('Diagnostic fixture cannot be a reparse path')
    source = ROOT / 'source/scripts/client/Driftkings/core/updater/windows_files.py'
    argv = [str(args.hg.resolve()), '--config',
            'extensions.dkfileprobe=build_tools/host_interference_hg.py', 'dkfileprobe']
    start = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        local = start.astimezone(ZoneInfo('Europe/Lisbon'))
    except Exception:
        # Diagnostic date supplied by the client: 8 October 2026, Lisbon UTC+1.
        local = start.astimezone(timezone(timedelta(hours=1)))
    report = dict(timestampUTC=start.isoformat(), localStartTime=local.isoformat(), localTimezone='Europe/Lisbon', parentPid=os.getpid(),
                  hostPythonVersion=sys.version, hostPythonExecutable=sys.executable,
                  launcherArgv=[sys.executable] + sys.argv, sourcePath=str(source),
                  fixturePath=str(fixture), fixtureMetadata=dict(exists=True, directory=True,
                      fileAttributes=fixture.stat().st_file_attributes, contents=sorted(p.name for p in fixture.iterdir())),
                  argv=argv, cwd=str(ROOT), operation='windows_files.safe_path',
                  sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(), pjOrion=False,
                  antivirusChanged=False, status='STARTING', timeout=False)
    # Never rerun accidentally after an antivirus termination or partial result.
    with (FOLDER / 'attempt.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    process = None
    try:
        with (FOLDER / 'stdout.log').open('wb') as output, (FOLDER / 'stderr.log').open('wb') as error:
            process = subprocess.Popen(argv, cwd=str(ROOT), stdout=output, stderr=error)
            report['hostPid'] = process.pid
            (FOLDER / 'launch.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            report['exitCode'] = process.wait(timeout=45)
        report['completed'] = (FOLDER / 'operation-completed.json').is_file()
        report['status'] = 'COMPLETED' if report['completed'] and report['exitCode'] == 0 else 'UNKNOWN'
        if report['exitCode'] < 0 or report['exitCode'] >= 0xC0000000: report['status'] = 'CRASHED'
    except subprocess.TimeoutExpired:
        process.kill()  # Only the diagnostic child created above.
        process.wait()
        report.update(status='TIMEOUT', timeout=True, exitCode=process.returncode)
    except Exception as error:
        report.update(status='UNKNOWN', error=str(error))
    finally:
        report['finishedUTC'] = datetime.now(timezone.utc).isoformat()
        report['sourceUnchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == report['sourceSha256']
        (FOLDER / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'COMPLETED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
