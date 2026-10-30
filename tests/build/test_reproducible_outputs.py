from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.package_tools import normalize_swf_compile_date, validate_swf


def tag(code, body):
    return struct.pack('<H', (code << 6) | len(body)) + body


def product_info(compile_date):
    # ProductId, Edition, Major, Minor, BuildLow, BuildHigh, CompileDate (milliseconds).
    return tag(41, struct.pack('<IIBBIIQ', 3, 6, 4, 6, 0, 0, compile_date))


def swf(tags, compressed=False):
    rect = b'\x08\x00'  # Nbits = 1, every coordinate zero.
    body = rect + struct.pack('<HH', 30 << 8, 1) + b''.join(tags) + tag(0, b'')
    raw = b'FWS' + bytes([14]) + struct.pack('<I', 8 + len(body)) + body
    return raw[:3].replace(b'F', b'C') + raw[3:8] + zlib.compress(raw[8:]) if compressed else raw


def compile_date(raw):
    expanded = raw if raw[:3] == b'FWS' else raw[:8] + zlib.decompress(raw[8:])
    index = expanded.index(struct.pack('<H', (41 << 6) | 26))
    return struct.unpack('<Q', expanded[index + 2 + 18:index + 2 + 26])[0]


class SwfCompileDateTests(unittest.TestCase):
    def test_compile_date_is_replaced_by_the_source_epoch(self):
        for compressed in (False, True):
            first = normalize_swf_compile_date(swf([tag(9, b'\x00\x00\x00'), product_info(111)], compressed), 1793318400)
            second = normalize_swf_compile_date(swf([tag(9, b'\x00\x00\x00'), product_info(222)], compressed), 1793318400)
            self.assertEqual(first, second)
            self.assertEqual(compile_date(first), 1793318400 * 1000)
            self.assertEqual(first[:3], b'CWS' if compressed else b'FWS')
            validate_swf(first)

    def test_movies_without_product_info_are_unchanged(self):
        for compressed in (False, True):
            raw = swf([tag(9, b'\x00\x00\x00')], compressed)
            self.assertIs(normalize_swf_compile_date(raw, 1793318400), raw)


if __name__ == '__main__':
    unittest.main()
