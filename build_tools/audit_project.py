"""Read-only checks of the unified package and its component inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile
import build_unified
import localize_configs

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=('packages', 'all'))
    parser.add_argument('--python27', default=os.environ.get('DK_PYTHON27', r'F:\Python27\python.exe'))
    args = parser.parse_args()
    report = {'version': build_unified.package_version(), 'issues': [], 'components': []}
    issues = report['issues']
    for folder in ('res', 'build_data'):
        for path in (ROOT/folder).rglob('*.json'):
            try:
                json.loads(path.read_text(encoding='utf-8-sig'))
            except (ValueError, OSError) as error:
                issues.append('%s: %s' % (path, error))
    count, errors = localize_configs.check_catalogs()
    report['catalogs'] = count
    issues.extend(errors)
    inputs = {}
    for path in sorted((ROOT/'build_data/components').glob('*.json')):
        try:
            config = json.loads(path.read_text(encoding='utf-8-sig'))
            if not config.get('enabled'):
                continue
            report['components'].append(path.stem)
            for target, source in build_unified.manifest_files(config, ROOT):
                if '..' in Path(target).parts or Path(target).is_absolute():
                    raise ValueError('Unsafe package destination: ' + target)
                if target == 'LICENSE':
                    target = 'licenses/' + path.stem + '.txt'
                inputs[target] = source
        except (ValueError, OSError) as error:
            issues.append('%s: %s' % (path, error))
    try:
        with zipfile.ZipFile(ROOT/'build/unified/Driftkings.wotmod') as archive:
            if archive.testzip() is not None:
                issues.append('Invalid package CRC')
            names = archive.namelist()
            build_unified.validate_dependency_resources({name: archive.read(name) for name in names if not name.endswith('/')}, ROOT/'res/wotmods')
            report['package_entries'] = len(names)
            if ET.fromstring(archive.read('meta.xml')).findtext('version') != report['version']:
                issues.append('Package version differs from source; rebuild')
            if [n for n in names if n.startswith(build_unified.PREFIX + 'mod_')] != [build_unified.PREFIX + 'mod_Driftkings.pyc']:
                issues.append('Expected one game entry point')
            for name in names:
                if name.endswith('.pyc') and archive.read(name)[:4] != b'\x03\xf3\x0d\x0a':
                    issues.append('Not Python 2.7 bytecode: ' + name)
            for name, source in inputs.items():
                if name not in names or archive.read(name) != source.read_bytes():
                    issues.append('Missing or stale packaged input: ' + name)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        issues.append(str(error))
    if args.check == 'all':
        code = "import ast,os; files=[os.path.join(r,n) for r,d,ns in os.walk('source/scripts/client') for n in ns if n.endswith('.py')]; [ast.parse(open(p,'rb').read(),p) for p in files]; print(len(files))"
        try:
            result = subprocess.run([args.python27, '-B', '-c', code], cwd=str(ROOT), capture_output=True, text=True, check=True)
            report['parsed_python_sources'] = int(result.stdout.strip())
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            issues.append('Python 2.7 syntax check failed: ' + str(error))
        manifest = json.loads((ROOT/'flash_source/shared/swc/manifest.json').read_text())
        for library in manifest['libraries']:
            path = ROOT/'flash_source/shared/swc'/library['name']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest().lower() != library['sha256'].lower():
                issues.append('SWC mismatch: ' + library['name'])
    output = ROOT/'audit_mods/project_inventory.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Driftkings %s: %d component definitions, %d issues' % (report['version'], len(report['components']), len(issues)))
    for issue in issues:
        print(issue)
    return int(bool(args.check and issues))


if __name__ == '__main__':
    raise SystemExit(main())
