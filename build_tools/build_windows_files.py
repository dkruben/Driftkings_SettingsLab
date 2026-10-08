"""Compile owned WindowsFiles IPC helper locally; never execute or deploy it."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def build():
    compiler=Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET/Framework/v4.0.30319/csc.exe'
    folder=ROOT/'build/windows-files'
    folder.mkdir(parents=True,exist_ok=True)
    binary=folder/'Driftkings.WindowsFiles.exe'
    binary.unlink(missing_ok=True)
    subprocess.check_call([str(compiler),'/nologo','/target:exe','/platform:anycpu','/optimize+',
                           '/out:'+str(binary),str(ROOT/'source/updater/WindowsFiles.cs')])
    data=binary.read_bytes()
    metadata=dict(schema=1,size=len(data),sha256=hashlib.sha256(data).hexdigest())
    (folder/'helper.json').write_text(json.dumps(metadata,sort_keys=True),encoding='utf-8')
    (folder/'build-report.json').write_text(json.dumps(dict(sourceSha256=hashlib.sha256((ROOT/'source/updater/WindowsFiles.cs').read_bytes()).hexdigest(),helperSha256=metadata['sha256'])),encoding='utf-8')
    return binary

if __name__=='__main__': print(build())
