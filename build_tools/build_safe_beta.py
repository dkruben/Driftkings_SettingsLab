"""Phase 10 beta artifacts with exact allowlist and real protected-bytecode checks."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

from obfuscate_staging import protect, load_profile, ROOT, sha

FOLDER = ROOT / 'build/obfuscation/safe'
BETA = ROOT / 'build/beta/0.1.2-beta.1'


def checked(argv, name, env=None):
    with (FOLDER / (name + '.log')).open('wb') as stream:
        subprocess.check_call([str(item) for item in argv], cwd=str(ROOT), stdout=stream,
                              stderr=subprocess.STDOUT, env=env, timeout=120)


def validate_package(clean, package, staging, config):
    expected = {'res/scripts/client/' + name for name in config['include']}
    with zipfile.ZipFile(clean) as before, zipfile.ZipFile(package) as after:
        if after.testzip() or before.namelist() != after.namelist() or len(after.namelist()) != len(set(after.namelist())):
            raise ValueError('Package structure/CRC differs')
        changed = {name for name in before.namelist() if before.read(name) != after.read(name)}
        if changed != expected: raise ValueError('Only allowlisted modules may change in final WOTMOD')
        for name in config['include']:
            if after.read('res/scripts/client/' + name) != (staging / name).read_bytes():
                raise ValueError('Package contains unvalidated protected bytecode')
        if any(after.read(name)[:4] != b'\x03\xf3\x0d\x0a' for name in after.namelist() if name.endswith('.pyc')):
            raise ValueError('Wrong Python bytecode magic')
        entries = [name for name in after.namelist() if name.startswith('res/scripts/client/gui/mods/mod_')]
        if entries != ['res/scripts/client/gui/mods/mod_Driftkings.pyc']: raise ValueError('Entrypoint changed')
        return dict(changed=sorted(changed), entries=len(after.namelist()), sha256=sha(package),
                    size=package.stat().st_size, version=ET.fromstring(after.read('meta.xml')).findtext('version'))


def run(hg, tool, python):
    FOLDER.mkdir(parents=True, exist_ok=True)
    for pattern in ('runtime-*.json', 'marks-*.json'):
        for previous in FOLDER.glob(pattern): previous.unlink()
    BETA.mkdir(parents=True, exist_ok=True)
    for name in ('Driftkings.wotmod', 'Driftkings.wotmod.sha256', 'release.json'):
        (BETA / name).unlink(missing_ok=True)
    package = ROOT / 'build/unified/Driftkings.wotmod'
    clean = FOLDER / 'baseline.wotmod'
    shutil.copyfile(package, clean)
    report = None
    try:
        profile = ROOT / 'build_data/obfuscation.json'
        config = load_profile(profile)
        staging, report = protect(ROOT / 'build/scripts/client', FOLDER, tool, profile)
        runtime = ROOT / 'build_tools/obfuscation_runtime.py'
        marks = ROOT / 'build_tools/pjorion_poc_runtime.py'
        original = ROOT / 'source/scripts/client/Driftkings/core/marks_calculator.py'
        protected = staging / 'Driftkings/core/marks_calculator.pyc'
        checked([python, '-B', runtime, staging, FOLDER / 'runtime-python2718.json'], 'python2718')
        checked([python, '-B', marks, '--original', original, '--protected', protected,
                 '--output', FOLDER / 'marks-python2718.json'], 'marks-python2718')
        host = [hg, '--config', 'extensions.dksafe=build_tools/obfuscation_hg.py', 'dksafe']
        env = dict(os.environ)
        for key in ('DK_SAFE_PACKAGE', 'DK_SAFE_MARKS', 'DK_SMOKE_STAGING'): env.pop(key, None)
        checked(host, 'build-python', env)
        if not (FOLDER / 'runtime-build.json').is_file():
            raise RuntimeError('Build host exited without completing smoke; exit code alone is not success')
        checked(host, 'marks-build', dict(env, DK_SAFE_MARKS='1'))
        if not (FOLDER / 'marks-build.json').is_file(): raise RuntimeError('Build host did not complete Marks checks')
        checked([sys.executable, 'build_tools/build_unified.py', '--staging', staging], 'package')
        report['package'] = validate_package(clean, package, staging, config)
        if report['package']['version'] != '0.1.2-beta.1': raise ValueError('Unexpected beta version')
        checked([python, '-B', runtime, staging, FOLDER / 'runtime-python2718-package.json', '--package', package], 'python2718-package')
        checked([python, '-B', marks, '--original', original, '--protected', protected,
                 '--output', FOLDER / 'marks-python2718-package.json', '--package', package], 'marks-python2718-package')
        checked(host, 'build-python-package', dict(env, DK_SAFE_PACKAGE=str(package)))
        checked(host, 'marks-build-package', dict(env, DK_SAFE_PACKAGE=str(package), DK_SAFE_MARKS='1'))
        if not all((FOLDER / name).is_file() for name in ('runtime-build-package.json', 'marks-build-package.json')):
            raise RuntimeError('Build host did not complete final package checks')
        report['runtimeTests'] = {path.stem: json.loads(path.read_text()) for path in FOLDER.glob('runtime-*.json')}
        report['marksTests'] = {path.stem: json.loads(path.read_text()) for path in FOLDER.glob('marks-*.json')}
        report['status'] = 'passed; beta real updater test pending'
        report.update(published=False, deployed=False)
        manifest = dict(schema=1, version=report['package']['version'], channel='beta', gameVersion='2.4.0.2',
                        file='Driftkings.wotmod', size=package.stat().st_size, sha256=sha(package),
                        download='https://github.com/dkruben/Driftkings_SettingsLab/releases/download/v0.1.2-beta.1/Driftkings.wotmod',
                        changelog=['Selective PJOrion protection: Marks calculator, versioning and manifest',
                                   'WindowsFiles native backend without PowerShell',
                                   'Updater reliability improvements: verified receipts and native replacement'])
        sys.path.insert(0, str(ROOT / 'source/scripts/client'))
        from Driftkings.core.updater.manifest import Manifest
        Manifest(manifest)
        shutil.copyfile(package, BETA / 'Driftkings.wotmod')
        (BETA / 'Driftkings.wotmod.sha256').write_text(sha(package) + '  Driftkings.wotmod\n', encoding='ascii')
        (BETA / 'release.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return report
    except Exception as error:
        if report is None:
            report = json.loads((ROOT / 'build/obfuscation/report.json').read_text()) if (ROOT / 'build/obfuscation/report.json').exists() else {}
        report['status'] = 'failed'
        report.setdefault('failed', []).append(str(error))
        package.unlink(missing_ok=True)
        for name in ('Driftkings.wotmod', 'Driftkings.wotmod.sha256', 'release.json'): (BETA / name).unlink(missing_ok=True)
        raise
    finally:
        if report is not None: (ROOT / 'build/obfuscation/report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hg', default=str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Atlassian/SourceTree/hg_local/hg.exe'))
    parser.add_argument('--tool', default='F:/Programas/PJOrion')
    parser.add_argument('--python', default='F:/Python27/python.exe')
    args = parser.parse_args()
    print(json.dumps(run(args.hg, args.tool, args.python)['package'], indent=2))
