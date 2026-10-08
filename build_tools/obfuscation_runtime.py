# -*- coding: utf-8 -*-
"""Validate actual SAFE staging/package imports on Python 2.7; no clean imports."""
import ast
import contextlib
import hashlib
import json
import os
import sys
import unittest
import zipfile


def validate(base, output, package=None, hooks=False):
    sys.dont_write_bytecode = True
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    source = os.path.join(root, 'source/scripts/client')
    assert not any(name == 'Driftkings' or name.startswith('Driftkings.') for name in sys.modules), 'Must use fresh process'
    selected = ('Driftkings.core.marks_calculator', 'Driftkings.core.updater.versioning', 'Driftkings.core.updater.manifest')
    with open(os.path.join(root, 'build/obfuscation/report.json'), 'rb') as stream: protection = json.load(stream)
    protected = dict((item['module'], item['outputSha256']) for item in protection['processed'])
    for name, digest in protected.items():
        with open(os.path.join(base, name), 'rb') as stream: assert hashlib.sha256(stream.read()).hexdigest() == digest
    previous_path = list(sys.path)
    sys.path[:] = [path for path in sys.path if source.lower() not in os.path.abspath(path).lower()]
    origin = package + '/res/scripts/client' if package else base
    sys.path.insert(0, origin)
    # Test resources must come from the package under test, not an unrelated
    # resource copy in the source tree. Staging uses current built resources.
    sys.path.append(os.path.join(root, 'build_tools/tests'))
    import windows_files_test_support as helper_fixture
    previous_initialize = helper_fixture.initialize
    windows_stats = {'V': 0, 'R': 0, 'responses': []}
    windows_originals = None
    try:
        for name in selected:
            module = __import__(name, fromlist=['*'])
            expected = os.path.join(origin, *name.split('.')) + '.pyc'
            assert os.path.normcase(os.path.normpath(module.__file__)) == os.path.normcase(os.path.normpath(expected)), module.__file__
            if package:
                with zipfile.ZipFile(package) as archive: data = archive.read('res/scripts/client/' + name.replace('.', '/') + '.pyc')
                assert hashlib.sha256(data).hexdigest() == protected[name.replace('.', '/') + '.pyc']
        from Driftkings.core.updater.versioning import Version, normalize_game_version
        from Driftkings.core.updater.manifest import Manifest, MAX_MANIFEST, MAX_PACKAGE
        from Driftkings.core.updater.endpoints import REPOSITORY
        assert Version.__name__ == 'Version' and Version.__module__ == 'Driftkings.core.updater.versioning'
        assert Manifest.__name__ == 'Manifest' and Manifest.__module__ == 'Driftkings.core.updater.manifest'
        assert callable(Manifest.parse) and callable(Manifest.document)
        from Driftkings import VERSION
        assert VERSION == '0.1.2-beta.1'
        assert Version('0.1.2-beta.1') < Version('0.1.2-rc.1') < Version('0.1.2')
        assert Version('1.0.0') <= Version('1.0.0') and Version('1.0.0') >= Version('1.0.0')
        from Driftkings.core.updater import windows_files as windows
        resources = {}
        for resource, filename in ((windows.HELPER_RESOURCE, 'Driftkings.WindowsFiles.exe'), (windows.INFO_RESOURCE, 'helper.json')):
            if package:
                with zipfile.ZipFile(package) as archive: resources[resource] = archive.read('res/' + resource)
            else:
                with open(os.path.join(root, 'build/windows-files', filename), 'rb') as stream: resources[resource] = stream.read()
        windows_hash = hashlib.sha256(resources[windows.HELPER_RESOURCE]).hexdigest()
        assert json.loads(resources[windows.INFO_RESOURCE])['sha256'] == windows_hash
        def initialize_test_helper():
            windows.initialize(resources.__getitem__, root, os.path.join(root, 'build/obfuscation/safe/windows-cache'))
        helper_fixture.initialize = initialize_test_helper
        windows_originals = (windows.WindowsPathValidator.request, windows.WindowsPathValidator.response)
        def observed_request(client, operation, *paths):
            windows_stats[operation] += 1
            return windows_originals[0](client, operation, *paths)
        def observed_response(client):
            value = windows_originals[1](client)
            windows_stats['responses'].append(value.decode('ascii'))
            return value
        windows.WindowsPathValidator.request, windows.WindowsPathValidator.response = observed_request, observed_response
        with open(os.path.join(root, 'build_tools/tests/test_updater.py'), 'rb') as stream: tree = ast.parse(stream.read())
        nodes = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'document': nodes.append(node)
            if isinstance(node, ast.ClassDef) and node.name in ('VersionTests', 'ManifestTests'):
                node.body = [item for item in node.body if getattr(item, 'name', '') != 'test_builder_uses_same_grammar']
                nodes.append(node)
        @contextlib.contextmanager
        def subtest(self, **unused): yield
        if not hasattr(unittest.TestCase, 'subTest'): unittest.TestCase.subTest = subtest
        scope = dict(unittest=unittest, json=json, Version=Version, Manifest=Manifest,
                     normalize_game_version=normalize_game_version, MAX_MANIFEST=MAX_MANIFEST,
                     MAX_PACKAGE=MAX_PACKAGE, REPOSITORY=REPOSITORY)
        exec(compile(ast.Module(body=nodes), 'existing-updater-contracts', 'exec'), scope)
        tests = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(scope[name]) for name in ('VersionTests', 'ManifestTests'))
        result = unittest.TextTestRunner(verbosity=1).run(tests)
        assert result.wasSuccessful(), 'Protected metadata contracts failed'
        with open(os.path.join(root, 'build_tools/tests/test_updater_smoke.py'), 'rb') as stream: tree = ast.parse(stream.read())
        tree.body = [node for node in tree.body if not isinstance(node, ast.If) and not
                     (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and
                      isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'insert')]
        namespace = {'__file__': os.path.join(root, 'build_tools/tests/test_updater_smoke.py'), '__name__': 'safe_updater_tests'}
        exec(compile(tree, 'existing-updater-smoke', 'exec'), namespace)
        smoke = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(value) for value in namespace.values()
                                   if isinstance(value, type) and issubclass(value, unittest.TestCase))
        smoke_result = unittest.TextTestRunner(verbosity=2).run(smoke)
        assert smoke_result.wasSuccessful(), 'Protected updater smoke failed'
        assert 'READY\t1' in windows_stats['responses'] and windows_stats['V'] > 0 and windows_stats['R'] > 0
        assert all(value in ('READY\t1', 'OK\tV', 'OK\tR') for value in windows_stats['responses'])
        from Driftkings.component_list import COMPONENTS
        assert len(COMPONENTS) > 0 and len(COMPONENTS) == len(set(COMPONENTS))
        from Driftkings.settings.service import SettingsService
        from Driftkings.settings.settings_data import SettingsData
        from Driftkings._constants import OWN_HEALTH
        class Config(object):
            ID = OWN_HEALTH.ID
            data = {'enabled': True}
        service = SettingsService(SettingsData())
        service.register(Config())
        if hooks:
            os.environ['DK_SMOKE_STAGING'] = base
            import python27_hooks_smoke
            class UI(object):
                def write(self, text): sys.stdout.write(text)
            python27_hooks_smoke.smoke(UI())
        loaded = dict((name, module.__file__) for name, module in sys.modules.items()
                      if name.startswith('Driftkings.') and getattr(module, '__file__', None))
        assert all(source.lower() not in os.path.abspath(path).lower() for path in loaded.values()), loaded
        report = dict(python=sys.version, status='passed', protectedHashes=protected, loaded=loaded,
                      metadataTests=result.testsRun, updaterSmokeTests=smoke_result.testsRun,
                      componentCount=len(COMPONENTS), settingsRegistration=True, managedHooks=hooks, package=package,
                      windowsFiles=dict(helperSha256=windows_hash, requests=windows_stats, resourceOrigin=package or 'current local build'))
        with open(output, 'wb') as stream: stream.write(json.dumps(report, indent=2).encode('utf-8'))
    finally:
        helper_fixture.initialize = previous_initialize
        if windows_originals is not None:
            windows.close()
            windows.WindowsPathValidator.request, windows.WindowsPathValidator.response = windows_originals
        sys.path[:] = previous_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base')
    parser.add_argument('output')
    parser.add_argument('--package')
    args = parser.parse_args()
    validate(args.base, args.output, args.package)
