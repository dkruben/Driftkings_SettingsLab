"""Pure build/contract tests. No game process, network, Inno or Windows required."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_tools.validate_build_data import build_plan
from build_tools.validate_installer_assets import validate, validate_png, inventory_limit


from support.build_assets import png


class AssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = build_plan(ROOT)['assets']

    def test_current_assets_and_optional_branding_warnings(self):
        report = validate(ROOT, self.assets)
        self.assertGreaterEqual(report['banks'], 1)
        self.assertGreaterEqual(report['icons'], 10)
        for name in ('setup-icon.ico', 'wizard-large.bmp', 'wizard-small.bmp'):
            if not (ROOT / 'installer/setup/assets/branding' / name).exists() and not (ROOT / 'installer/setup/assets/branding' / name.replace('.bmp', '.png')).exists():
                self.assertTrue(any(name in warning for warning in report['warnings']))

    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        path = root / 'mod/res/scripts/client/driftkings/core/updater/inventory.py'
        path.parent.mkdir(parents=True)
        shutil.copy2(ROOT / path.relative_to(root), path)
        audio = root / 'mod/res/audioww'
        audio.mkdir(parents=True)
        return root, audio

    def test_missing_or_unlisted_xml_and_unpacked_banks_fail(self):
        root, audio = self.fixture()
        (audio / 'new.bnk').write_bytes(b'bank')
        assets = [{'source': 'mod/res/audioww/new.' + ext} for ext in ('bnk', 'xml')]
        with self.assertRaisesRegex(ValueError, 'Missing bank XML'):
            validate(root, assets)
        xml = audio / 'new.xml'
        xml.write_text('<audio_mods.xml><loadBanks/></audio_mods.xml>')
        with self.assertRaisesRegex(ValueError, 'missing from loadBanks'):
            validate(root, assets)
        xml.write_text('<audio_mods.xml><loadBanks><bank><name>new.bnk</name></bank></loadBanks></audio_mods.xml>')
        self.assertEqual(validate(root, assets)['banks'], 1)
        with self.assertRaisesRegex(ValueError, 'not declared'):
            validate(root, assets[:1])
        (audio / 'new.bnk').unlink()
        with self.assertRaisesRegex(ValueError, 'Orphan bank XML'):
            validate(root, assets)

    def test_source_project_is_not_a_distribution_payload(self):
        with self.assertRaisesRegex(ValueError, 'Wwise source project'):
            validate(ROOT, [{'source': 'res/sound_bank_wwise/source.bnk'}])

    def test_bank_size_uses_the_inventory_limit(self):
        root, audio = self.fixture()
        path = root / 'mod/res/scripts/client/driftkings/core/updater/inventory.py'
        text = path.read_text(encoding='utf-8').replace('MAX_FILE = 64 * 1024 * 1024', 'MAX_FILE = 3')
        path.write_text(text, encoding='utf-8')
        (audio / 'new.bnk').write_bytes(b'1234')
        (audio / 'new.xml').write_text('<audio_mods.xml/>')
        with self.assertRaisesRegex(ValueError, 'inventory limit'):
            validate(root, [{'source': 'mod/res/audioww/new.' + ext} for ext in ('bnk', 'xml')])

    def test_png_crc_truncation_and_size_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'icon.png'
            path.write_bytes(png())
            self.assertEqual(validate_png(path, inventory_limit(ROOT)), (1, 1))
            with self.assertRaises(ValueError):
                validate_png(path, 20)
            raw = bytearray(png())
            raw[20] ^= 1
            for data in (bytes(raw), png()[:-1], b'not a png'):
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    validate_png(path, inventory_limit(ROOT))

    def test_documentation_is_excluded_and_no_loose_media_are_installed(self):
        self.assertFalse(any(entry['source'].endswith('/readme.md') for entry in self.assets))
        script = (ROOT / 'installer/setup/driftkings.iss').read_text(encoding='utf-8')
        code = (ROOT / 'installer/setup/wizard.iss').read_text(encoding='utf-8')
        self.assertIn('components.generated.iss', script)
        self.assertIn('payload.generated.iss', script)
        self.assertNotIn('Source:', script)
        self.assertIn('if not PreserveProfile then ApplyConfiguration', code)
        self.assertIn('uninsneveruninstall', script)
        self.assertNotIn('DelTree', code)
        self.assertLess(code.index('Configuration backup failed'), code.index('if not DeleteFile(ConfigRoot'))

