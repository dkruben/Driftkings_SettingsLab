# -*- coding: utf-8 -*-
"""Serialization tests only; never import functional updater or native backend."""
import json
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.abspath('build_tools'))
from windows_files_diagnostic_json import UNICODE, _to_json_unicode, json_bytes


class DiagnosticJsonTests(unittest.TestCase):
    def roundtrip(self, path):
        original = {path: {'path': path, 'items': [path, (path, 17, None, True)]}}
        wire = json_bytes(original, indent=2)
        expected = _to_json_unicode(path)
        self.assertEqual(json.loads(wire.decode('utf-8')), {
            expected: {'path': expected, 'items': [expected, [expected, 17, None, True]]}})
        self.assertIsInstance(expected, UNICODE)
        self.assertEqual(list(original.keys())[0], path)
        self.assertEqual(original[path]['path'], path)

    def test_ascii(self): self.roundtrip(b'E:\\fixture\\plain.json')
    def test_spaces(self): self.roundtrip(b'E:\\fixture spaces\\file name.json')
    def test_accents(self): self.roundtrip(u'E:\\fixture\\\u00e1\u00e9\u00ed\u00f3\u00fa.json')
    def test_portuguese_unicode(self): self.roundtrip(u'E:\\configura\u00e7\u00f5es\\a\u00e7\u00e3o.json')
    def test_mixed_separators(self): self.roundtrip(u'E:/configura\u00e7\u00f5es\\a\u00e7\u00e3o.json')
    def test_mbcs_str(self):
        encoding = 'mbcs' if os.name == 'nt' else sys.getfilesystemencoding()
        path = u'E:\\configura\u00e7\u00f5es\\a\u00e7\u00e3o.json'
        raw = path.encode(encoding)
        self.roundtrip(raw)
        self.assertEqual(_to_json_unicode(raw), path)
        if sys.version_info[0] == 2: self.assertIsInstance(raw, str)

    def test_unicode_type(self):
        path = u'E:\\fixture\\path-\u00e1'
        self.assertIs(_to_json_unicode(path), path)
        self.roundtrip(path)

    def test_original_failure_reproduced_before_fix(self):
        if sys.version_info[0] != 2: self.skipTest('Implicit mbcs key decode is Python 2 specific')
        path = u'E:\\fixture\\path-\u00e1'.encode('mbcs')
        with self.assertRaises(UnicodeDecodeError): json.dumps({path: 'value'})
        self.assertEqual(json.loads(json_bytes({path: 'value'}).decode('utf-8')), {path.decode('mbcs'): 'value'})


if __name__ == '__main__': unittest.main()
