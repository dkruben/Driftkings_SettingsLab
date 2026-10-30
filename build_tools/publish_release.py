"""Preview release publication; --publish explicitly uploads a validated release."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.compiler import version_contract
from build_tools.package_tools import sha
from build_tools.modpack import verify as verify_modpack
from build_tools.validate_build_data import input_path, read_json, relative_path, require


def signature_module():
    from build_tools.sign_release import load_signature
    return load_signature()


def verify_signature(folder, signature):
    """Every published manifest must carry a signature from a trusted key; returns the asset name."""
    require(signature.TRUSTED_KEYS, 'TRUSTED_KEYS is empty in signature.py; releases cannot be published unsigned')
    path = folder / signature.SIGNATURE_ASSET
    require(path.is_file(), 'Missing %s; run build_tools/sign_release.py first' % signature.SIGNATURE_ASSET)
    try:
        signature.verify_manifest((folder / 'release.json').read_bytes(), path.read_bytes(), signature.TRUSTED_KEYS)
    except ValueError as error:
        raise ValueError('Release manifest signature is not valid for a trusted key: %s' % error)
    return signature.SIGNATURE_ASSET


def prepare(folder):
    folder = folder.resolve()
    report = read_json(folder / 'build-report.json')
    manifest = read_json(folder / 'release.json')
    release = read_json(ROOT / 'build_data/release.json')
    require(report['status'] == 'success' and report['mode'] == 'release' and report['publishable'],
            'Only completed publishable release builds can be uploaded; diagnostic builds are excluded')
    version = version_contract().Version(report['version'])
    channel = 'beta' if version.prerelease else 'stable'
    require(manifest['version'] == version.text and manifest['channel'] == channel and report['channel'] == channel,
            'Version/channel mismatch')
    require(manifest.get('schema') == 2, 'New releases must use the complete modpack updater contract')
    require(manifest['download'] == 'https://github.com/%s/releases/download/v%s/driftkings.wotmod' % (release['repository'], version.text),
            'Unexpected release download URL')
    for name, item in report['artifacts'].items():
        path = input_path(folder, name)
        require(path.stat().st_size == item['size'] and sha(path) == item['sha256'], 'Artifact changed: ' + name)
    require(sha(folder / 'driftkings.wotmod') == manifest['sha256'] and
            (folder / 'driftkings.wotmod').stat().st_size == manifest['size'], 'Release package mismatch')
    inventory = verify_modpack(folder, manifest, read_json(folder / 'modpack.json'))
    require(report.get('verification', {}).get('modpack', {}).get('status') == 'passed',
            'Missing packaged Python 2.7 modpack verification')
    required = {'driftkings.wotmod', 'release.json', 'modpack.json', 'Driftkings-defaults.zip', inventory.distribution['file']}
    required.update('dependencies/' + Path(item['path']).name for item in inventory.files if item['kind'] == 'dependency')
    require(required.issubset(report['artifacts']), 'Incomplete release artifacts')
    for item in inventory.files:
        if item['kind'] == 'dependency':
            path = input_path(folder, 'dependencies/' + Path(item['path']).name)
            require(path.stat().st_size == item['size'] and sha(path) == item['sha256'], 'Dependency differs from modpack')
    # The checksum list covers the report as well as the uploaded artifacts.
    covered = set()
    for line in (folder / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        relative_path(name)
        require(name not in covered, 'Duplicate checksum entry')
        covered.add(name)
        require(sha(input_path(folder, name)) == digest, 'Checksum mismatch: ' + name)
    require(covered == set(report['artifacts']) | {'build-report.json'}, 'Incomplete checksum inventory')
    names = set(report['artifacts']) | {'build-report.json', 'SHA256SUMS.txt'}
    names.add(verify_signature(folder, signature_module()))
    files = [folder / name for name in sorted(names)]
    require(len({path.name.lower() for path in files}) == len(files), 'Release assets have duplicate filenames')
    command = ['gh', 'release', 'create', 'v' + version.text, '--repo', release['repository'],
               '--target', report['git']['commit'] or '', '--title', release['title'] + ' ' + version.text]
    if channel == 'beta':
        command.append('--prerelease')
    return command, files, report, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path, help='Version directory produced by a release build')
    parser.add_argument('--publish', action='store_true', help='Create the GitHub release and upload assets')
    parser.add_argument('--live', action='store_true', help='Publish publicly; otherwise create a draft')
    args = parser.parse_args()
    try:
        command, files, report, manifest = prepare(args.folder)
        if not args.live:
            command.append('--draft')
        if not args.publish:
            print(json.dumps(dict(command=command, assets=[str(p) for p in files], publication='preview only'), indent=2))
            return
        require(not report['git']['dirty'], 'Build was produced from uncommitted sources; commit and rebuild first')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
        dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip()
        require(head == report['git']['commit'] and not dirty, 'Checkout differs from the built source revision')
        with tempfile.TemporaryDirectory(prefix='dk-release-') as temporary:
            notes = Path(temporary) / 'notes.md'
            notes.write_bytes(('\n'.join('- ' + text for text in manifest.get('changelog', [])) + '\n').encode('utf-8'))
            subprocess.run(command + ['--notes-file', str(notes)] + [str(p) for p in files], cwd=ROOT, check=True)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, 'Publication failed: %s\n' % error)


if __name__ == '__main__':
    main()
