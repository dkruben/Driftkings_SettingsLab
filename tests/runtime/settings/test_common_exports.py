# -*- coding: utf-8 -*-
"""Package markers must not import the game or restore the old facade."""
import ast
import os
import unittest
from support.settings import CLIENT, load_source


class CommonExportsTests(unittest.TestCase):
    def test_package_markers_have_no_import_side_effects(self):
        for relative in ('common/__init__.py', 'common/utils/__init__.py'):
            namespace = load_source(relative, {})
            self.assertNotIn('BigWorld', namespace)
            self.assertNotIn('curCV', namespace)
            self.assertNotIn('callback', namespace)

    def test_runtime_no_longer_imports_functions_from_common_facade(self):
        for directory, dirs, files in os.walk(CLIENT):
            for name in files:
                if not name.endswith('.py'):
                    continue
                path = os.path.join(directory, name)
                with open(path, 'rb') as stream:
                    text = stream.read().decode('utf-8-sig')
                tree = ast.parse(text.encode('utf-8'), path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        self.assertNotEqual(node.module, 'driftkings.common', path)
                        self.assertNotEqual(node.module, 'driftkings.common.utils.logger', path)
