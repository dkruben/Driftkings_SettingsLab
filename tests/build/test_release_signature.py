import binascii
from pathlib import Path
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.publish_release import verify_signature
from build_tools.sign_release import load_signature, sign_folder

SEED = bytes(range(32))


class ReleaseSignatureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        (self.folder / 'release.json').write_bytes(b'{"version": "1.0.0"}\n')
        (self.folder / 'release.key').write_text(binascii.hexlify(SEED).decode('ascii'))
        module = load_signature()
        self.signature = types.SimpleNamespace(
            SIGNATURE_ASSET=module.SIGNATURE_ASSET, verify_manifest=module.verify_manifest,
            TRUSTED_KEYS=(binascii.hexlify(module.public_key(SEED)).decode('ascii'),))

    def sign(self):
        sign_folder(self.folder, self.folder / 'release.key')

    def test_accepts_a_manifest_signed_by_a_trusted_key(self):
        self.sign()
        self.assertEqual(verify_signature(self.folder, self.signature), 'release.json.sig')

    def test_refuses_unsigned_releases(self):
        with self.assertRaisesRegex(ValueError, 'Missing release.json.sig'):
            verify_signature(self.folder, self.signature)

    def test_refuses_publication_without_trusted_keys(self):
        self.sign()
        self.signature.TRUSTED_KEYS = ()
        with self.assertRaisesRegex(ValueError, 'TRUSTED_KEYS is empty'):
            verify_signature(self.folder, self.signature)

    def test_refuses_a_manifest_changed_after_signing(self):
        self.sign()
        (self.folder / 'release.json').write_bytes(b'{"version": "1.0.1"}\n')
        with self.assertRaisesRegex(ValueError, 'not valid for a trusted key'):
            verify_signature(self.folder, self.signature)

    def test_refuses_a_signature_from_another_key(self):
        self.sign()
        self.signature.TRUSTED_KEYS = ('00' * 32,)
        with self.assertRaisesRegex(ValueError, 'not valid for a trusted key'):
            verify_signature(self.folder, self.signature)


if __name__ == '__main__':
    unittest.main()
