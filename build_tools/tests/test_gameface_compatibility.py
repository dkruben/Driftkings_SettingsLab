import ast
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load('compatibility_builder', 'build_tools/build_unified.py')


class GamefaceCompatibilityTests(unittest.TestCase):
    def test_conflicting_global_resource_is_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            with zipfile.ZipFile(Path(folder)/'openwg.wotmod', 'w') as archive:
                archive.writestr('res/gui/gameface/js/index.js', b'OpenWG')
            with self.assertRaisesRegex(ValueError, 'Package resource conflict'):
                builder.validate_dependency_resources({'res/gui/gameface/js/index.js': b'Driftkings'}, Path(folder))
            builder.validate_dependency_resources({'res/gui/gameface/mods/Driftkings/shared/bootstrap.js': b'ours'}, Path(folder))

    def test_actual_dependencies_have_no_resource_conflicts(self):
        builder.validate_dependency_resources({}, ROOT/'res/wotmods')
        manifest = json.loads((ROOT/'build_data/components/ui.json').read_text())
        self.assertNotIn('res/gui/gameface/js/index.js', manifest['files'])
        self.assertNotIn('res/gui/unbound/res_map.json', manifest['files'])
        self.assertIn('res/gui/gameface/mods/Driftkings/shared/bootstrap.js', manifest['files'])

    def test_bridge_uses_shared_ids_and_injects_only_owned_bootstrap(self):
        class Model:
            def __init__(self, properties=0, commands=0):
                self.values = {}
                self.properties = properties
                self._initialize()
            def _initialize(self): pass
            def _addStringProperty(self, name, value): self.values[name] = value
            def _addViewModelProperty(self, name, value): self.values[name] = value
        dependency = types.SimpleNamespace(gf_mod_inject=Mock(), res_id_by_key=Mock(return_value=812))
        with patch.dict(sys.modules, {'frameworks.wulf': types.SimpleNamespace(ViewModel=Model), 'openwg_gameface': dependency}):
            bridge = load('gameface_compatibility_bridge', 'source/scripts/client/Driftkings/ui/gameface.py')
            parent = Model()
            bridge.attach_assets(parent, 'DriftkingsCarouselStats', ['a.css'], ['first.js', 'second.js'])
            dependency.gf_mod_inject.assert_called_once_with(parent, 'DriftkingsCarouselStatsBridge', scripts=[bridge.BOOTSTRAP])
            meta = parent.values['DriftkingsUI']
            self.assertEqual(meta.properties, len(meta.values))
            self.assertEqual(json.loads(meta.values['scripts']), ['first.js', 'second.js'])
            self.assertEqual(bridge.resource_id('mods/Driftkings/CarouselStats/model'), 812)
            dependency.res_id_by_key.return_value = 945
            self.assertEqual(bridge.resource_id('mods/Driftkings/CarouselStats/model'), 945)

    def test_all_asset_models_reserve_payload_and_two_metadata_properties(self):
        found = 0
        for path in (ROOT/'source/scripts/client/Driftkings/views').rglob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef) or not any(isinstance(base, ast.Name) and base.id == 'ViewModel' for base in node.bases): continue
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'attach_assets' for method in methods for n in ast.walk(method)): continue
                found += 1
                init = next(n for n in methods if n.name == '__init__')
                props = [keyword.value.value for n in ast.walk(init) if isinstance(n, ast.Call) for keyword in n.keywords if keyword.arg == 'properties']
                self.assertEqual(props, [3], path)
        self.assertEqual(found, 6)


if __name__ == '__main__': unittest.main()
