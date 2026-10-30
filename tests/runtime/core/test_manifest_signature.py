# -*- coding: utf-8 -*-
import base64
import binascii
import json

from support import RuntimeTest
from support.releases import BASE, manifest

VECTORS = (  # RFC 8032 section 7.1: seed, public key, message, signature
    ('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60',
     'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a', '',
     'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b'),
    ('4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb',
     '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c', '72',
     '92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00'),
)
SEED = binascii.unhexlify(VECTORS[0][0])


class SignatureTests(RuntimeTest):
    def setUp(self):
        super(SignatureTests, self).setUp()
        self.sig = self.load('core.updater.signature')

    def test_rfc8032_vectors(self):
        for seed, public, message, signature in VECTORS:
            seed, public, message, signature = [binascii.unhexlify(x) for x in (seed, public, message, signature)]
            self.assertEqual(self.sig.public_key(seed), public)
            self.assertEqual(self.sig.sign(seed, message), signature)
            self.assertTrue(self.sig.verify(public, message, signature))

    def test_rejects_tampering_and_malformed_input(self):
        public = self.sig.public_key(SEED)
        signature = self.sig.sign(SEED, b'manifest')
        self.assertTrue(self.sig.verify(public, b'manifest', signature))
        self.assertFalse(self.sig.verify(public, b'manifest ', signature))
        flipped = bytearray(signature)
        flipped[10] ^= 1
        self.assertFalse(self.sig.verify(public, b'manifest', bytes(flipped)))
        self.assertFalse(self.sig.verify(self.sig.public_key(b'\x01' * 32), b'manifest', signature))
        for bad in (b'', signature[:-1], signature + b'0', None):
            self.assertFalse(self.sig.verify(public, b'manifest', bad))
        high_s = signature[:32] + self.sig._bytes(self.sig._int(signature[32:]) + self.sig._Q, 32)
        self.assertFalse(self.sig.verify(public, b'manifest', high_s))

    def test_verify_manifest_requires_trusted_key_and_valid_base64(self):
        key = binascii.hexlify(self.sig.public_key(SEED)).decode('ascii')
        encoded = base64.b64encode(self.sig.sign(SEED, b'{}')) + b'\n'
        self.sig.verify_manifest(b'{}', encoded, keys=(key,))
        for raw, text, keys in ((b'{ }', encoded, (key,)), (b'{}', b'!!', (key,)), (b'{}', encoded, ()),
                                (b'{}', encoded, (VECTORS[1][1],))):
            self.assertRaises(ValueError, self.sig.verify_manifest, raw, text, keys)

    def test_not_enforced_without_keys(self):
        self.assertFalse(self.sig.enforced())


class SignedCheckerTests(RuntimeTest):
    def run_signed(self, files, version='1.1.0'):
        sig = self.load('core.updater.signature')
        sig.TRUSTED_KEYS = (binascii.hexlify(sig.public_key(SEED)).decode('ascii'),)
        endpoints = self.load('core.updater.endpoints')
        Response = self.load('core.updater.transport').Response
        base = BASE + 'v' + version + '/'
        assets = [dict(name=name, browser_download_url=base + name) for name in files]
        documents = {endpoints.RELEASES: json.dumps([dict(draft=False, prerelease=False, tag_name='v' + version, assets=assets)]).encode('utf-8')}
        documents.update((base + name, body) for name, body in files.items())
        results = []

        class Transport(object):
            def request(self, url, callback, timeout, maximum):
                callback(Response(200, documents[url], url), None)

        checker = self.load('core.updater.checker').Checker(Transport())
        checker.check('1.0.0', 'stable', '2.4.1.0', lambda result, error: results.append((result, error)))
        return results[0]

    def signed(self, raw, seed=SEED):
        sig = self.load('core.updater.signature')
        return base64.b64encode(sig.sign(seed, raw))

    def test_valid_signature_is_accepted(self):
        raw = json.dumps(manifest()).encode('utf-8')
        result, error = self.run_signed({'release.json': raw, 'release.json.sig': self.signed(raw)})
        self.assertIsNone(error)
        self.assertEqual(result['latestVersion'], '1.1.0')

    def test_missing_wrong_or_stale_signature_is_rejected(self):
        raw = json.dumps(manifest()).encode('utf-8')
        other = json.dumps(manifest(data=b'evil')).encode('utf-8')
        cases = ({'release.json': raw},
                 {'release.json': raw, 'release.json.sig': self.signed(raw, b'\x02' * 32)},
                 {'release.json': other, 'release.json.sig': self.signed(raw)},
                 {'release.json': raw, 'release.json.sig': b'not base64!'})
        for files in cases:
            result, error = self.run_signed(files)
            self.assertIsNone(result)
            self.assertEqual(error, 'invalidManifest')


class DownloadPinningTests(RuntimeTest):
    def test_download_must_point_to_official_repository(self):
        Manifest = self.load('core.updater.manifest').Manifest
        Manifest(manifest())
        for url in ('https://github.com/attacker/repo/releases/download/v1.1.0/driftkings.wotmod',
                    'https://objects.githubusercontent.com/x/driftkings.wotmod',
                    'https://api.github.com/repos/x/y/driftkings.wotmod'):
            document = manifest()
            document['download'] = url
            self.assertRaises(ValueError, Manifest, document)


if __name__ == '__main__':
    import unittest
    unittest.main()
