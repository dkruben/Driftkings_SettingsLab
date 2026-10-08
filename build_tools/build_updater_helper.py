"""Build the owned offline installer into build/; never launch or deploy it."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def build():
    compiler = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
    if not compiler.is_file():
        raise RuntimeError('Windows .NET Framework C# compiler is required for the local installer build')
    output = ROOT / 'build/updater'
    output.mkdir(parents=True, exist_ok=True)
    binary = output / 'Driftkings.UpdateInstaller.exe'
    subprocess.check_call([str(compiler), '/nologo', '/target:exe', '/platform:anycpu', '/optimize+',
                           '/reference:System.Web.Extensions.dll', '/reference:System.IO.Compression.dll',
                           '/out:' + str(binary), str(ROOT / 'source/updater/Installer.cs')])
    data = binary.read_bytes()
    metadata = dict(schema=1, size=len(data), sha256=hashlib.sha256(data).hexdigest())
    (output / 'helper.json').write_text(json.dumps(metadata, sort_keys=True), encoding='utf-8')
    report = dict(source='source/updater/Installer.cs',
                  sourceSha256=hashlib.sha256((ROOT / 'source/updater/Installer.cs').read_bytes()).hexdigest(),
                  helperSha256=metadata['sha256'], runtime='Windows .NET Framework 4.5+')
    (output / 'build-report.json').write_text(json.dumps(report, sort_keys=True), encoding='utf-8')
    print('Owned updater helper built locally: %d bytes' % len(data))
    return binary


if __name__ == '__main__':
    build()
