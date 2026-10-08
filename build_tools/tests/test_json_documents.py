import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/scripts/client'))
from Driftkings.settings.store import JsonDocuments, SettingsStore, read_object
from Driftkings.settings.carousel_store import CarouselStore, FILES


class JsonDocumentsTests(unittest.TestCase):
    def test_carousel_middle_write_failure_restores_all_documents(self):
        with tempfile.TemporaryDirectory() as folder:
            store = CarouselStore(folder)
            data = store.load()
            before = {name: read_object(str(Path(folder, name))) for name in FILES}
            data['carousel']['rows'] = 2
            data['carousel']['normal']['width'] += 1
            data['carousel']['small']['width'] += 1
            write = SettingsStore.write
            failed = []

            def interrupted(writer, document):
                if Path(writer.path).name == FILES[1] and not failed:
                    failed.append(True)
                    raise IOError('simulated write failure')
                return write(writer, document)

            with patch.object(SettingsStore, 'write', interrupted):
                with self.assertRaises(IOError):
                    store.save(data)
            self.assertEqual(before, {name: read_object(str(Path(folder, name))) for name in FILES})
            self.assertFalse(Path(folder, '.transaction.json').exists())

    def test_restart_rolls_back_new_and_replaced_documents(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'a.json').write_text('{"v":2}')
            Path(folder, 'b.json').write_text('{"new":true}')
            Path(folder, '.transaction.json').write_text('{"a.json":{"v":1},"b.json":null}')
            JsonDocuments(folder, ('a.json', 'b.json')).recover()
            self.assertEqual(read_object(str(Path(folder, 'a.json'))), {'v': 1})
            self.assertFalse(Path(folder, 'b.json').exists())
            self.assertFalse(Path(folder, '.transaction.json').exists())

    def test_invalid_journal_does_not_partially_restore(self):
        for invalid in ({'outside.json': {}}, {'b.json': []}):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as folder:
                Path(folder, 'a.json').write_text('{"v":2}')
                journal = dict({'a.json': {'v': 1}}, **invalid)
                Path(folder, '.transaction.json').write_text(json.dumps(journal))
                with self.assertRaises(ValueError):
                    JsonDocuments(folder, ('a.json', 'b.json')).recover()
                self.assertEqual(read_object(str(Path(folder, 'a.json'))), {'v': 2})
                self.assertTrue(Path(folder, '.transaction.json').exists())

    def test_serialization_failure_precedes_first_write(self):
        with tempfile.TemporaryDirectory() as folder:
            store = JsonDocuments(folder, ('a.json', 'b.json'))
            with self.assertRaises(TypeError):
                store.publish([(str(Path(folder, 'a.json')), {}),
                               (str(Path(folder, 'b.json')), {'invalid': object()})])
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_failed_recovery_retains_journal_for_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, '.transaction.json').write_text('{"a.json":{"v":1}}')
            store = JsonDocuments(folder, ('a.json',))
            with patch.object(SettingsStore, 'write', side_effect=IOError('disk unavailable')):
                with self.assertRaises(IOError):
                    store.recover()
            self.assertTrue(Path(folder, '.transaction.json').exists())
            store.recover()
            self.assertEqual(read_object(str(Path(folder, 'a.json'))), {'v': 1})
