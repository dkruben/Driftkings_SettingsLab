from build_tools.tests.meta_support import meta_namespace
import ast
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


overlay = load('overlay', 'source/scripts/client/Driftkings/core/overlay.py')
resources = load('ui_resources', 'build_tools/build_ui_resources.py')


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.scene = overlay.OverlayScene()
        self.view = Mock()

    def test_late_flash_load_receives_latest_state_with_parents_first(self):
        props = {'text': 'first'}
        self.scene.create('panel.text', 'label', props)
        self.scene.create('panel', 'panel', {'drag': True})
        props['text'] = 'caller mutation'
        self.scene.update('panel.text', {'text': 'latest'})
        self.scene.attach(self.view)
        items = self.view.reset.call_args.args[0]
        self.assertEqual([entry['alias'] for entry in items], ['panel', 'panel.text'])
        self.assertEqual(items[1]['props']['text'], 'latest')
        items[1]['props']['text'] = 'transport mutation'
        self.assertEqual(self.scene.elements['panel.text'][1]['text'], 'latest')

    def test_view_recreation_ignores_old_dispose_and_callbacks(self):
        self.scene.create('panel', 'panel', {'drag': True, 'x': 10})
        self.scene.attach(self.view)
        replacement = Mock()
        self.scene.attach(replacement)
        self.scene.detach(self.view)
        self.scene.moved(self.view, 'panel', 999, 999)
        self.scene.update('panel', {'x': 15})
        replacement.update.assert_called_once_with('panel', {'x': 15}, 0.0)
        self.assertEqual(self.scene.elements['panel'][1]['x'], 15)

    def test_drag_saves_zero_coordinates_but_rejects_locked_and_invalid_moves(self):
        listener = Mock()
        self.scene.updated += listener
        self.scene.create('panel', 'panel', {'drag': True, 'x': 12, 'y': 34})
        self.scene.attach(self.view)
        self.scene.moved(self.view, 'panel', 0, 0)
        listener.assert_called_once_with('panel', {'x': 0., 'y': 0.})
        self.scene.moved(self.view, 'panel', float('nan'), 1)
        self.scene.update('panel', {'drag': False})
        self.scene.moved(self.view, 'panel', 30, 40)
        self.assertEqual(listener.call_count, 1)

    def test_recursive_delete_cancels_pending_children_and_does_not_touch_siblings(self):
        for name in ('panel', 'panel.text', 'panel2'):
            self.scene.create(name, 'label', {})
        self.scene.remove('panel')
        self.assertEqual(set(self.scene.elements), {'panel2'})
        self.assertFalse(self.scene.update('panel.text', {'text': 'late'}))
        self.scene.attach(self.view)
        self.assertEqual(len(self.view.reset.call_args.args[0]), 1)

    def test_animation_state_survives_detachment(self):
        self.scene.create('text', 'label', {'alpha': 0})
        self.scene.attach(self.view)
        self.scene.animate('text', .5, {'alpha': 1})
        self.view.update.assert_called_once_with('text', {'alpha': 1}, .5)
        self.scene.detach(self.view)
        replacement = Mock()
        self.scene.attach(replacement)
        self.assertEqual(replacement.reset.call_args.args[0][0]['props']['alpha'], 1)

    def test_replacing_parent_keeps_children_in_the_live_scene(self):
        self.scene.create('panel', 'panel', {})
        self.scene.create('panel.text', 'label', {'text': 'retain'})
        self.scene.attach(self.view)
        self.view.reset.reset_mock()
        self.scene.create('panel', 'panel', {'x': 50})
        items = self.view.reset.call_args.args[0]
        self.assertEqual([item['alias'] for item in items], ['panel', 'panel.text'])
        self.assertEqual(items[1]['props']['text'], 'retain')

    def test_flash_transport_methods_exist_in_the_compiled_source(self):
        source = (ROOT/'flash_source/battle/src/driftkings/battle/components/overlay/OverlayUI.as').read_text()
        for name in ('as_reset', 'as_create', 'as_update', 'as_remove'):
            self.assertIn('public function ' + name + '(', source)
        self.assertIn('public var onElementMoved:Function', source)

    def test_native_create_lifecycle_attaches_view_and_accepts_live_elements(self):
        path = ROOT/'source/scripts/client/Driftkings/views/battle/overlay.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'OverlayView']
        visibility = Mock()
        namespace = meta_namespace(visibility)
        namespace['overlays'] = self.scene
        exec(compile(tree, str(path), 'exec'), namespace)
        view = namespace['OverlayView']()
        view.flashObject = Mock()
        self.scene.create('early', 'label', {'text': 'queued'})
        view.create()
        visibility.attach.assert_called_once_with(view)
        view.setBattleHudVisible(False)
        view.flashObject.as_setBattleHudVisible.assert_called_once_with(False)
        self.assertIs(self.scene.view, view)
        self.assertEqual(view.flashObject.as_reset.call_args.args[0][0]['alias'], 'early')
        self.scene.create('late', 'label', {'text': 'live'})
        view.flashObject.as_create.assert_called_once_with('late', 'label', {'text': 'live'})


class ResourceTests(unittest.TestCase):
    def test_declarations_are_unique_and_resolve_owned_layouts(self):
        items = resources.collect_resources()
        self.assertEqual(len(items), 8)
        self.assertNotIn('mods/Driftkings/DKModSettings/button', items)
        self.assertTrue(all(key.startswith('mods/Driftkings/') for key in items))

    def test_only_modlist_and_its_gameface_dependency_are_distributed(self):
        forbidden = ('from gui.mods.gambiter', 'import modsSettingsApi')
        for path in (ROOT/'source/scripts/client').rglob('*.py'):
            source = path.read_text(encoding='utf-8-sig')
            self.assertFalse(any(name in source for name in forbidden), path)
        libraries = list((ROOT/'res/wotmods').glob('*.wotmod'))
        self.assertTrue(libraries)
        self.assertEqual({path.name for path in libraries}, {'me.poliroid.modslistapi_1.7.9.wotmod', 'net.openwg.gameface_1.1.6.wotmod'})


if __name__ == '__main__':
    unittest.main()
