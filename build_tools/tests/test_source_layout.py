import ast
import json
import re
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'source/scripts/client'


class SourceLayoutTests(unittest.TestCase):
    def test_local_imports_resolve_after_moves(self):
        for path in (CLIENT/'Driftkings').rglob('*.py'):
            # This traceback helper intentionally uses Python 2's three-argument raise.
            # The Python 2 build smoke check parses and checks its imports directly.
            if path == CLIENT/'Driftkings/common/utils/abstract.py':
                continue
            tree=ast.parse(path.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                module=node.module if isinstance(node,ast.ImportFrom) else None
                if module and module.startswith('Driftkings.'):
                    target=CLIENT/module.replace('.','/')
                    self.assertTrue(target.with_suffix('.py').is_file() or (target/'__init__.py').is_file(), (path,module))

    def test_components_keep_settings_definitions_outside_gameplay(self):
        for scope in ('battle','lobby','components'):
            for path in (CLIENT/'Driftkings'/scope).glob('*.py'):
                tree=ast.parse(path.read_text(encoding='utf-8-sig'))
                for cls in (n for n in tree.body if isinstance(n,ast.ClassDef)):
                    if any(isinstance(b,ast.Name) and b.id=='Settings' for b in cls.bases):
                        self.assertFalse(any(isinstance(n,ast.FunctionDef) and n.name in ('init','createTemplate') for n in cls.body),path)

    def test_presentation_hooks_still_imported_for_registration(self):
        for scope,name in (('components','battle_efficiency'),('lobby','hangar_options')):
            path=CLIENT/'Driftkings'/scope/(name+'.py')
            tree=ast.parse(path.read_text(encoding='utf-8'))
            self.assertTrue(any(isinstance(n,ast.ImportFrom) and n.module=='Driftkings.views.hangar' and
                                any(a.name==name+'_hooks' for a in n.names) for n in tree.body))

    def test_flash_projects_and_manifests_use_grouped_inputs(self):
        flash=ROOT/'flash_source'
        for project in flash.glob('*/*/*.as3proj'):
            tree=ET.parse(project)
            for node in tree.findall('./classpaths/class'):
                self.assertTrue((project.parent/node.get('path')).is_dir(), project)
            for node in tree.findall('./externalLibraryPaths/element'):
                self.assertTrue((project.parent/node.get('path')).is_file(), project)
            for node in tree.findall('./compileTargets/compile'):
                self.assertTrue((project.parent/node.get('path').replace('\\','/')).is_file(),project)
        for path in (ROOT/'build_data/components').glob('*.json'):
            manifest=json.loads(path.read_text(encoding='utf-8-sig'))
            for destination,source in manifest.get('files',{}).items():
                if source.startswith('res/flash/') and source.endswith('.swf'):
                    self.assertIn(Path(source).parts[2],('battle','hangar','shared'))
                    self.assertTrue((ROOT/source).is_file(),source)
                    self.assertTrue(destination.startswith('res/gui/flash/'))

    def test_flash_classes_have_unique_packages_and_resolvable_owned_imports(self):
        roots = [ROOT/'flash_source/battle/src', ROOT/'flash_source/shared/as3']
        classes = {}
        sources = []
        for root in roots:
            for path in root.rglob('*.as'):
                text = path.read_text(encoding='utf-8-sig')
                package = re.search(r'package\s*([\w.]*)\s*\{', text).group(1)
                name = (package + '.' if package else '') + path.stem
                self.assertNotIn(name, classes, name)
                classes[name] = path
                self.assertEqual(path.relative_to(root).as_posix(), name.replace('.', '/') + '.as')
                sources.append((path, text))
        for path, text in sources:
            for name in re.findall(r'import\s+(driftkings\.[\w.]+);', text):
                self.assertIn(name, classes, (path, name))
            for image in re.findall(r'\[Embed\(source\s*=\s*"([^"]+)"', text):
                self.assertTrue((path.parent/image).is_file(), (path, image))

    def test_settings_base_keeps_constructor_callbacks_safe(self):
        class CoreConfig:
            def __init__(self):
                self.init()
                self.onApplySettings({})
            def init(self): pass
            def onApplySettings(self, settings): self.data.update(settings)
        classes=[]
        for name in ('base.py', 'battle/own_health.py'):
            settings=ast.parse((CLIENT/'Driftkings/settings/templates'/name).read_text(encoding='utf-8'))
            classes.extend(n for n in settings.body if isinstance(n,ast.ClassDef))
        from Driftkings.settings.settings_data import defaults, default_keys
        from Driftkings._constants import OWN_HEALTH, GLOBAL
        from Driftkings.settings.template_schema import build_template, slider
        settings_ns={'build_template':build_template, 'slider':slider, 'OWN_HEALTH':OWN_HEALTH, 'GLOBAL':GLOBAL, 'DriftkingsConfigInterface':CoreConfig, 'defaults':defaults, 'default_keys':default_keys, 'processHotKeys':lambda *args:None}
        exec(compile(ast.Module(body=classes,type_ignores=[]),'OwnHealthSettings','exec'),settings_ns)
        runtime=ast.parse((CLIENT/'Driftkings/battle/own_health.py').read_text(encoding='utf-8'))
        declaration=next(n for n in runtime.body if isinstance(n,ast.ImportFrom) and
                         n.module=='Driftkings.settings.templates.battle.own_health')
        self.assertEqual([(n.name, n.asname) for n in declaration.names], [('OwnHealthSettings', 'ConfigInterface')])
        instance=settings_ns['OwnHealthSettings']()
        self.assertEqual(instance.data['colors']['ally'],'#60CB00')
        self.assertEqual(instance.data['y'],-55)
