import importlib.util
import ast
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('unified', ROOT / 'build_tools/build_unified.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ManifestFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_recursive_resources_keep_relative_paths(self):
        (self.root / 'icons/sub').mkdir(parents=True)
        (self.root / 'icons/a.png').write_bytes(b'a')
        (self.root / 'icons/sub/b.png').write_bytes(b'b')
        files = dict(module.manifest_files({'files': {'res/icons/**': 'icons/**'}}, self.root))
        self.assertEqual(set(files), {'res/icons/a.png', 'res/icons/sub/b.png'})
        self.assertEqual(files['res/icons/sub/b.png'].read_bytes(), b'b')

    def test_missing_file_and_empty_directory_fail_instead_of_silent_omission(self):
        (self.root / 'empty').mkdir()
        for mapping in ({'res/file': 'absent'}, {'res/icons/**': 'empty/**'}, {'res/icons/**': 'missing/**'}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                list(module.manifest_files({'files': mapping}, self.root))

    def test_recursive_mapping_requires_matching_directory_syntax(self):
        with self.assertRaises(ValueError):
                list(module.manifest_files({'files': {'res/icons/**': 'icons'}}, self.root))

    def test_stale_infrastructure_bytecode_is_rejected_even_outside_components(self):
        name = 'res/scripts/client/Driftkings/ui/common/injector.pyc'
        with self.assertRaisesRegex(ValueError, 'no source'):
            module.validate_owned_bytecode_source(name, self.root)
        source = self.root/'source/scripts/client/Driftkings/ui/common/injector.py'
        source.parent.mkdir(parents=True)
        source.write_text('# source exists\n')
        module.validate_owned_bytecode_source(name, self.root)
        module.validate_owned_bytecode_source('res/gui/flash/DriftkingsBattle.swf', self.root)

    def test_package_version_reads_one_central_source_and_rejects_invalid_values(self):
        target = self.root/'source/scripts/client/Driftkings/__init__.py'
        target.parent.mkdir(parents=True)
        target.write_text("VERSION = '2.3.4'\n", encoding='utf-8')
        self.assertEqual(module.package_version(self.root), '2.3.4')
        for text in ("VERSION = 'invalid'", "VERSION = '1.0.0'\nVERSION = '2.0.0'", ''):
            target.write_text(text, encoding='utf-8')
            with self.assertRaises(ValueError):
                module.package_version(self.root)

    def test_component_settings_inherit_package_version(self):
        client = ROOT/'source/scripts/client/Driftkings'
        tree = ast.parse((client/'common/config/interfaces/simple.py').read_text(encoding='utf-8-sig'))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ConfigBase')
        cls.body = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '__init__']
        tree.body = [cls]
        ns = {'VERSION': '9.8.7'}
        exec(compile(tree, 'ConfigBase', 'exec'), ns)
        self.assertEqual(ns['ConfigBase']().version, '9.8.7')
        for path in (client/'settings').glob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    self.assertFalse(any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                                         and t.value.id == 'self' and t.attr == 'version' for t in node.targets), path)

if __name__ == '__main__': unittest.main()
