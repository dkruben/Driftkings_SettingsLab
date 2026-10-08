"""Inspect the local debug package; never publish/deploy or change source."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'build/windows-files-regression'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline=json.loads((FOLDER/'baseline.json').read_text())
    changes={name:dict(before=value,after=digest(ROOT/name)) for name,value in baseline['functionalHashes'].items() if digest(ROOT/name)!=value}
    allowed={'build/windows-files/Driftkings.WindowsFiles.exe','build/windows-files/helper.json','build/windows-files/build-report.json'}
    assert set(changes).issubset(allowed),changes
    package=ROOT/'build/unified/Driftkings.wotmod'
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        names=archive.namelist();assert len(names)==len(set(names))
        meta=ET.fromstring(archive.read('meta.xml'))
        assert meta.findtext('id')=='driftkings.unified' and meta.findtext('version')=='0.1.2-beta.1'
        entry='res/scripts/client/gui/mods/mod_Driftkings.pyc'
        assert [n for n in names if n.startswith('res/scripts/client/gui/mods/mod_')]==[entry]
        pycs=[n for n in names if n.endswith('.pyc')]
        assert all(archive.read(n)[:4]==b'\x03\xf3\x0d\x0a' for n in pycs)
        assert not any(n.endswith('.py') for n in names)
        assert not any(n.lower().endswith(('.ps1','.cmd','.bat')) or 'powershell' in n.lower() for n in names)
        helpers={}
        for kind,directory,name,source in [('windows','windows-files','Driftkings.WindowsFiles.exe','WindowsFiles.cs'),('installer','updater','Driftkings.UpdateInstaller.exe','Installer.cs')]:
            prefix='res/gui/Driftkings/'+directory+'/'
            data=archive.read(prefix+name);info=json.loads(archive.read(prefix+'helper.json'))
            actual=hashlib.sha256(data).hexdigest();assert info==dict(schema=1,size=len(data),sha256=actual)
            assert actual==digest(ROOT/'build'/directory/name)
            build=json.loads((ROOT/'build'/directory/'build-report.json').read_text())
            assert build['helperSha256']==actual and build['sourceSha256']==digest(ROOT/'source/updater'/source)
            helpers[kind]=dict(sha256=actual,size=len(data),matchesLocalBuild=True)
        bytecode=archive.read('res/scripts/client/Driftkings/core/updater/windows_files.pyc')
        assert b'-EncodedCommand' not in bytecode and b'powershell.exe' not in bytecode.lower() and b'cmd.exe' not in bytecode.lower()
        swf_hash=hashlib.sha256(archive.read('res/gui/flash/DriftkingsBattle.swf')).hexdigest()
        assert swf_hash==baseline['resHashes'][str(Path('res/flash/battle/DriftkingsBattle.swf'))]
        assets=[n for n in names if 'gameface' in n.lower()];assert assets
        release_unchanged=digest(ROOT/'build/release/Driftkings.wotmod')==baseline['resHashes'][str(Path('build/release/Driftkings.wotmod'))]
        assert release_unchanged
        report=dict(status='PASS',package=str(package),sha256=digest(package),entries=len(names),components=len(json.loads((ROOT/'build/unified/components.json').read_text())['modules']),
            version=meta.findtext('version'),entryPoint=entry,pycEntries=len(pycs),python27Magic=True,CRC='PASS',helpers=helpers,gamefaceAssets=len(assets),swfPreserved=True,
            shellResources=0,runtimeOldMechanism=False,functionalBaselineChanges=changes,releaseUnchanged=release_unchanged)
    (FOLDER/'package-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
