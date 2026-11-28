"""Owner-controlled signing of a release candidate: prepare, sign and finalize.

The workflow reuses the existing tools and adds only orchestration:

  prepare   (build host)       copy the verified candidate files to the signing directory
  sign      (signing machine)  owner confirmation, then sign_release.py with the configured key
  finalize  (build host)       copy the four signed files back, then promote_release.py finalize

  python -B build_tools/sign_candidate.py prepare  --run build/runs/<run>
  python -B build_tools/sign_candidate.py sign     --candidate <signing root>/<channel>/<version>
  python -B build_tools/sign_candidate.py finalize --run build/runs/<run>

Local configuration lives outside Git in build_data/signing.local.json, or in the environment:
  {"signing_root": "<owner signing directory>", "signing_key": "<owner private-key file>"}
  DK_SIGNING_ROOT and DK_SIGNING_KEY override it. The key file is read only by `sign`, after confirmation.

Nothing here scans for keys, generates keys, signs on build completion, contacts GitHub or publishes.
Exit codes: 0 success, 2 refused (nothing changed, or a safe partial state that the message explains), 3 cancelled.
"""
import argparse
import binascii
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools import sign_release  # noqa: E402
from build_tools.compiler import version_contract  # noqa: E402
from build_tools.package_tools import sha, write_json  # noqa: E402
from build_tools.publication_state import eligible_for_signing  # noqa: E402
from build_tools.validate_build_data import read_json  # noqa: E402

LOCAL_CONFIG = ROOT / 'build_data/signing.local.json'
MANIFEST_SUFFIX = '.dk-candidate.json'
PARTIAL = '.dk-partial'
SIGNATURES = ('release.json.sig', 'SHA256SUMS.txt.sig')
SIGNING_REWRITTEN = ('build-report.json', 'SHA256SUMS.txt')
UNSIGNED_EVIDENCE = 'unsigned-candidate.json'
UNSIGNED_INVENTORY = 'unsigned-SHA256SUMS.txt'
EXIT_OK, EXIT_REFUSED, EXIT_CANCELLED = 0, 2, 3


class Refused(Exception):
    """A check failed. The message is actionable and no signing material was read."""


class Cancelled(Exception):
    """The owner did not confirm the signing operation."""


def need(condition, message):
    if not condition:
        raise Refused(message)


def settings():
    local = read_json(LOCAL_CONFIG) if LOCAL_CONFIG.is_file() else {}
    return {'signing_root': os.environ.get('DK_SIGNING_ROOT') or local.get('signing_root'),
            'signing_key': os.environ.get('DK_SIGNING_KEY') or local.get('signing_key')}


def signing_root():
    root = settings()['signing_root']
    need(root, 'Set signing_root in build_data/signing.local.json or DK_SIGNING_ROOT')
    return Path(root)


def parse_inventory(text):
    entries = {}
    for line in text.splitlines():
        digest, name = line.split('  ', 1)
        need(name not in entries, 'Duplicate inventory entry: ' + name)
        entries[name] = digest
    return entries


def write_atomic(path, data):
    temporary = Path(str(path) + PARTIAL)
    if isinstance(data, (dict, list)):
        write_json(temporary, data)
    else:
        temporary.write_bytes(data)
    os.replace(temporary, path)


def candidate_location(root, version, channel):
    return Path(root) / channel / version


def manifest_location(root, version, channel):
    return Path(root) / channel / (version + MANIFEST_SUFFIX)


def is_beta(version):
    return bool(version_contract().Version(version).prerelease)


def unsigned_candidate(run):
    """Verify the run as an unsigned, complete, successful production candidate. Read-only."""
    run = Path(run).resolve()
    output, evidence = run / 'output', run / 'evidence'
    need(output.is_dir() and evidence.is_dir(), 'The run has no output or evidence folder: ' + str(run))
    report = read_json(output / 'build-report.json')
    need(eligible_for_signing(report), 'Only a successful production release build can be signed; '
         'development, debug and CT artifacts are refused')
    need(report.get('verification_result') == 'passed', 'The build verification did not pass')
    version, channel = report['version'], report['channel']
    need(channel == ('beta' if is_beta(version) else 'stable'),
         'The channel %s does not match version %s' % (channel, version))
    for name in (UNSIGNED_EVIDENCE, UNSIGNED_INVENTORY):
        need((evidence / name).is_file(), 'Unsigned evidence is missing: ' + name)
    meta = read_json(evidence / UNSIGNED_EVIDENCE)
    need(meta.get('stage') == 'unsigned' and meta.get('artifactSuite') == 'passed',
         'The unsigned build did not pass its artifact suite')
    need(meta.get('version') == version and meta.get('channel') == channel,
         'Unsigned evidence describes another candidate')
    need(meta.get('commit') == report.get('git', {}).get('commit') and report['git'].get('dirty') is False,
         'The build report is not from a clean commit that matches the evidence')
    need(sha(evidence / UNSIGNED_INVENTORY) == meta.get('inventorySha256'), 'Unsigned inventory evidence was modified')
    inventory = parse_inventory((evidence / UNSIGNED_INVENTORY).read_text(encoding='utf-8'))
    present = {path.relative_to(output).as_posix() for path in output.iterdir() if path.is_file()}
    need(not (present & set(SIGNATURES)), 'The run output already carries signatures; prepare only unsigned candidates')
    need(present == set(inventory) | {'SHA256SUMS.txt'}, 'The run output differs from its unsigned inventory: %s'
         % sorted(present ^ (set(inventory) | {'SHA256SUMS.txt'})))
    for name, digest in inventory.items():
        need(sha(output / name) == digest, 'Modified artifact in the run output: ' + name)
    need(sha(output / 'driftkings.wotmod') == meta['wotmodSha256'], 'The WOTMOD differs from the suite-tested build')
    return dict(run=run, output=output, version=version, channel=channel, commit=meta['commit'],
                target=meta['target'], inventory=inventory, report=report, evidence=evidence)


