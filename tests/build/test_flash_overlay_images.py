"""Flash overlay images: every path the Python side sends must be accepted by the AS3 loader whitelist."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
LOADER = ROOT / 'flash_source/shared/as3/driftkings/utils/imageloadercomponent.as'
TRAVERSE = ROOT / 'mod/res/scripts/client/driftkings/flash/battle/gun_traverse_limits.py'


def accepted_prefixes():
    text = LOADER.read_text(encoding='utf-8')
    return re.findall(r'path\.indexOf\("([^"]+)"\) == 0', text)


class FlashOverlayImageTests(unittest.TestCase):
    def test_traverse_images_are_accepted_by_the_loader(self):
        prefixes = accepted_prefixes()
        self.assertTrue(prefixes)
        sent = re.findall(r"'(\.\./aimingangles/%s/[^']*)'", TRAVERSE.read_text(encoding='utf-8'))
        self.assertEqual(len(sent), 4)  # left, right, bottom, top
        for path in sent:
            self.assertTrue(any(path.startswith(prefix) for prefix in prefixes), path)

    def test_traverse_images_exist_for_every_marker(self):
        names = ('left', 'right', 'bottom', 'top')
        for marker in range(1, 7):
            for name in names:
                for suffix in ('', '_limit'):
                    path = ROOT / 'mod/res/gui/aimingangles' / str(marker) / (name + suffix + '.png')
                    self.assertTrue(path.is_file(), str(path))


if __name__ == '__main__':
    unittest.main()
