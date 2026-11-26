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
from build_tools.validation_record import MAX_RECORD, RECORD_FOLDER, evaluate, stable_target

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

    def compile(self, stable, key, target):
        require(key.is_file(), 'Local release signing key is missing')
        require(subprocess.run(['git', 'ls-files', '--error-unmatch', str(key)], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0,
                'The signing key is tracked by git; stop and rotate it')
        subprocess.run([sys.executable, '-B', str(ROOT / 'build_tools/compiler.py'), '--mode', 'release',
                        '--target', target, '--version', stable, '--channel', 'stable'], cwd=ROOT, check=True)
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


ATTESTATION = '.official-build-attestation.json'
OFFICIAL_SOURCE = 'official-stable-build'
# Files the official build reported whose bytes signing rewrites (scrubbed build report and its checksum list).
SIGNING_REWRITTEN = frozenset(('build-report.json', 'SHA256SUMS.txt'))


def require_build_stamp(folder, commit):
    path = folder / BUILD_STAMP
    if not path.is_file() and (folder / ATTESTATION).is_file():
        return require_official_attestation(folder, commit)
    require(path.is_file(), 'This folder did not come from `promote_release.py build` or the official stable build; run it first')
    expected = dict(commit=commit, digest=artifacts_digest(folder), manifestSha256=sha(folder / 'release.json'),
                    artifactSuite='passed')
    require(read_json(path) == expected, 'The build changed after `promote_release.py build`; run it again')


def official_build_facts(summary, folder, commit):
    """Verify the official stable build report against the signed folder; raise ValueError on any mismatch."""
    require(summary.get('build_rc') == 0 and summary.get('installer_rc') == 0 and summary.get('artifacts_suite_rc') == 0,
            'The official build did not finish with exit code 0 at every step')
    require(summary.get('git', {}).get('commit') == commit and summary['git'].get('dirty') is False,
            'The official build report is not from the original clean artifact commit %s' % commit[:12])
    artifacts = summary.get('artifacts') or {}
    compared = []
    for name, record in sorted(artifacts.items()):
        if name in SIGNING_REWRITTEN:
            continue
        path = folder / name
        require(path.is_file() and path.stat().st_size == record['size'] and sha(path) == record['sha256'],
                'Signed artifact differs from the official build: ' + name)
        compared.append(name)
    require('driftkings.wotmod' in compared and 'release.json' in compared, 'Official build report lacks the core artifacts')
    return compared


def require_official_attestation(folder, commit):
    """Accept only an attestation that binds the official build, the artifact commit, the digest and the manifest."""
    attestation = read_json(folder / ATTESTATION)
    release = read_json(folder / 'release.json')
    expected = dict(schema=1, source=OFFICIAL_SOURCE, version=release['version'], channel=release['channel'],
                    commit=commit, digest=artifacts_digest(folder), manifestSha256=sha(folder / 'release.json'),
                    artifactSuite='passed')
    for key, value in expected.items():
        require(attestation.get(key) == value, 'Official build attestation does not match the folder: ' + key)
    require(attestation.get('summarySha256') and attestation.get('artifacts'),
            'Official build attestation is incomplete')
    for name, digest in sorted(attestation['artifacts'].items()):
        require((folder / name).is_file() and sha(folder / name) == digest,
                'Signed artifact differs from the official build attestation: ' + name)
    return attestation


def attest_official(folder, summary_path, beta, commit):
    """Write the attestation of an existing official stable build. Nothing is rebuilt or re-signed."""
    stable = stable_target(beta)
    release = read_json(folder / 'release.json')
    require(release['version'] == stable and release['channel'] == 'stable',
            'The folder is not the stable %s release' % stable)
    require(re.match(r'\A[0-9a-f]{40}\Z', commit), 'The artifact commit must be a full SHA-1')
    summary = read_json(summary_path)
    compared = official_build_facts(summary, folder, commit)
    log = summary_path.parent / 'installer-and-artifacts.log'
    require(log.is_file() and re.search(r'(?m)^OK \(', log.read_text(encoding='utf-8', errors='replace')),
            'The artifacts-suite log of the official build does not record OK')
    data = dict(schema=1, source=OFFICIAL_SOURCE, version=stable, channel='stable', commit=commit,
                digest=artifacts_digest(folder), manifestSha256=sha(folder / 'release.json'),
                artifactSuite='passed', summarySha256=sha(summary_path), logSha256=sha(log),
                artifacts={name: sha(folder / name) for name in compared}, signingRewritten=sorted(SIGNING_REWRITTEN),
                note='Evidence from the official stable build; promote_release.py build was not run.')
    write_json(folder / ATTESTATION, data)
    return data


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


# Owner-approved for the 0.1.7 release cycle only: the approved record and the CI run are read from an authorized
# descendant of the stable artifact commit on main. The stable artifact commit itself is never changed.
EVIDENCE_CYCLE = '0.1.7'
EVIDENCE_EXTRA_FILES = frozenset(('.github/workflows/python-package.yml',))


def authorized_evidence_commit(context, identity):
    """origin/main, once it descends from the stable artifact commit through allowlisted changes only."""
    cycle = getattr(context, 'evidence_cycle', EVIDENCE_CYCLE)
    require(identity['stable'] == cycle,
            'The evidence exception applies only to the %s release cycle' % cycle)
    tip = context.git('rev-parse', 'origin/' + STABLE_BRANCH)
    require(context.is_ancestor(identity['commit'], tip),
            'The stable artifact commit %s is not an ancestor of origin/%s' % (identity['commit'][:12], STABLE_BRANCH))
    paths = [path for path in context.git('diff', '--name-only', '--no-renames', identity['commit'], tip).splitlines()
             if path]
    blocked = sorted(path for path in paths if path not in EVIDENCE_EXTRA_FILES and forbidden_changes([path]))
    require(not blocked, 'Changes after the stable artifact commit are outside the evidence allowlist: '
            + ', '.join(blocked[:10]))
    return tip


def check_record(context, identity):
    evidence = authorized_evidence_commit(context, identity)
    text = context.read(evidence, record_location(identity['beta']))
    summary = evaluate(text, identity['beta'], identity['stable'])
    summary['path'] = record_location(identity['beta'])
    summary['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
    summary['evidenceCommit'] = evidence
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
    """The successful CI run is on the authorized evidence commit; it is recorded as the tested commit."""
    query = lambda path: context.query(path)
    tested = record['evidenceCommit']
    return dict(tested=tested, runs=require_green_ci(context.repository, tested, query))


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


def run_checks(state, checks):
    """Run every check; each result is PASS, FAIL or NOT RUN when something it needs failed first."""
    results = []
    for name, needs, action in checks:
        if not all(item in state for item in needs):
            results.append((name, 'NOT RUN', 'requires ' + ', '.join(needs)))
            continue
        try:
            state[name] = action()
            results.append((name, 'PASS', ''))
        except (ValueError, KeyError, TypeError, OSError, AttributeError, subprocess.SubprocessError) as error:
            results.append((name, 'FAIL', str(error)))
    return results


def preflight(context, beta, commit, resume=False):
    """Beta route: every check that needs the approved beta; see preflight_direct for the stable-only route."""
    state = {}
    checks = (
        ('identity', (), lambda: check_identity(context, beta, commit)),
        ('record', ('identity',), lambda: check_record(context, state['identity'])),
        ('history', ('identity', 'record'), lambda: check_history(context, state['identity'], state['record'])),
        ('changes', ('identity', 'record'), lambda: check_changes(context, state['identity'], state['record'])),
        ('beta', ('identity', 'record'), lambda: check_beta_release(context, state['identity'], state['record'])),
        ('ci', ('identity', 'record'), lambda: check_ci(context, state['identity'], state['record'])),
        ('slot', ('identity',), lambda: check_slot(context, state['identity'], resume)),
    )
    return state, run_checks(state, checks)


# Direct stable route: no beta exists, so nothing here asks GitHub for one. The record is an explicit file bound
# to the artifact commit and to the candidate package digest, and CI must be green on the artifact commit itself.
def direct_identity(context, stable, commit):
    require(re.match(r'\A[0-9a-f]{40}\Z', commit), 'The stable commit must be a full SHA-1')
    parsed = version_contract().Version(stable)
    require(not parsed.prerelease and not parsed.metadata and '%d.%d.%d' % parsed.release == stable,
            'The direct route promotes a stable version such as 1.2.3, not ' + stable)
    release = json.loads(context.read(commit, RELEASE_DATA))
    require(release['version'] == stable and release['channel'] == 'stable',
            'release.json at %s is %s/%s, not %s/stable' % (commit[:12], release['version'], release['channel'], stable))
    source = context.read(commit, context.version_source)
    require(override_version(source, stable) == source, 'Runtime VERSION differs from ' + stable)
    return dict(beta=None, stable=stable, tag='v' + stable, commit=commit, route='direct')


def read_record_file(path):
    require(path is not None and Path(path).is_file(), 'The direct route needs --record <validation record file>')
    require(Path(path).stat().st_size <= MAX_RECORD, 'Validation record is too large')
    return Path(path).read_text(encoding='utf-8')


def check_direct_record(text, identity):
    summary = evaluate(text, identity['stable'], identity['stable'], commit=identity['commit'])
    summary['path'] = 'explicit record'
    summary['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
    summary['evidenceCommit'] = identity['commit']
    return summary


def preflight_direct(context, stable, commit, text=None, resume=False):
    """Direct route checks. The record is checked only when given: the initial unsigned build needs none, because
    the record binds the candidate digest, which exists only after the build."""
    state = {}
    checks = [
        ('identity', (), lambda: direct_identity(context, stable, commit)),
        ('ci', ('identity',), lambda: dict(tested=commit, runs=require_green_ci(
            context.repository, commit, lambda path: context.query(path)))),
        ('slot', ('identity',), lambda: check_slot(context, state['identity'], resume)),
    ]
    if text is not None:
        checks.insert(1, ('record', ('identity',), lambda: check_direct_record(text, state['identity'])))
    return state, run_checks(state, checks)


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
    identity = state['identity']
    command, files, report, manifest = prepare(folder)
    require(report['version'] == identity['stable'] and report['channel'] == 'stable' and
            manifest['channel'] == 'stable', 'The build is not the expected stable')
    require('--prerelease' not in command, 'A stable cannot be published as a prerelease')
    require(report['git']['commit'] == identity['commit'] and not report['git']['dirty'],
            'The build does not come from the stable commit')
    require(not any('beta' in path.name.lower() for path in files), 'A stable asset carries a beta name')
    if identity.get('route') == 'direct':
        record = state.get('record')  # the binding is checked at publication, when the record exists
        if record is not None:
            require(manifest['sha256'] == record['packageSha256'],
                    'The candidate package is not the package the validation record approved')
            require(report['gameVersion'] == record['gameVersion'], 'Record and build target different game versions')
    else:
        beta = state['beta']
        require(report['gameVersion'] == beta['gameVersion'], 'Stable and beta target different game versions')
        require(manifest['sha256'] != beta['packageSha256'], 'The stable package is the beta package; it must be rebuilt')
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
    identity, record, beta = state['identity'], state['record'], state.get('beta')
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
        beta=None if identity.get('route') == 'direct' else dict(
            version=identity['beta'], tag='v' + identity['beta'], commit=record['commit'],
            manifestSha256=beta['manifestSha256'], packageSha256=beta['packageSha256']),
        changedAfterBeta=state.get('changes'),
        validation=dict(path=record['path'], sha256=record['sha256'], approvedBy=record['approvedBy'],
                        approvedOn=record['approvedOn'], validatedRegions=record['validatedRegions'],
                        **({'sourceVerifiedRegions': record['sourceVerifiedRegions']}
                           if 'sourceVerifiedRegions' in record else {}),
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


def route_label(args):
    """The name the gate and the messages use: the beta for the beta route, the stable for the direct route."""
    return args.stable if getattr(args, 'stable', None) else args.beta


def require_route_preflight(context, args, commit, resume=False, record=True):
    if getattr(args, 'stable', None):
        text = read_record_file(args.record) if record else None
        state, results = preflight_direct(context, args.stable, commit, text, resume)
        print_results(results)
        require(all(result == 'PASS' for _, result, _ in results), 'Promotion blocked')
        return state
    return require_preflight(context, args.beta, commit, resume)


def run_prepare(context, args):
    stable = args.stable or stable_target(args.beta)
    require(not context.git('status', '--porcelain'), 'Commit or set aside local changes first')
    sync_release_version(ROOT, read_json(ROOT / RELEASE_DATA), stable, 'stable')
    print('release.json and VERSION now say %s/stable; nothing was committed.' % stable)
    print('Review the changelog, update README and SECURITY, commit on %s and push.' % STABLE_BRANCH)


def run_check(context, args):
    require(args.digest is None or re.match(r'\A[0-9a-f]{16}\Z', args.digest), 'Invalid artifacts digest')
    commit = context.git('rev-parse', '--verify', args.commit + '^{commit}')
    require_route_preflight(context, args, commit)
    print('Promotion of %s from %s is allowed; nothing was changed.' % (route_label(args), commit[:12]))


def run_build(context, args):
    commit = context.git('rev-parse', 'HEAD')
    require_clean_checkout(context, commit)
    state = require_route_preflight(context, args, commit, record=False)
    folder = context.compile(state['identity']['stable'], args.key, args.target)
    require_clean_checkout(context, commit)
    verify_stable_folder(context, folder, state)
    write_build_stamp(folder, commit)
    print('Built, signed and verified %s; nothing was uploaded.' % folder)
    print('Commit %s, artifacts digest %s; request the approval with these exact values.'
          % (commit, artifacts_digest(folder)))


def run_attest_official(context, args):
    data = attest_official(args.folder, args.summary, args.beta, args.commit)
    print('Attested the official %s build of %s in %s (promote_release.py build was not run).'
          % (data['version'], data['commit'][:12], args.folder))


def run_publish(context, args):
    commit = args.commit or context.git('rev-parse', 'HEAD')
    require(not context.git('status', '--porcelain'), 'The checkout has uncommitted changes')
    state = require_route_preflight(context, args, commit, resume=True)
    identity = state['identity']
    folder = stable_folder(identity['stable'])
    command, files, report, manifest = verify_stable_folder(context, folder, state)
    if args.target:
        require_target_identity(report, args.target)
    require_build_stamp(folder, commit)
    digest = artifacts_digest(folder)
    gate = find_gate(context, route_label(args), commit, digest, args.waive_environment_review)
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
    print('Published %s from %s; route %s.' % (identity['tag'], commit[:12], route_label(args)))


def require_target_identity(report, target):
    """A build report must describe the configured target; historical reports without a target field still pass."""
    config = read_json(ROOT / 'build_data/build_config.json')
    require(target in config.get('targets', {}), 'Unknown build target: ' + target)
    if 'source_client' in report:
        expected = config['targets'][target]
        require((report['source_client'].get('realm'), report['source_client'].get('build')) ==
                (expected['realm'], expected['build']), 'The build was made for another client than ' + target)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    for name, action in (('prepare', run_prepare), ('check', run_check), ('build', run_build), ('publish', run_publish),
                         ('attest-official', run_attest_official)):
        command = commands.add_parser(name)
        command.set_defaults(action=action)
        if name == 'attest-official':
            command.add_argument('--commit', required=True, help='Original stable artifact commit')
            command.add_argument('--folder', required=True, type=Path, help='Signed stable folder')
            command.add_argument('--summary', required=True, type=Path, help='summary.json of the official stable build')
            command.add_argument('--beta', required=True, help='Published beta being promoted, for example 1.2.3-beta.4')
            continue
        route = command.add_mutually_exclusive_group(required=True)
        route.add_argument('--beta', help='Beta route: the published beta being promoted, for example 1.2.3-beta.4')
        route.add_argument('--stable', help='Direct route: the committed stable version, for example 1.2.3')
        command.add_argument('--record', type=Path,
                             help='Direct route: validation record file for the stable version and artifact commit')
        if name == 'check':
            command.add_argument('--commit', default='HEAD', help='Stable commit (default: HEAD)')
            command.add_argument('--digest', help='Artifacts digest printed by build, checked for format only')
        if name == 'build':
            command.add_argument('--key', type=Path, default=ROOT / 'release-signing.key')
            command.add_argument('--target', required=True, help='Configured build target, for example na999')
        if name == 'publish':
            command.add_argument('--commit', help='Original stable artifact commit (the tool itself is always the current checkout)')
            command.add_argument('--target', help='Configured build target the candidate must describe')
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
