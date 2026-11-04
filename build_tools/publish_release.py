"""Preview release publication; --publish explicitly uploads a validated release."""
import argparse
import json
from pathlib import Path
import re
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


CI_WORKFLOW = 'python-package.yml'


def signature_module():
    from build_tools.sign_release import load_signature
    return load_signature()


def github_json(path, missing_ok=False):
    """Read one GitHub API document through the authenticated gh client."""
    result = subprocess.run(['gh', 'api', path], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        detail = result.stderr.decode('utf-8', 'replace').strip()
        if missing_ok and 'HTTP 404' in detail:
            return None
        raise ValueError('GitHub query failed for %s; check `gh auth status` and repository permissions: %s'
                         % (path, detail[-300:]))
    return json.loads(result.stdout.decode('utf-8'))


def require_green_ci(repository, commit, query=github_json):
    """The newest push run of the validation workflow must have passed on every branch that built the commit."""
    runs = query('repos/%s/actions/workflows/%s/runs?head_sha=%s&event=push&per_page=50'
                 % (repository, CI_WORKFLOW, commit))['workflow_runs']
    newest = {}
    for run in runs:
        if run['head_sha'] == commit and run['head_repository']['full_name'] == repository:
            branch = run['head_branch']
            if branch not in newest or run['run_number'] > newest[branch]['run_number']:
                newest[branch] = run
    require(newest, 'No %s run on a push of %s; push it and wait for GitHub Actions' % (CI_WORKFLOW, commit[:12]))
    for branch, run in sorted(newest.items()):
        require(run['status'] == 'completed' and run['conclusion'] == 'success',
                'GitHub Actions did not pass for %s on %s: %s/%s (%s)' % (commit[:12], branch, run['status'],
                                                                          run['conclusion'], run['html_url']))
    return [run['html_url'] for _, run in sorted(newest.items())]


def releases_for_tag(repository, tag, query=github_json):
    """Published and draft releases of a tag; a draft has no git tag, so only the full list shows it."""
    found, page = [], 1
    while True:
        items = query('repos/%s/releases?per_page=100&page=%d' % (repository, page))
        found.extend(item for item in items if item['tag_name'] == tag)
        if len(items) < 100:
            return found
        page += 1


def require_unpublished(repository, tag, query=github_json):
    """Refuse a second release, published or draft, for the same tag."""
    found = releases_for_tag(repository, tag, query)
    require(not found, '%s already has %d release(s) on GitHub (%s); review or remove them first'
            % (tag, len(found), ', '.join('draft' if item['draft'] else 'published' for item in found)))
    refs = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/tags/' + tag], cwd=ROOT).strip()
    require(not refs, 'Tag %s already exists on origin' % tag)


def create_release(command, files, manifest):
    """Create the GitHub release with notes taken from the signed manifest changelog."""
    with tempfile.TemporaryDirectory(prefix='dk-release-') as temporary:
        notes = Path(temporary) / 'notes.md'
        notes.write_bytes(('\n'.join('- ' + text for text in manifest.get('changelog', [])) + '\n').encode('utf-8'))
        subprocess.run(command + ['--notes-file', str(notes)] + [str(p) for p in files], cwd=ROOT, check=True)


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


def absolute_paths(value):
    """Keys and values of a report that look like a path on the build machine."""
    if isinstance(value, dict):
        return [item for pair in value.items() for part in pair for item in absolute_paths(part)]
    if isinstance(value, list):
        return [item for part in value for item in absolute_paths(part)]
    return [value] if isinstance(value, str) and re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|\A[\\/]', value) else []


def prepare(folder):
    folder = folder.resolve()
    report = read_json(folder / 'build-report.json')
    manifest = read_json(folder / 'release.json')
    release = read_json(ROOT / 'build_data/release.json')
    require(report['status'] == 'success' and report['mode'] == 'release' and report['publishable'],
            'Only completed publishable release builds can be uploaded; diagnostic builds are excluded')
    require(not absolute_paths(report), 'The build report carries local paths; run build_tools/sign_release.py')
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
    required = {'driftkings.wotmod', 'release.json', 'modpack.json', 'Driftkings-defaults.zip',
                inventory.distribution['file'], 'Driftkings-%s-WoT-%s-Setup.exe' % (version.text, manifest['gameVersion'])}
    required.update('dependencies/' + Path(item['path']).name for item in inventory.files
                    if item['kind'] == 'dependency')
    require(required.issubset(report['artifacts']), 'Incomplete release artifacts')
    for item in inventory.files:
        if item['kind'] == 'dependency':
            path = input_path(folder, 'dependencies/' + Path(item['path']).name)
            require(path.stat().st_size == item['size'] and sha(path) == item['sha256'],
                    'Dependency differs from modpack')
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
            print(json.dumps(dict(command=command, assets=[str(p) for p in files], publication='preview only'),
                             indent=2))
            return
        require(not report['git']['dirty'], 'Build was produced from uncommitted sources; commit and rebuild first')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
        dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip()
        require(head == report['git']['commit'] and not dirty, 'Checkout differs from the built source revision')
        require(manifest['channel'] != 'stable',
                'Stable releases are published through build_tools/promote_release.py, from an approved beta')
        repository = read_json(ROOT / 'build_data/release.json')['repository']
        require_green_ci(repository, head)
        require_unpublished(repository, 'v' + manifest['version'])
        create_release(command, files, manifest)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, 'Publication failed: %s\n' % error)


if __name__ == '__main__':
    main()
