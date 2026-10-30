"""Rebuild an existing release from its tagged revision using its GitHub notes; sign locally, optionally upload.

The published tag is never moved: the checkout must already be the commit the tag points to.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.compiler import select_version
from build_tools.publish_release import prepare
from build_tools.sign_release import sign_folder
from build_tools.validate_build_data import read_json, require


def changelog_lines(body):
    """Preserve notes as plain text lines within the signed manifest's limits."""
    require(isinstance(body, str) and body.strip(), 'GitHub release notes are empty')
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    require(len(lines) <= 50 and all(len(line) <= 500 for line in lines) and
            sum(len(line.encode('utf-8')) for line in lines) <= 16 * 1024,
            'Release notes exceed changelog limits (50 lines, 500 characters/line, 16 KiB); shorten the GitHub notes')
    return lines


def tag_commit(refs, tag):
    """Resolve a tag from `git ls-remote` output, preferring the peeled commit of an annotated tag."""
    found = {}
    for line in refs.splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            found[name.strip()] = digest
    commit = found.get('refs/tags/%s^{}' % tag) or found.get('refs/tags/' + tag)
    require(commit, 'Published tag %s was not found on origin' % tag)
    return commit


def require_tagged_revision(commit, head, tag):
    require(commit == head, 'Tag %s points to %s, not the checkout %s. Check out the tagged commit to rebuild '
            'its assets, or publish the changes as a new version; the tag is never moved.' % (tag, commit[:12], head[:12]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', help='Existing version; defaults to build_data/release.json')
    parser.add_argument('--key', type=Path, default=ROOT / 'release-signing.key')
    parser.add_argument('--publish', action='store_true', help='Replace existing release assets after validation')
    args = parser.parse_args()
    try:
        release = read_json(ROOT / 'build_data/release.json')
        version, channel, source = select_version(ROOT, release, args.version, 'auto')
        # Do not move a published tag or publish uncommitted code implicitly.
        require(version == source and version == release['version'],
                'Build once to synchronize release.json and source VERSION, then commit and rerun')
        require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip(),
                'Commit source changes before rebuilding a release')
        tag = 'v' + version
        remote = json.loads(subprocess.check_output(
            ['gh', 'release', 'view', tag, '--repo', release['repository'],
             '--json', 'tagName,body,isDraft,isPrerelease'], cwd=ROOT))
        require(remote['tagName'] == tag and not remote['isDraft'] and
                remote['isPrerelease'] == (channel == 'beta'), 'Release identity/channel mismatch')
        tagged = tag_commit(subprocess.check_output(
            ['git', 'ls-remote', 'origin', 'refs/tags/' + tag, 'refs/tags/%s^{}' % tag], cwd=ROOT).decode('utf-8'), tag)
        require_tagged_revision(tagged, subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(), tag)
        lines = changelog_lines(remote['body'])
        require(args.key.is_file(), 'Local release signing key is missing')
        with tempfile.TemporaryDirectory(prefix='dk-release-notes-') as temporary:
            notes = Path(temporary) / 'changelog.txt'
            notes.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            subprocess.run([sys.executable, '-B', str(ROOT / 'build_tools/compiler.py'),
                            '--mode', 'release', '--version', version, '--channel', channel,
                            '--changelog', str(notes)], cwd=ROOT, check=True)
        config = read_json(ROOT / 'build_data/build_config.json')
        folder = ROOT / config['package']['release_root'] / channel / version
        subprocess.run([sys.executable, '-B', str(ROOT / 'build_tools/build_installer.py'),
                        '--artifacts', str(folder), '--compile', '--attach-to-release'], cwd=ROOT, check=True)
        sign_folder(folder, args.key)
        _, files, report, _ = prepare(folder)
        require(not report['git']['dirty'], 'Release build is not clean')
        if args.publish:
            head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
            require(head == report['git']['commit'] and
                    not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip(),
                    'Checkout changed during the build')
            require_tagged_revision(tagged, head, tag)
            subprocess.run(['gh', 'release', 'upload', tag, '--repo', release['repository'], '--clobber'] +
                           [str(path) for path in files], cwd=ROOT, check=True)
            print('Updated %s with %d verified assets and GitHub release notes' % (tag, len(files)))
        else:
            print('Prepared and signed %s; no upload. Use --publish to update GitHub.' % folder)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, 'Release update failed: %s\n' % error)


if __name__ == '__main__':
    main()
