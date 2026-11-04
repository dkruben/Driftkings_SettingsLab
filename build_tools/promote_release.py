"""Promote an approved beta to a stable release, rebuilt from source and signed anew.

  python build_tools/promote_release.py prepare --beta <beta>      # edit release.json and VERSION; no commit
  python build_tools/promote_release.py check --beta <beta>        # read-only gate
  python build_tools/promote_release.py build --beta <beta>        # compile, sign and verify locally
  python build_tools/promote_release.py publish --beta <beta>      # preview: nothing is uploaded
  python build_tools/promote_release.py publish --beta <beta> --confirm v<stable>@<artifacts digest>

A stable differs from its beta by a commit that only changes metadata, so the approved beta commit and
the stable commit are compared rather than assumed equal. Compilation needs the game client and the
signing key is offline, so only `check` runs on GitHub; publication stays local, which also keeps the
Discord workflow firing (events from GITHUB_TOKEN do not start other workflows). Traceability is the
promotion.json release asset: the updater rejects unknown fields, so it must not enter release.json.

Approval names the stable commit and the digest of SHA256SUMS.txt, which covers every artifact and the
manifest, so the build comes first and any rebuild needs a new approval.
"""
import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.compiler import override_version, sync_release_version, version_contract
from build_tools.package_tools import sha, write_json
from build_tools.publish_release import (create_release, github_json, prepare, releases_for_tag, require_green_ci,
                                         signature_module)
from build_tools.sign_release import sign_folder
from build_tools.update_release import tag_commit
from build_tools.validate_build_data import read_json, require
from build_tools.validation_record import RECORD_FOLDER, evaluate, stable_target

STABLE_BRANCH = 'main'
GATE_WORKFLOW = 'promotion-gate.yml'
GATE_JOB = 'Environment approval'
GATE_ENVIRONMENT = 'stable-release'
PROVENANCE = 'promotion.json'
BUILD_STAMP = '.promotion-build.json'
RELEASE_DATA = 'build_data/release.json'
VOLATILE_RELEASE_FIELDS = ('version', 'channel', 'changelog')
# Paths a stable may change after its beta: none of them reaches the package. Anything else needs a new beta.
ALLOWED_PREFIXES = ('docs/', 'tests/', '.github/ISSUE_TEMPLATE/')
ALLOWED_FILES = frozenset(('README.md', 'CONTRIBUTING.md', 'SECURITY.md', RELEASE_DATA,
                           '.github/workflows/promotion-gate.yml', 'build_tools/promote_release.py',
                           'build_tools/publish_release.py', 'build_tools/sign_release.py',
                           'build_tools/update_release.py', 'build_tools/validation_record.py'))