def setup_name(report):
    names = [name for name in report['artifacts'] if name.endswith('-Setup.exe')]
    need(len(names) == 1, 'The candidate must hold exactly one Setup executable')
    return names[0]


def prepare(run, out=print):
    candidate = unsigned_candidate(run)
    root = signing_root()
    version, channel = candidate['version'], candidate['channel']
    destination = candidate_location(root, version, channel)
    manifest_path = manifest_location(root, version, channel)
    names = sorted(set(candidate['inventory']) | {'SHA256SUMS.txt'})
    expected = {name: sha(candidate['output'] / name) for name in names}
    if manifest_path.is_file():
        existing = read_json(manifest_path)
        need(existing.get('commit') == candidate['commit'] and existing.get('files') == expected,
             'A different candidate is already prepared at %s; it is never overwritten' % destination)
        need(existing.get('status') == 'prepared',
             'This candidate was already signed at %s; prepare does not copy it again' % destination)
    destination.mkdir(parents=True, exist_ok=True)
    # An interrupted earlier copy leaves only temporary files; they are removed and the copy is repeated.
    for leftover in destination.glob('*' + PARTIAL):
        leftover.unlink()
    for name in names:
        target = destination / name
        if target.exists():
            need(sha(target) == expected[name],
                 'A different file is already at %s; refusing to overwrite it. Remove the folder after checking it.'
                 % target)
            continue
        staged = destination / (name + PARTIAL)
        shutil.copyfile(candidate['output'] / name, staged)
        os.replace(staged, target)
    report = candidate['report']
    write_atomic(manifest_path, dict(
        schema=1, status='prepared', version=version, channel=channel, commit=candidate['commit'],
        target=candidate['target'], wotmodSha256=expected['driftkings.wotmod'],
        setupName=setup_name(report), setupSha256=expected[setup_name(report)],
        inventorySha256=expected['SHA256SUMS.txt'], files=expected))
    out('Prepared %s/%s at %s (%d files). Nothing was signed.' % (version, channel, destination, len(names)))
    return destination


def load_candidate(candidate):
    candidate = Path(candidate).resolve()
    manifest_path = candidate.parent / (candidate.name + MANIFEST_SUFFIX)
    need(manifest_path.is_file(), 'No candidate manifest next to %s; run prepare first' % candidate)
    manifest = read_json(manifest_path)
    return candidate, manifest_path, manifest


def verify_files(candidate, manifest):
    actual = {path.name for path in candidate.iterdir() if path.is_file()}
    need(actual == set(manifest['files']), 'The candidate files differ from the prepared set: %s'
         % sorted(actual ^ set(manifest['files'])))
    for name, digest in manifest['files'].items():
        need(sha(candidate / name) == digest, 'Modified candidate file: ' + name)


def sign(candidate, confirm=None, out=print):
    candidate, manifest_path, manifest = load_candidate(candidate)
    need(manifest.get('status') == 'prepared', 'The candidate is %s; only a prepared candidate is signed'
         % manifest.get('status'))
    verify_files(candidate, manifest)
    module = sign_release.load_signature()
    trusted = tuple(module.TRUSTED_KEYS)
    need(trusted, 'TRUSTED_KEYS is empty; nothing can be signed')
    phrase = 'SIGN %s %s %s' % (manifest['version'], manifest['channel'], manifest['wotmodSha256'][:8])
    out('Candidate:   %s/%s' % (manifest['version'], manifest['channel']))
    out('Commit:      %s' % manifest['commit'])
    out('Target:      %s' % manifest['target'])
    out('WOTMOD:      %s' % manifest['wotmodSha256'])
    out('Setup:       %s' % manifest['setupSha256'])
    out('Inventory:   %s' % manifest['inventorySha256'])
    out('Trusted public key(s): ' + ', '.join(trusted))
    out('Signing into: %s' % candidate)
    answer = confirm(phrase) if confirm else None
    if answer is not True:
        raise Cancelled('Not confirmed. Nothing was signed and the signing key was not read.')
    key = settings()['signing_key']
    need(key, 'Set signing_key in build_data/signing.local.json or DK_SIGNING_KEY on this signing machine')
    key = Path(key)
    need(key.is_file(), 'The configured signing key is not available on this machine')
    seed = sign_release.read_seed(key)
    public = binascii.hexlify(module.public_key(seed)).decode('ascii')
    need(public in trusted, 'The configured key is not a trusted production key; nothing was signed')
    sign_release.sign_folder(candidate, key, module)
    try:
        module.verify_manifest((candidate / 'release.json').read_bytes(),
                               (candidate / 'release.json.sig').read_bytes(), trusted)
        module.verify_manifest((candidate / 'SHA256SUMS.txt').read_bytes(),
                               (candidate / 'SHA256SUMS.txt.sig').read_bytes(), trusted)
    except ValueError as error:
        for name in SIGNATURES:
            (candidate / name).unlink(missing_ok=True)
        raise Refused('Signature verification failed; the signature files were removed: %s' % error)
    manifest['status'] = 'signed'
    manifest['files'] = {path.name: sha(path) for path in candidate.iterdir()
                         if path.is_file() and path.name != manifest_path.name}
    write_atomic(manifest_path, manifest)
    out('Signed %s/%s; both signatures verify against the trusted production key.' % (manifest['version'],
                                                                                     manifest['channel']))
    return candidate


