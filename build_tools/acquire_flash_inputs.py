# -*- coding: utf-8 -*-
"""Acquire the Flash library inputs of one realm from an installed World of Tanks client.

The tool reads the client packages named by a pinned manifest, extracts only the resources the manifest
lists, verifies each one against its pinned SHA-256, and writes the verified files to a Git-ignored cache
under build/. It never writes into the client, never downloads anything and never publishes what it extracts.

Rules enforced:
- The client is read-only: packages and version.xml are opened for reading only.
- The client identity (game version, build, revision, realm) must equal the manifest identity.
- Every resource must match its pinned SHA-256. All verification happens before anything is written, so a
  failure leaves no new file behind.
- Files that are not listed by the manifest are never accepted, and they are never deleted.
- A cached file that no longer matches its pin is moved aside as a quarantine file, then re-acquired.
- Interrupted writes (".partial-*" files written by this tool) are removed at the start of each run.
- Only realms in SUPPORTED_REALMS are accepted. RU, PT_RU and LESTA are excluded.
- The cache root must be inside the build directory, which is Git-ignored.

Usage (run from the repository root):
    python -B build_tools/acquire_flash_inputs.py --realm NA --build 999 --client <client-root>
    python -B build_tools/acquire_flash_inputs.py --realm NA --build 999 --check-cache
Add --install-tree to place verified files where the Flash build reads them (only absent or identical files).
"""
import argparse
import contextlib
import datetime
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / 'build'
SWC_DIR = ROOT / 'flash_source' / 'shared' / 'swc'
SCHEMA = 1
TOOL = 'acquire_flash_inputs'
SUPPORTED_REALMS = ('NA', 'EU', 'ASIA', 'CN', 'CT')
EXCLUDED_REALMS = ('RU', 'PT_RU', 'LESTA')
REQUIRED_KEYS = ('game_version', 'realm', 'build', 'revision', 'libraries')
REQUIRED_LIBRARY_KEYS = ('name', 'sha256', 'package', 'resource')
NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*\.swc$')
PACKAGE_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*\.pkg$')
SHA_RE = re.compile(r'^[0-9a-f]{64}$')
DIGITS_RE = re.compile(r'^[0-9]+$')
VERSION_RE = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')
SIDE_PREFIXES = ('.partial-', '.quarantine-')


class AcquisitionError(Exception):
    """A rejected input. The message is safe to print and contains no absolute paths."""


