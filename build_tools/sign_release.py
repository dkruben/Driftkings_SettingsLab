"""Sign a release manifest with an offline Ed25519 key (free; no certificate authority involved).

  python build_tools/sign_release.py --generate release-signing.key   # once; keep the file OFFLINE
  python build_tools/sign_release.py <version-folder> --key release-signing.key

--generate prints the public key to paste into TRUSTED_KEYS in core/updater/signature.py.
Signing writes <version-folder>/release.json.sig, which must be uploaded with the other release assets.
"""
import argparse
import base64
import binascii
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from build_tools.publication_state import require_signable  # noqa: E402
MODULE = ROOT / 'mod/res/scripts/client/driftkings/core/updater/signature.py'
# Machine-specific fields written by the compiler (paths on the build host). Without scrubbing them the published
# report would carry local paths and the publisher would refuse it.
LOCAL_REPORT_FIELDS = ('tools', 'logs', 'workspace', 'output', 'evidence', 'wotmod', 'canonical')
INVENTORY_SIGNATURE = 'SHA256SUMS.txt.sig'


def load_signature():
    spec = importlib.util.spec_from_file_location('driftkings_manifest_signature', str(MODULE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_seed(path):
    seed = binascii.unhexlify(Path(path).read_text(encoding='ascii').strip())
    if len(seed) != 32:
        raise SystemExit('Key file must contain 64 hex characters')
    return seed


def scrub_report(folder):
    """Keep machine paths out of the published report; build/runs retains the complete local report."""
    folder = Path(folder)
    path = folder / 'build-report.json'
    if not path.is_file():
        return
    report = json.loads(path.read_text(encoding='utf-8'))
    if not any(field in report for field in LOCAL_REPORT_FIELDS):
        return
    for field in LOCAL_REPORT_FIELDS:
        report.pop(field, None)
    path.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    names = sorted(set(report['artifacts']) | {path.name})
    lines = ['%s  %s\n' % (hashlib.sha256((folder / name).read_bytes()).hexdigest(), name) for name in names]
    (folder / 'SHA256SUMS.txt').write_bytes(''.join(lines).encode('utf-8'))


def sign_folder(folder, key_file, module=None):
    module = module or load_signature()
    report_path = Path(folder) / 'build-report.json'
    if not report_path.is_file():
        raise SystemExit('Missing build-report.json; only a production release build can be signed')
    require_signable(json.loads(report_path.read_text(encoding='utf-8')))
    seed = read_seed(key_file)
    scrub_report(folder)
    raw = (Path(folder) / 'release.json').read_bytes()
    signature = module.sign(seed, raw)
    public = module.public_key(seed)
    if not module.verify(public, raw, signature):
        raise SystemExit('Self-check failed; signature not written')
    output = Path(folder) / module.SIGNATURE_ASSET
    output.write_bytes(base64.b64encode(signature) + b'\n')
    # Detached inventory signature: covers the checksum list, which lists every artifact except the signature files,
    # so no signature covers itself and nothing is circular.
    if (Path(folder) / 'SHA256SUMS.txt').is_file():
        inventory = (Path(folder) / 'SHA256SUMS.txt').read_bytes()
        inventory_signature = module.sign(seed, inventory)
        if not module.verify(public, inventory, inventory_signature):
            raise SystemExit('Self-check failed; inventory signature not written')
        (Path(folder) / INVENTORY_SIGNATURE).write_bytes(base64.b64encode(inventory_signature) + b'\n')
    return output, binascii.hexlify(public).decode('ascii')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folder', nargs='?', type=Path, help='Version directory containing release.json')
    parser.add_argument('--key', type=Path, help='File with the private seed (64 hex characters)')
    parser.add_argument('--generate', type=Path, metavar='KEYFILE',
                        help='Create a new private key file and print the public key')
    args = parser.parse_args()
    module = load_signature()
    if args.generate:
        if args.generate.exists():
            raise SystemExit('Refusing to overwrite ' + str(args.generate))
        seed = os.urandom(32)
        descriptor = os.open(str(args.generate), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(binascii.hexlify(seed).decode('ascii') + '\n')
        print('Private key written to %s. Keep it offline and back it up.' % args.generate)
        print('Public key for TRUSTED_KEYS: ' + binascii.hexlify(module.public_key(seed)).decode('ascii'))
        return 0
    if not args.folder or not args.key:
        parser.error('folder and --key are required')
    output, public = sign_folder(args.folder, args.key, module)
    print('Wrote %s (public key %s)' % (output, public))
    return 0


if __name__ == '__main__':
    sys.exit(main())