def finalize(run, out=print):
    run = Path(run).resolve()
    evidence = run / 'evidence'
    output = run / 'output'
    meta = read_json(evidence / UNSIGNED_EVIDENCE)
    inventory = parse_inventory((evidence / UNSIGNED_INVENTORY).read_text(encoding='utf-8'))
    version, channel = meta['version'], meta['channel']
    root = signing_root()
    candidate = candidate_location(root, version, channel)
    manifest_path = manifest_location(root, version, channel)
    need(manifest_path.is_file(), 'No candidate manifest for %s/%s in the signing directory' % (version, channel))
    manifest = read_json(manifest_path)
    need(manifest.get('status') == 'signed', 'The candidate is not signed yet (status %s)' % manifest.get('status'))
    need(manifest['commit'] == meta['commit'] and manifest['target'] == meta['target']
         and manifest['version'] == version and manifest['channel'] == channel,
         'The returned candidate does not match this run (commit, target, version or channel)')
    for name, digest in inventory.items():
        if name not in SIGNING_REWRITTEN:
            need(sha(candidate / name) == digest, 'Immutable artifact differs from the unsigned build: ' + name)
    module = sign_release.load_signature()
    trusted = tuple(module.TRUSTED_KEYS)
    try:
        module.verify_manifest((candidate / 'release.json').read_bytes(),
                               (candidate / 'release.json.sig').read_bytes(), trusted)
        module.verify_manifest((candidate / 'SHA256SUMS.txt').read_bytes(),
                               (candidate / 'SHA256SUMS.txt.sig').read_bytes(), trusted)
    except (OSError, ValueError) as error:
        raise Refused('The returned signatures do not verify against the trusted keys: %s' % error)
    returned = list(SIGNATURES) + list(SIGNING_REWRITTEN)
    staged = []
    try:
        for name in returned:
            source, target = candidate / name, output / name
            if target.is_file() and sha(target) == sha(source):
                continue
            if name in SIGNATURES:
                need(not target.exists(), 'A different %s is already in the run output; refusing to replace it' % name)
            temporary = output / (name + PARTIAL)
            shutil.copyfile(source, temporary)
            staged.append((temporary, target))
        for temporary, target in staged:
            os.replace(temporary, target)
    except BaseException:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
        raise
    out('Returned %d signed files to %s. Running the existing finalization.' % (len(returned), output))
    route = ['--stable', version] if channel == 'stable' else ['--beta', version]
    return subprocess.run([sys.executable, '-B', str(ROOT / 'build_tools/promote_release.py'), 'finalize']
                          + route + ['--commit', meta['commit'], '--target', meta['target'], '--folder', str(output)],
                          cwd=ROOT).returncode


def run_cli(argv, confirm=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_cmd = commands.add_parser('prepare')
    prepare_cmd.add_argument('--run', required=True, type=Path)
    sign_cmd = commands.add_parser('sign')
    sign_cmd.add_argument('--candidate', required=True, type=Path)
    finalize_cmd = commands.add_parser('finalize')
    finalize_cmd.add_argument('--run', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            prepare(args.run)
            return EXIT_OK
        if args.command == 'sign':
            sign(args.candidate, confirm=confirm or (lambda phrase: input(
                'Type exactly "%s" to sign with the configured key: ' % phrase).strip() == phrase))
            return EXIT_OK
        return finalize(args.run)
    except Cancelled as error:
        print('Cancelled: ' + str(error), file=sys.stderr)
        return EXIT_CANCELLED
    except (Refused, OSError, ValueError, KeyError, SystemExit) as error:
        print('Refused: %s' % error, file=sys.stderr)
        return EXIT_REFUSED


if __name__ == '__main__':
    sys.exit(run_cli(sys.argv[1:]))
