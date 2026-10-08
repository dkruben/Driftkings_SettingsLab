# -*- coding: utf-8 -*-
"""Python 2.7 checks of the actual protected file or experimental package."""
import ast
import hashlib
import imp
import json
import math
import os
import sys
import tempfile
import zipfile
import unittest


def validate(original, protected, output, package=None):
    source = imp.load_source('poc_reference', original)
    before = set(sys.modules)
    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins
    importing = builtins.__import__
    imports = []
    def restricted(name, *args, **kwargs):
        imports.append(name)
        if name.split('.')[0] in ('ctypes', '_ctypes', 'PjOrion', 'pjorion', 'dispack', 'dcpack'):
            raise ImportError('POC output must not require tool runtime or ctypes: ' + name)
        return importing(name, *args, **kwargs)
    temporary = None
    package_import = None
    previous_path = list(sys.path)
    try:
        if package:
            with zipfile.ZipFile(package) as archive:
                assert archive.testzip() is None
                data = archive.read('res/scripts/client/Driftkings/core/marks_calculator.pyc')
                with open(protected, 'rb') as handle: assert data == handle.read()
                assert len([n for n in archive.namelist() if n.startswith('res/scripts/client/gui/mods/mod_')]) == 1
                assert all(archive.read(n)[:4] == '\x03\xf3\x0d\x0a' for n in archive.namelist() if n.endswith('.pyc'))
            descriptor, temporary = tempfile.mkstemp(suffix='.pyc', dir=os.path.dirname(output))
            with os.fdopen(descriptor, 'wb') as handle: handle.write(data)
        builtins.__import__ = restricted
        candidate = imp.load_compiled('poc_protected', temporary or protected)
        assert os.path.abspath(candidate.__file__) == os.path.abspath(temporary or protected)
        comparisons = 0
        values = [n / 100.0 for n in range(10001)]
        values += [n + offset for n in (-100, -1, 0, 65, 85, 95, 100, 2840, 30000)
                   for offset in (-.000001, 0, .000001)]
        for value in values:
            for name in ('ceil_damage', 'ceil_damage_tens'):
                expected = getattr(source, name)(value)
                actual = getattr(candidate, name)(value)
                assert actual == expected and type(actual) is type(expected), (name, value)
                comparisons += 1
        for value in (float('nan'), float('inf'), -float('inf')):
            for name in ('ceil_damage', 'ceil_damage_tens'):
                exceptions = []
                for module in (source, candidate):
                    try: getattr(module, name)(value)
                    except Exception as error: exceptions.append(type(error).__name__)
                assert len(exceptions) == 2 and exceptions[0] == exceptions[1]
                comparisons += 1
        for damage in (0, 1, 2840, 123.5):
            for assists in ((0, 0, 0), (100, 50, 20), (20, 100, 50), (20, 50, 100),
                            (100, 100, 100), (100, 100.0, 0), (100.0, 100, 0)):
                expected = source.combined_damage(damage, *assists)
                actual = candidate.combined_damage(damage, *assists)
                assert actual == expected and type(actual) is type(expected)
                comparisons += 1
        # Run the existing arithmetic test class with protected function bindings.
        # Do not import the Python-3 test module (that imports clean source).
        class FilePath(object):
            def __init__(self, path): self.path = path
            def __div__(self, name): return FilePath(os.path.join(self.path, name))
            __truediv__ = __div__
            def read_text(self):
                with open(self.path, 'rb') as handle: return handle.read()
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        with open(os.path.join(root, 'build_tools/tests/test_marks_equivalence.py'), 'rb') as handle:
            tree = ast.parse(handle.read())
        tree.body = [node for node in tree.body if getattr(node, 'name', None) in
                     ('old_units', 'old_tens', 'MarksEquivalenceTests')]
        assert len(tree.body) == 3
        namespace = dict(unittest=unittest, math=math, ast=ast, ROOT=FilePath(root),
                         ceil_damage=candidate.ceil_damage, ceil_damage_tens=candidate.ceil_damage_tens,
                         combined_damage=candidate.combined_damage)
        eval(compile(tree, 'existing_marks_tests_bound_to_protected_output', 'exec'), namespace)
        try:
            from StringIO import StringIO
        except ImportError:
            from io import StringIO
        log = StringIO()
        result = unittest.TextTestRunner(stream=log).run(unittest.defaultTestLoader.loadTestsFromTestCase(namespace['MarksEquivalenceTests']))
        assert result.wasSuccessful(), log.getvalue()
        if package:
            assert 'Driftkings' not in sys.modules, 'Clean package already imported; test would be ambiguous'
            sys.path.insert(0, package + '/res/scripts/client')
            module = __import__('Driftkings.core.marks_calculator', fromlist=['ceil_damage'])
            expected_path = os.path.normcase(os.path.normpath(package + '/res/scripts/client/Driftkings/core/marks_calculator.pyc'))
            assert os.path.normcase(os.path.normpath(module.__file__)) == expected_path
            assert module.ceil_damage(64.99) == 65 and module.ceil_damage_tens(2840.001) == 2850
            assert module.combined_damage(2500, 340, 100, 20) == 2840
            package_import = module.__file__
        report = dict(status='passed', pythonVersion=sys.version, executable=sys.executable,
                      loadedFile=candidate.__file__, comparisons=comparisons, imports=sorted(set(imports)),
                      newModules=sorted(set(sys.modules) - before), package=package,
                      extraToolRuntime=False, ctypesRequired=False,
                      existingMarksTests=result.testsRun,
                      actualPackageImport=package_import,
                      protectedSha256=hashlib.sha256(open(protected, 'rb').read()).hexdigest())
        with open(output, 'w') as handle: json.dump(report, handle, indent=2)
        return report
    finally:
        builtins.__import__ = importing
        sys.path[:] = previous_path
        for name in set(sys.modules) - before:
            if name == 'Driftkings' or name.startswith('Driftkings.'):
                del sys.modules[name]
        if temporary and os.path.exists(temporary): os.remove(temporary)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True)
    parser.add_argument('--protected', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--package')
    args = parser.parse_args()
    print(json.dumps(validate(args.original, args.protected, args.output, args.package), indent=2))