class Context(object):
    """The repository and GitHub as seen by the checks; tests replace these calls."""
    root = ROOT

    def __init__(self):
        self.release = read_json(ROOT / RELEASE_DATA)
        self.repository = self.release['repository']
        self.version_source = self.release['version_source']

    def git(self, *args):
        return subprocess.check_output(['git'] + list(args), cwd=ROOT).decode('utf-8').strip()

    def read(self, commit, path):
        """A file exactly as committed, never as it is in the working tree."""
        return subprocess.check_output(['git', 'show', '%s:%s' % (commit, path)], cwd=ROOT).decode('utf-8')

    def is_ancestor(self, ancestor, commit):
        return subprocess.run(['git', 'merge-base', '--is-ancestor', ancestor, commit], cwd=ROOT).returncode == 0

    def query(self, path, missing_ok=False):
        return github_json(path, missing_ok)

    def tag_commit(self, tag):
        refs = self.git('ls-remote', 'origin', 'refs/tags/' + tag, 'refs/tags/%s^{}' % tag)
        return tag_commit(refs, tag) if refs else None

    def download(self, asset, target):
        with Path(target).open('wb') as stream:
            result = subprocess.run(['gh', 'api', '-H', 'Accept: application/octet-stream',
                                     'repos/%s/releases/assets/%s' % (self.repository, asset['id'])],
                                    cwd=ROOT, stdout=stream, stderr=subprocess.PIPE)
        require(result.returncode == 0, 'Could not download release asset ' + asset['name'])

    def compile(self, stable, key):
        require(key.is_file(), 'Local release signing key is missing')
        require(subprocess.run(['git', 'ls-files', '--error-unmatch', str(key)], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0,
                'The signing key is tracked by git; stop and rotate it')
        subprocess.run([sys.executable, '-B', str(ROOT / 'build_tools/compiler.py'), '--mode', 'release',
                        '--version', stable, '--channel', 'stable'], cwd=ROOT, check=True)
        folder = stable_folder(stable)
        subprocess.run([sys.executable, '-B', str(ROOT / 'build_tools/build_installer.py'), '--artifacts', str(folder),
                        '--compile', '--attach-to-release'], cwd=ROOT, check=True)
        sign_folder(folder, key)
        subprocess.run([sys.executable, '-B', str(ROOT / 'tests/run_python.py'), '--suite', 'artifacts',
                        '--wotmod', str(folder / 'driftkings.wotmod')], cwd=ROOT, check=True)
        return folder

    def create_draft(self, command, files, manifest):
        create_release(command + ['--draft'], files, manifest)

    def publish_draft(self, release):
        subprocess.run(['gh', 'api', '-X', 'PATCH', 'repos/%s/releases/%s' % (self.repository, release['id']),
                        '-F', 'draft=false', '-F', 'prerelease=false', '-f', 'make_latest=true'],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)

    def viewer(self):
        return self.query('user')['login']


def stable_folder(stable):
    config = read_json(ROOT / 'build_data/build_config.json')
    return ROOT / config['package']['release_root'] / 'stable' / stable


def record_location(beta):
    return '%s/%s-validation.md' % (RECORD_FOLDER, beta)


def artifacts_digest(folder):
    """Short identity of a build: SHA256SUMS.txt covers the report, the manifest and every artifact."""
    return sha(folder / 'SHA256SUMS.txt')[:16]


def gate_title(beta, commit, digest):
    """Must match run-name in .github/workflows/promotion-gate.yml."""
    return 'Promotion %s @ %s # %s' % (beta, commit, digest)


def write_build_stamp(folder, commit):
    """Local proof that `build` finished here, artifact suite included; never uploaded."""
    write_json(folder / BUILD_STAMP, dict(commit=commit, digest=artifacts_digest(folder),
                                          manifestSha256=sha(folder / 'release.json'), artifactSuite='passed'))


def require_build_stamp(folder, commit):
    path = folder / BUILD_STAMP
    require(path.is_file(), 'This folder did not come from `promote_release.py build`; run it first')
    expected = dict(commit=commit, digest=artifacts_digest(folder), manifestSha256=sha(folder / 'release.json'),
                    artifactSuite='passed')
    require(read_json(path) == expected, 'The build changed after `promote_release.py build`; run it again')


def check_identity(context, beta, commit):
    """The stable commit must already carry the stable version and channel."""
    stable = stable_target(beta)
    require(re.match(r'\A[0-9a-f]{40}\Z', commit), 'The stable commit must be a full SHA-1')
    release = json.loads(context.read(commit, RELEASE_DATA))
    require(release['version'] == stable and release['channel'] == 'stable',
            'release.json at %s is %s/%s, not %s/stable' % (commit[:12], release['version'], release['channel'], stable))
    source = context.read(commit, context.version_source)
    require(override_version(source, stable) == source, 'Runtime VERSION differs from ' + stable)
    return dict(beta=beta, stable=stable, tag='v' + stable, commit=commit)


def check_record(context, identity):
    text = context.read(identity['commit'], record_location(identity['beta']))
    summary = evaluate(text, identity['beta'], identity['stable'])
    summary['path'] = record_location(identity['beta'])
    summary['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return summary


def check_history(context, identity, record):
    require(context.is_ancestor(record['commit'], identity['commit']),
            'The approved commit %s is not an ancestor of the stable commit' % record['commit'][:12])
    require(context.is_ancestor(identity['commit'], 'origin/' + STABLE_BRANCH),
            'The stable commit is not on origin/%s; push it first' % STABLE_BRANCH)
    return True


def forbidden_changes(paths):
    return sorted(path for path in paths if path not in ALLOWED_FILES and not path.startswith(ALLOWED_PREFIXES))


def check_changes(context, identity, record):
    """Between the approved beta and the stable, nothing that reaches the package may change but its version."""
    approved, commit = record['commit'], identity['commit']
    paths = [path for path in context.git('diff', '--name-only', '--no-renames', approved, commit).splitlines() if path]
    code = [path for path in paths if path != context.version_source]
    blocked = forbidden_changes(code)
    require(not blocked, 'Changes after the approved beta need a new beta: ' + ', '.join(blocked[:10]))
    if context.version_source in paths:
        require(override_version(context.read(approved, context.version_source), identity['stable']) ==
                context.read(commit, context.version_source),
                'The runtime version source changes more than VERSION')
    before, after = (json.loads(context.read(item, RELEASE_DATA)) for item in (approved, commit))
    changed = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
    require(changed.issubset(VOLATILE_RELEASE_FIELDS), 'release.json changes more than version data: %s' % sorted(changed))
    return paths


def assets_by_name(release):
    names = [asset['name'] for asset in release['assets']]
    require(len(names) == len(set(names)), 'Release has duplicate asset names')
    return {asset['name']: asset for asset in release['assets']}


def summed(text):
    return {line.split('  ', 1)[1]: line.split('  ', 1)[0] for line in text.splitlines() if line}


def check_beta_release(context, identity, record):
    """Authenticate the published beta the record speaks about, from its public assets."""
    tag = 'v' + identity['beta']
    release = context.query('repos/%s/releases/tags/%s' % (context.repository, tag), True)
    require(release and not release['draft'] and release['prerelease'], '%s is not a published prerelease' % tag)
    require(context.tag_commit(tag) == record['commit'], 'Tag %s does not point to the recorded commit' % tag)
    assets = assets_by_name(release)
    names = ('release.json', 'release.json.sig', 'build-report.json', 'SHA256SUMS.txt')
    require(set(names).issubset(assets), 'Beta release is missing signed metadata')
    with tempfile.TemporaryDirectory(prefix='dk-promotion-') as temporary:
        folder = Path(temporary)
        for name in names:
            context.download(assets[name], folder / name)
        raw = (folder / 'release.json').read_bytes()
        signature = signature_module()
        require(signature.TRUSTED_KEYS, 'TRUSTED_KEYS is empty')
        signature.verify_manifest(raw, (folder / 'release.json.sig').read_bytes(), signature.TRUSTED_KEYS)
        sums = summed((folder / 'SHA256SUMS.txt').read_text(encoding='utf-8'))
        for name in ('release.json', 'build-report.json'):
            require(sums.get(name) == sha(folder / name), 'Beta checksum mismatch: ' + name)
        manifest, report = json.loads(raw.decode('utf-8')), read_json(folder / 'build-report.json')
    require(manifest['version'] == identity['beta'] and manifest['channel'] == 'beta', 'Beta manifest identity mismatch')
    require(report['git']['commit'] == record['commit'] and not report['git']['dirty'],
            'Beta build report does not come from the recorded commit')
    require(manifest['sha256'] == record['packageSha256'] == report['artifacts']['driftkings.wotmod']['sha256'],
            'The validated package is not the published beta package')
    require(manifest['gameVersion'] == record['gameVersion'], 'Record and beta target different game versions')
    return dict(manifestSha256=hashlib.sha256(raw).hexdigest(), packageSha256=manifest['sha256'],
                gameVersion=manifest['gameVersion'], inputs=report['inputs'])


def check_ci(context, identity, record):
    query = lambda path: context.query(path)
    return dict(beta=require_green_ci(context.repository, record['commit'], query),
                stable=require_green_ci(context.repository, identity['commit'], query))


def check_slot(context, identity, resume=False):
    """A stable is never replaced: its tag must be unused and it must be newer than every published stable."""
    tag, query = identity['tag'], lambda path: context.query(path)
    found = releases_for_tag(context.repository, tag, query)
    require(not any(not item['draft'] for item in found),
            '%s is already published; it is never overwritten. If an earlier run ended with an error, '
            'compare the public release with promotion.json by hand' % tag)
    require(not found or (resume and len(found) == 1), '%s already has %d draft(s)' % (tag, len(found)))
    require(context.tag_commit(tag) is None, 'Tag %s already exists on origin' % tag)
    contract = version_contract()
    current = contract.Version(identity['stable'])
    newest = [contract.Version(item['tag_name'][1:]) for item in query('repos/%s/releases?per_page=100' % context.repository)
              if not item['draft'] and not item['prerelease']]
    require(all(version < current for version in newest), 'A newer or equal stable is already published')
    return found[0] if found else True


def preflight(context, beta, commit, resume=False):
    """Run every check; each result is PASS, FAIL or NOT RUN when something it needs failed first."""
    state, results = {}, []
    checks = (
        ('identity', (), lambda: check_identity(context, beta, commit)),
        ('record', ('identity',), lambda: check_record(context, state['identity'])),
        ('history', ('identity', 'record'), lambda: check_history(context, state['identity'], state['record'])),
        ('changes', ('identity', 'record'), lambda: check_changes(context, state['identity'], state['record'])),
        ('beta', ('identity', 'record'), lambda: check_beta_release(context, state['identity'], state['record'])),
        ('ci', ('identity', 'record'), lambda: check_ci(context, state['identity'], state['record'])),
        ('slot', ('identity',), lambda: check_slot(context, state['identity'], resume)),
    )
    for name, needs, action in checks:
        if not all(item in state for item in needs):
            results.append((name, 'NOT RUN', 'requires ' + ', '.join(needs)))
            continue
        try:
            state[name] = action()
            results.append((name, 'PASS', ''))
        except (ValueError, KeyError, TypeError, OSError, AttributeError, subprocess.SubprocessError) as error:
            results.append((name, 'FAIL', str(error)))
    return state, results


def print_results(results):
    for name, result, detail in results:
        print('%-10s %-8s %s' % (name, result, detail))


def require_preflight(context, beta, commit, resume=False):
    state, results = preflight(context, beta, commit, resume)
    print_results(results)
    require(all(result == 'PASS' for _, result, _ in results), 'Promotion blocked')
    return state


def require_clean_checkout(context, commit):
    require(context.git('rev-parse', 'HEAD') == commit, 'Check out the stable commit first')
    require(not context.git('status', '--porcelain'), 'The checkout has uncommitted changes')


def compare_inputs(before, after, version_source):
    """The authoritative comparison: hashes the two builds recorded for every source they compiled."""
    changed = {name for name in set(before) | set(after) if before.get(name) != after.get(name)}
    blocked = forbidden_changes(changed - {version_source})
    require(not blocked, 'Stable build inputs differ from the approved beta: ' + ', '.join(blocked[:10]))


def verify_stable_folder(context, folder, state):
    """Integrity, signature and identity of a local stable build, using the publisher's own checks."""
    identity, beta = state['identity'], state['beta']
    command, files, report, manifest = prepare(folder)
    require(report['version'] == identity['stable'] and report['channel'] == 'stable' and
            manifest['channel'] == 'stable', 'The build is not the expected stable')
    require('--prerelease' not in command, 'A stable cannot be published as a prerelease')
    require(report['git']['commit'] == identity['commit'] and not report['git']['dirty'],
            'The build does not come from the stable commit')
    require(report['gameVersion'] == beta['gameVersion'], 'Stable and beta target different game versions')
    require(manifest['sha256'] != beta['packageSha256'], 'The stable package is the beta package; it must be rebuilt')
    require(not any('beta' in path.name.lower() for path in files), 'A stable asset carries a beta name')
    compare_inputs(beta['inputs'], report['inputs'], context.version_source)
    return command, files, report, manifest


def environment_protected(context):
    """True when GitHub enforces reviewers on the approval environment."""
    environment = context.query('repos/%s/environments/%s' % (context.repository, GATE_ENVIRONMENT), True)
    return any(rule['type'] == 'required_reviewers' for rule in (environment or {}).get('protection_rules', []))


def find_gate(context, beta, commit, digest, waive):
    """The green gate run of this exact build and who approved it in the GitHub environment."""
    data = context.query('repos/%s/actions/workflows/%s/runs?event=workflow_dispatch&status=success&per_page=100'
                         % (context.repository, GATE_WORKFLOW), True)
    runs = [run for run in (data or {}).get('workflow_runs', [])
            if run['display_title'] == gate_title(beta, commit, digest) and run['head_branch'] == STABLE_BRANCH]
    reviewers = []
    if runs:
        run = max(runs, key=lambda item: item['run_number'])
        jobs = context.query('repos/%s/actions/runs/%s/jobs' % (context.repository, run['id']))['jobs']
        if any(job['name'] == GATE_JOB and job['conclusion'] == 'success' for job in jobs):
            approvals = context.query('repos/%s/actions/runs/%s/approvals' % (context.repository, run['id']))
            reviewers = sorted({item['user']['login'] for item in approvals if item['state'] == 'approved'})
            if reviewers:
                return dict(run=run['html_url'], approvedBy=reviewers, status='approved')
    missing = 'No approved %s run for this commit and artifacts digest %s; dispatch it with request_approval'
    require(waive, missing % (GATE_WORKFLOW, digest))
    require(not environment_protected(context),
            '%s has required reviewers, so it cannot be waived. ' % GATE_ENVIRONMENT + missing % (GATE_WORKFLOW, digest))
    return dict(run=None, approvedBy=[], status='waived')


def provenance(context, state, gate, folder, promoter):
    identity, record, beta = state['identity'], state['record'], state['beta']
    signature = signature_module()
    raw, encoded = (folder / 'release.json').read_bytes(), (folder / signature.SIGNATURE_ASSET).read_bytes()
    decoded = base64.b64decode(encoded.strip())
    manifest = read_json(folder / 'release.json')
    return dict(
        schema=1,
        repository=context.repository,
        stable=dict(version=identity['stable'], tag=identity['tag'], commit=identity['commit'],
                    manifestSha256=sha(folder / 'release.json'), packageSha256=manifest['sha256'],
                    checksumsSha256=sha(folder / 'SHA256SUMS.txt'), signatureSha256=sha(folder / signature.SIGNATURE_ASSET),
                    signingKey=next(key for key in signature.TRUSTED_KEYS
                                    if signature.verify(binascii.unhexlify(key), raw, decoded))),
        beta=dict(version=identity['beta'], tag='v' + identity['beta'], commit=record['commit'],
                  manifestSha256=beta['manifestSha256'], packageSha256=beta['packageSha256']),
        changedAfterBeta=state['changes'],
        validation=dict(path=record['path'], sha256=record['sha256'], approvedBy=record['approvedBy'],
                        approvedOn=record['approvedOn'], validatedRegions=record['validatedRegions'],
                        notValidatedRegions=record['notValidatedRegions'], knownIssues=record['knownIssues']),
        ci=state['ci'],
        gate=gate,
        promotedBy=promoter)


def verify_remote_assets(context, release, files):
    """Compare what GitHub holds, byte for byte, with the verified local files; nothing extra or missing."""
    assets = assets_by_name(release)
    expected = {path.name: path for path in files}
    require(set(assets) == set(expected),
            'Draft assets differ, so it stays unpublished: %s. Review and delete the draft, then run this again'
            % sorted(set(assets) ^ set(expected)))
    with tempfile.TemporaryDirectory(prefix='dk-promotion-') as temporary:
        for name, path in expected.items():
            target = Path(temporary) / name
            require(assets[name]['size'] == path.stat().st_size, 'Draft asset size differs: ' + name)
            context.download(assets[name], target)
            require(sha(target) == sha(path), 'Draft asset digest differs: ' + name)


def find_draft(context, tag):
    found = releases_for_tag(context.repository, tag, lambda path: context.query(path))
    require(len(found) == 1 and found[0]['draft'], 'Expected exactly one draft of ' + tag)
    return found[0]


def require_published(context, release, identity, files):
    current = context.query('repos/%s/releases/%s' % (context.repository, release['id']))
    require(not current['draft'] and not current['prerelease'], '%s was not published as stable' % identity['tag'])
    require(context.tag_commit(identity['tag']) == identity['commit'], 'The published tag is not the stable commit')
    metadata = [path for path in files if path.name in ('release.json', 'release.json.sig', PROVENANCE)]
    assets = assets_by_name(current)
    with tempfile.TemporaryDirectory(prefix='dk-promotion-') as temporary:
        for path in metadata:
            target = Path(temporary) / path.name
            context.download(assets[path.name], target)
            require(sha(target) == sha(path), 'Published asset differs: ' + path.name)


def run_prepare(context, args):
    stable = stable_target(args.beta)
    require(not context.git('status', '--porcelain'), 'Commit or set aside local changes first')
    sync_release_version(ROOT, read_json(ROOT / RELEASE_DATA), stable, 'stable')
    print('release.json and VERSION now say %s/stable; nothing was committed.' % stable)
    print('Review the changelog, update README and SECURITY, commit on %s and push.' % STABLE_BRANCH)


def run_check(context, args):
    require(args.digest is None or re.match(r'\A[0-9a-f]{16}\Z', args.digest), 'Invalid artifacts digest')
    commit = context.git('rev-parse', '--verify', args.commit + '^{commit}')
    require_preflight(context, args.beta, commit)
    print('Promotion of %s from %s is allowed; nothing was changed.' % (args.beta, commit[:12]))


def run_build(context, args):
    commit = context.git('rev-parse', 'HEAD')
    require_clean_checkout(context, commit)
    state = require_preflight(context, args.beta, commit)
    folder = context.compile(state['identity']['stable'], args.key)
    require_clean_checkout(context, commit)
    verify_stable_folder(context, folder, state)
    write_build_stamp(folder, commit)
    print('Built, signed and verified %s; nothing was uploaded.' % folder)
    print('Commit %s, artifacts digest %s; request the approval with these exact values.'
          % (commit, artifacts_digest(folder)))


def run_publish(context, args):
    commit = context.git('rev-parse', 'HEAD')
    require_clean_checkout(context, commit)
    state = require_preflight(context, args.beta, commit, resume=True)
    identity = state['identity']
    folder = stable_folder(identity['stable'])
    command, files, report, manifest = verify_stable_folder(context, folder, state)
    require_build_stamp(folder, commit)
    digest = artifacts_digest(folder)
    gate = find_gate(context, args.beta, commit, digest, args.waive_environment_review)
    write_json(folder / PROVENANCE, provenance(context, state, gate, folder, context.viewer()))
    files = files + [folder / PROVENANCE]
    token = '%s@%s' % (identity['tag'], digest)
    if args.confirm is None:
        print(json.dumps(dict(command=command + ['--draft'], assets={path.name: sha(path) for path in files}, gate=gate,
                              publication='preview only'), indent=2))
        print('Pass --confirm %s to create the draft, verify it and publish it.' % token)
        return
    require(args.confirm == token, '--confirm must be exactly ' + token)
    if state['slot'] is True:
        context.create_draft(command, files, manifest)
    release = find_draft(context, identity['tag'])
    require(release['target_commitish'] == commit, 'The draft targets another commit; remove it first')
    verify_remote_assets(context, release, files)
    context.publish_draft(release)
    require_published(context, release, identity, files)
    print('Published %s from %s; origin in %s.' % (identity['tag'], commit[:12], args.beta))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    for name, action in (('prepare', run_prepare), ('check', run_check), ('build', run_build), ('publish', run_publish)):
        command = commands.add_parser(name)
        command.set_defaults(action=action)
        command.add_argument('--beta', required=True, help='Published beta being promoted, for example 1.2.3-beta.4')
        if name == 'check':
            command.add_argument('--commit', default='HEAD', help='Stable commit (default: HEAD)')
            command.add_argument('--digest', help='Artifacts digest printed by build, checked for format only')
        if name == 'build':
            command.add_argument('--key', type=Path, default=ROOT / 'release-signing.key')
        if name == 'publish':
            command.add_argument('--confirm', help='<stable tag>@<artifacts digest>; without it nothing is uploaded')
            command.add_argument('--waive-environment-review', action='store_true',
                                 help='Accept the record alone; refused when the environment has required reviewers. '
                                      'Recorded in %s' % PROVENANCE)
    args = parser.parse_args()
    try:
        args.action(Context(), args)
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, 'Promotion stopped: %s\n' % error)


if __name__ == '__main__':
    main()
