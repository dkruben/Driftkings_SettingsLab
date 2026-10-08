"""Normal unittest runner with counts, module results and local archived logs."""
import argparse
from collections import Counter
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'build/windows-files-regression'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scope',choices=['windows','updater','source'],required=True)
    parser.add_argument('--output',type=Path,default=FOLDER)
    args=parser.parse_args()
    folder=args.output.resolve()
    folder.relative_to((ROOT/'build').resolve())
    folder.mkdir(parents=True,exist_ok=True)
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(ROOT))
    sys.path.insert(0,str(ROOT/'build_tools/tests'))
    pattern={'windows':'test_windows_files_v2.py','updater':'test_updater*.py','source':'test_*.py'}[args.scope]
    log=folder/(args.scope+'.log')
    events=[]
    original_popen=subprocess.Popen
    class ObservedPopen(original_popen):
        def __init__(self,argv,*pargs,**kwargs):
            executable=str(argv[0]) if isinstance(argv,(list,tuple)) else str(argv)
            event=dict(executable=executable,argv=argv,shell=kwargs.get('shell',False),parentPid=os.getpid(),
                       startUTC=datetime.now(timezone.utc).isoformat())
            if executable.lower().endswith('driftkings.windowsfiles.exe'):
                event['sha256']=hashlib.sha256(Path(executable).read_bytes()).hexdigest()
            super().__init__(argv,*pargs,**kwargs)
            event['pid']=self.pid;events.append(event)
    class Results(unittest.TextTestResult):
        def __init__(self,*a,**k):
            super().__init__(*a,**k);self.passed=[]
        def addSuccess(self,test):
            self.passed.append(test.id());super().addSuccess(test)
    subprocess.Popen=ObservedPopen
    start=datetime.now(timezone.utc)
    try:
        with log.open('w',encoding='utf8') as stream,redirect_stdout(stream),redirect_stderr(stream):
            suite=unittest.defaultTestLoader.discover(str(ROOT/'build_tools/tests'),pattern=pattern)
            result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Results,failfast=True).run(suite)
    finally: subprocess.Popen=original_popen
    report=dict(status='PASS' if result.wasSuccessful() else 'FAIL',scope=args.scope,
        startUTC=start.isoformat(),endUTC=datetime.now(timezone.utc).isoformat(),
        total=result.testsRun,passed=len(result.passed),fail=len(result.failures),error=len(result.errors),
        skip=len(result.skipped),skipped=[(test.id(),reason) for test,reason in result.skipped],
        failures=[(test.id(),detail) for test,detail in result.failures+result.errors],
        passedByModule=dict(Counter(name.split('.')[0] for name in result.passed)),processes=events,
        powershellCount=sum('powershell' in Path(e['executable']).name.lower() for e in events),
        cmdCount=sum(Path(e['executable']).name.lower()=='cmd.exe' for e in events),
        shellTrueCount=sum(e['shell'] is True for e in events))
    if report['powershellCount'] or report['cmdCount'] or report['shellTrueCount']:
        report['status']='FAIL_FORBIDDEN_PROCESS'
    (folder/(args.scope+'.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({key:report[key] for key in ('status','scope','total','passed','fail','error','skip','powershellCount','cmdCount','shellTrueCount')},indent=2))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
