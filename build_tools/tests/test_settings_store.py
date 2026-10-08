import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('settings_store', ROOT / 'source/scripts/client/Driftkings/settings/store.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'configs' / 'Driftkings.json'
        self.store = module.SettingsStore(str(self.path))

    def test_import_once_keeps_templates_nested_fields_and_new_defaults(self):
        legacy = Mock(return_value={'enabled': False, 'textFields': {'custom': {'text': '{{name}} José'}}, 'hotKey': ['KEY_LALT']})
        defaults = {'enabled': True, 'textFields': {}, 'newOption': 4}
        result = self.store.load('PlayerPanelPro', defaults, legacy)
        self.assertFalse(result['enabled'])
        self.assertEqual(result['textFields']['custom']['text'], '{{name}} José')
        self.assertEqual(result['newOption'], 4)
        self.assertEqual(result['hotKey'], ['KEY_LALT'])
        self.store.load('PlayerPanelPro', defaults, legacy)
        legacy.assert_called_once()
        self.assertEqual(defaults['textFields'], {})

    def test_save_preserves_other_sections_unknown_keys_and_manual_changes(self):
        self.store.load('A', {'x': 1})
        self.store.load('B', {'y': 2})
        document = json.loads(self.path.read_text())
        document['components']['A']['future'] = {'flag': True}
        document['components']['B']['y'] = 7
        self.path.write_text(json.dumps(document))
        self.store.save('A', {'x': 9})
        result = self.store.read()['components']
        self.assertEqual(result['A'], {'x': 9, 'future': {'flag': True}})
        self.assertEqual(result['B']['y'], 7)
        backup = json.loads(Path(str(self.path) + '.bak').read_text())
        self.assertEqual(backup['components']['A']['x'], 1)

    def test_corrupt_file_is_not_overwritten(self):
        self.path.parent.mkdir()
        self.path.write_text('{broken')
        with self.assertRaises(ValueError): self.store.save('A', {'x': 1})
        with self.assertRaises(ValueError): self.store.load('A', {})
        self.assertEqual(self.path.read_text(), '{broken')

    def test_failed_atomic_replace_keeps_original_and_removes_temp(self):
        self.store.load('A', {'x': 1})
        original = self.path.read_bytes()
        with patch.object(module, 'replace_file', side_effect=OSError('locked')):
            with self.assertRaises(OSError): self.store.save('A', {'x': 2})
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.path.parent.glob('*.tmp')), [])

    def test_invalid_legacy_does_not_create_central_file(self):
        with self.assertRaises(ValueError): self.store.load('A', {}, lambda: [])
        self.assertFalse(self.path.exists())


    def test_windows_python27_replace_without_ctypes(self):
        self.store.load('A', {'x': 1})
        with patch.object(module.os, 'replace', None), patch.object(module.os, 'name', 'nt'):
            self.store.save('A', {'x': 2})
        self.assertEqual(self.store.read()['components']['A']['x'], 2)
        self.assertFalse(Path(str(self.path) + '.previous').exists())

    def test_windows_publish_failure_restores_original(self):
        self.store.load('A', {'x': 1})
        original = module.os.rename
        def rename(source, target):
            if str(source).endswith('.tmp'): raise OSError('publication failed')
            return original(source, target)
        with patch.object(module.os, 'replace', None), patch.object(module.os, 'name', 'nt'), patch.object(module.os, 'rename', side_effect=rename):
            with self.assertRaises(OSError): self.store.save('A', {'x': 2})
        self.assertEqual(self.store.read()['components']['A']['x'], 1)

    def test_interrupted_publication_is_recovered_on_read(self):
        self.store.load('A', {'x': 1})
        self.path.rename(str(self.path) + '.previous')
        self.assertEqual(self.store.read()['components']['A']['x'], 1)
        self.assertTrue(self.path.exists())

if __name__ == '__main__': unittest.main()

