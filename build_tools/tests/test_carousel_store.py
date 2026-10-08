import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/scripts/client'))
from Driftkings.core.carousel import config_defaults
from Driftkings.settings.carousel_store import CarouselStore, FILES, documents


class CarouselStoreTests(unittest.TestCase):
    def test_up_to_four_rows_roundtrip_and_five_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            store = CarouselStore(folder)
            data = store.load()
            for rows in (0,1,2,3,4):
                data['carousel']['rows'] = rows
                store.save(data)
                self.assertEqual(store.load()['carousel']['rows'],rows)
            original = Path(folder, FILES[0]).read_bytes()
            for rows in (5,-1,2.5,True):
                data['carousel']['rows'] = rows
                with self.assertRaises(ValueError): store.save(data)
                self.assertEqual(Path(folder, FILES[0]).read_bytes(),original)

    def test_first_load_ignores_old_slots_and_generates_three_files(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'CarouselStats.json').write_text('{"slot1X":99}')
            data = CarouselStore(folder).load()
            self.assertEqual(data, config_defaults())
            self.assertTrue(all(Path(folder, name).is_file() for name in FILES))

    def test_roundtrip_profiles_empty_fields_and_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            store = CarouselStore(folder)
            data = store.load()
            data['carousel']['normal']['extraFields'] = []
            data['carousel']['small']['extraFields'][0]['format'] = 'Vit\u00f3rias {{winrate}}'
            data['carousel']['rows'] = 2
            store.save(data)
            self.assertEqual(store.load(), data)
            self.assertTrue(Path(folder, FILES[1] + '.bak').is_file())

    def test_invalid_document_preserved_and_no_missing_files_created(self):
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder, FILES[1])
            broken.write_text('{broken')
            with self.assertRaises(ValueError):
                CarouselStore(folder).load()
            self.assertEqual(broken.read_text(), '{broken')
            self.assertFalse(Path(folder, FILES[0]).exists())

    def test_bad_profile_rejected_before_saving_general(self):
        with tempfile.TemporaryDirectory() as folder:
            store = CarouselStore(folder)
            data = store.load()
            original = Path(folder, FILES[0]).read_bytes()
            data['carousel']['rows'] = 2
            data['carousel']['small']['extraFields'] = [None]
            with self.assertRaises(ValueError):
                store.save(data)
            self.assertEqual(Path(folder, FILES[0]).read_bytes(), original)

    def test_distributed_templates_match_defaults(self):
        for name, expected in zip(FILES, documents(config_defaults())):
            path = ROOT / 'res/configs/Driftkings/default/carousel_stats' / name
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), expected)