def fail(message):
    raise AcquisitionError(message)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(str(path), 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def relative(path):
    """Repository-relative name for reports, so that no developer-specific absolute path is recorded."""
    path = Path(path)
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def safe_resource(value):
    if not isinstance(value, str) or not value:
        fail('resource must be a non-empty string')
    if '\\' in value or value.startswith('/') or re.match(r'^[A-Za-z]:', value):
        fail('resource is not a relative POSIX path: %r' % value)
    parts = PurePosixPath(value).parts
    if any(part in ('', '.', '..') for part in parts):
        fail('resource escapes its package: %r' % value)
    if parts[0] != 'gui' or not value.endswith('.swc'):
        fail('resource must be a gui/ .swc entry: %r' % value)
    return '/'.join(parts)


def load_manifest(path):
    """Parse and validate a pinned manifest. Returns the identity and the parsed library list."""
    data = Path(path).read_bytes()
    try:
        document = json.loads(data.decode('utf-8-sig'))
    except (UnicodeDecodeError, ValueError) as error:
        fail('manifest is not UTF-8 JSON: %s' % error)
    if not isinstance(document, dict):
        fail('manifest root must be an object')
    for key in REQUIRED_KEYS:
        if key not in document:
            fail('manifest lacks "%s"' % key)
    realm = document['realm']
    if realm in EXCLUDED_REALMS:
        fail('realm %s is excluded from acquisition' % realm)
    if realm not in SUPPORTED_REALMS:
        fail('unsupported realm in manifest: %r' % (realm,))
    for key in ('build', 'revision'):
        if not isinstance(document[key], str) or not DIGITS_RE.match(document[key]):
            fail('manifest "%s" must be a string of digits' % key)
    if not isinstance(document['game_version'], str) or not VERSION_RE.match(document['game_version']):
        fail('manifest game_version must look like 2.4.2.0')
    libraries = document['libraries']
    if not isinstance(libraries, list) or not libraries:
        fail('manifest lists no libraries')
    parsed, names = [], set()
    for index, item in enumerate(libraries):
        if not isinstance(item, dict):
            fail('library %d is not an object' % index)
        for key in REQUIRED_LIBRARY_KEYS:
            if key not in item:
                fail('library %d lacks "%s" (client pins are required for acquisition)' % (index, key))
        name, sha, package = item['name'], item['sha256'], item['package']
        if not isinstance(name, str) or not NAME_RE.match(name):
            fail('library %d has an unsafe name: %r' % (index, name))
        if name in names:
            fail('duplicate library name: %s' % name)
        names.add(name)
        if not isinstance(sha, str) or not SHA_RE.match(sha):
            fail('library %s has a malformed sha256' % name)
        if not isinstance(package, str) or not PACKAGE_RE.match(package):
            fail('library %s has an unsafe package name: %r' % (name, package))
        parsed.append({'name': name, 'sha256': sha, 'package': package, 'resource': safe_resource(item['resource'])})
    return {
        'path': relative(path), 'sha256': sha256_bytes(data), 'game_version': document['game_version'],
        'realm': realm, 'build': document['build'], 'revision': document['revision'], 'libraries': parsed,
    }


def read_client_identity(client_root):
    """Read version.xml of the installed client (read-only) and return its identity."""
    version = Path(client_root) / 'version.xml'
    if not version.is_file():
        fail('client has no version.xml')
    text = version.read_bytes().decode('utf-8', 'replace')
    found = re.search(r'<version>\s*v\.([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\s*#([0-9]+)\s*</version>', text)
    client = re.search(r'<client>\s*([0-9]+)\s*</client>', text)
    realm = re.search(r'<realm>\s*([A-Z_]+)\s*</realm>', text)
    if not (found and client and realm):
        fail('version.xml is not a recognised client version file')
    return {'game_version': found.group(1), 'build': found.group(2), 'revision': client.group(1),
            'realm': realm.group(1)}


def check_identity(manifest, identity):
    for key in ('game_version', 'build', 'revision', 'realm'):
        if identity[key] != manifest[key]:
            fail('client %s is %s but the manifest pins %s' % (key, identity[key], manifest[key]))


def package_file(client_root, package):
    base = (Path(client_root) / 'res' / 'packages').resolve()
    target = (base / package).resolve()
    if target.parent != base:
        fail('package path escapes the client package folder')
    if not target.is_file():
        fail('missing client package: %s' % package)
    return target


def safe_cache_root(cache_root):
    base = BUILD_DIR.resolve()
    root = Path(cache_root)
    root = (root if root.is_absolute() else ROOT / root).resolve()
    if root != base and base not in root.parents:
        fail('the cache must be inside the git-ignored build directory')
    return root


def is_side_file(name):
    return name.startswith(SIDE_PREFIXES)


def cache_key(manifest):
    return '%s-%s-%s' % (manifest['realm'].lower(), manifest['build'], manifest['revision'])


def write_atomic(path, data):
    temporary = path.with_name('.partial-%d-%s' % (os.getpid(), path.name))
    with open(str(temporary), 'wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(temporary), str(path))


def acquire(manifest_path, cache_root, client_root=None, realm=None, build=None, install_tree=False):
    """Run one acquisition. Returns a JSON-serialisable report; raises nothing for rejected inputs."""
    report = {'schema': SCHEMA, 'tool': TOOL, 'status': 'failed', 'errors': [], 'libraries': [],
              'client': None, 'cache': None,
              'started': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}
    cache_dir = None
    try:
        manifest = load_manifest(manifest_path)
        report['manifest'] = {'path': manifest['path'], 'sha256': manifest['sha256'],
                              'realm': manifest['realm'], 'build': manifest['build'],
                              'revision': manifest['revision'], 'game_version': manifest['game_version']}
        if realm is not None and realm != manifest['realm']:
            fail('requested realm %s differs from the manifest realm %s' % (realm, manifest['realm']))
        if build is not None and build != manifest['build']:
            fail('requested build %s differs from the manifest build %s' % (build, manifest['build']))
        cache_dir = safe_cache_root(cache_root) / cache_key(manifest)
        libraries = cache_dir / 'libs'
        libraries.mkdir(parents=True, exist_ok=True)
        report['cache'] = relative(cache_dir)
        expected = dict((item['name'], item) for item in manifest['libraries'])

        for leftover in libraries.iterdir():
            if leftover.is_file() and leftover.name.startswith('.partial-'):
                leftover.unlink()  # interrupted write from an earlier run of this tool; never a recovery copy
        unexpected = sorted(item.name for item in libraries.iterdir()
                            if item.is_file() and item.name not in expected and not is_side_file(item.name))
        if unexpected:
            fail('unexpected files in the cache (kept, not deleted): %s' % ', '.join(unexpected))

        states, pending = {}, []
        for item in manifest['libraries']:
            path = libraries / item['name']
            if path.is_file():
                digest = sha256_file(path)
                if digest == item['sha256']:
                    states[item['name']] = 'cache-hit'
                    continue
                quarantine = libraries / ('.quarantine-%s-%s' % (digest[:16], item['name']))
                os.replace(str(path), str(quarantine))
                states[item['name']] = 'quarantined-and-reacquired'
            else:
                states[item['name']] = 'extracted'
            pending.append(item)

        if client_root is not None:
            identity = read_client_identity(client_root)
            check_identity(manifest, identity)
            report['client'] = {'game_version': identity['game_version'], 'build': identity['build'],
                                'revision': identity['revision'], 'realm': identity['realm'], 'packages': {}}
        if pending and client_root is None:
            fail('cache incomplete and no client given; missing: %s' % ', '.join(i['name'] for i in pending))

        extracted = {}
        with contextlib.ExitStack() as stack:
            archives = {}
            for item in pending:
                if item['package'] not in archives:
                    package = package_file(client_root, item['package'])
                    archive = zipfile.ZipFile(str(package), 'r')  # read-only
                    stack.callback(archive.close)
                    archives[item['package']] = archive
                    report['client']['packages'][item['package']] = {
                        'size': package.stat().st_size, 'sha256': sha256_file(package)}
                try:
                    info = archives[item['package']].getinfo(item['resource'])
                except KeyError:
                    fail('missing resource %s in %s' % (item['resource'], item['package']))
                data = archives[item['package']].read(info)
                digest = sha256_bytes(data)
                if digest != item['sha256']:
                    report['libraries'].append({'name': item['name'], 'status': 'hash-mismatch',
                                                'expected_sha256': item['sha256'], 'actual_sha256': digest})
                    fail('hash mismatch for %s: expected %s, got %s' % (item['name'], item['sha256'], digest))
                extracted[item['name']] = data

        for item in pending:
            write_atomic(libraries / item['name'], extracted[item['name']])
        for item in manifest['libraries']:
            digest = sha256_file(libraries / item['name'])
            if digest != item['sha256']:
                fail('read-back hash mismatch for %s' % item['name'])
            entry = {'name': item['name'], 'package': item['package'], 'resource': item['resource'],
                     'status': states[item['name']], 'expected_sha256': item['sha256'], 'actual_sha256': digest,
                     'bytes': (libraries / item['name']).stat().st_size, 'install': None}
            report['libraries'].append(entry)

        if install_tree:
            install_verified(manifest, libraries, report)
        report['status'] = 'ok'
    except AcquisitionError as error:
        report['errors'].append(str(error))
    finally:
        report['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        if cache_dir is not None:
            write_report(cache_dir, report)
    return report


def write_report(cache_dir, report):
    """Machine-readable record next to the cache files. It is rewritten on every run."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / 'acquisition-report.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def install_verified(manifest, libraries, report):
    """Place verified cache files where the Flash build reads them. Never overwrites a differing file."""
    destination = Path(SWC_DIR)
    names = [item['name'] for item in manifest['libraries']]
    for name in names:
        existing = destination / name
        if existing.exists():
            if sha256_file(existing) != sha256_file(libraries / name):
                fail('%s exists with different bytes; refusing to overwrite' % relative(existing))
    for item in report['libraries']:
        if 'name' not in item:
            continue
        existing = destination / item['name']
        if existing.exists():
            item['install'] = 'already-present-identical'
        else:
            destination.mkdir(parents=True, exist_ok=True)
            write_atomic(existing, (libraries / item['name']).read_bytes())
            item['install'] = 'installed'


def check_cache(manifest_path, cache_root):
    """Offline check: every manifest entry is present in the cache and matches its pin."""
    report = {'schema': SCHEMA, 'tool': TOOL, 'mode': 'check-cache', 'status': 'failed', 'errors': []}
    try:
        manifest = load_manifest(manifest_path)
        libraries = safe_cache_root(cache_root) / cache_key(manifest) / 'libs'
        for item in manifest['libraries']:
            path = libraries / item['name']
            if not path.is_file():
                fail('cache lacks %s' % item['name'])
            if sha256_file(path) != item['sha256']:
                fail('cache file %s does not match its pin' % item['name'])
        report['status'] = 'ok'
    except AcquisitionError as error:
        report['errors'].append(str(error))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--realm', required=True, help='NA, EU, ASIA, CN or CT')
    parser.add_argument('--build', required=True, help='client build number, for example 999')
    parser.add_argument('--client', help='installed client root (folder with version.xml and res/packages)')
    parser.add_argument('--manifest', help='pinned manifest (default: flash_source/shared/swc/manifest.<realm><build>.json)')
    parser.add_argument('--cache-root', default='build/cache/flash_inputs', help='must stay inside build/')
    parser.add_argument('--install-tree', action='store_true', help='also place verified files in flash_source/shared/swc')
    parser.add_argument('--check-cache', action='store_true', help='verify the cache offline; needs no client')
    args = parser.parse_args(argv)
    if args.realm in EXCLUDED_REALMS:
        print('acquisition rejected: realm %s is excluded' % args.realm)
        return 2
    manifest_path = Path(args.manifest) if args.manifest else SWC_DIR / ('manifest.%s%s.json' % (args.realm.lower(), args.build))
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    if args.check_cache:
        report = check_cache(manifest_path, args.cache_root)
    else:
        report = acquire(manifest_path, args.cache_root, client_root=args.client, realm=args.realm,
                         build=args.build, install_tree=args.install_tree)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
