# -*- coding: utf-8 -*-
"""Validate the iterable-of-pairs contract used by WG EventsHandler."""
import ast
import os
import unittest

from support import CLIENT


class GamefaceEventsTests(unittest.TestCase):
    def test_literal_event_extensions_contain_pairs_not_a_flat_command_and_handler(self):
        checked = 0
        for folder, dirs, files in os.walk(CLIENT):
            for name in files:
                if not name.endswith('.py'):
                    continue
                path = os.path.join(folder, name)
                with open(path, 'rb') as stream:
                    tree = ast.parse(stream.read(), path)
                for method in ast.walk(tree):
                    if not isinstance(method, ast.FunctionDef) or method.name != '_getEvents':
                        continue
                    for node in ast.walk(method):
                        if (isinstance(node, ast.Return) and isinstance(node.value, ast.BinOp) and
                                isinstance(node.value.op, ast.Add) and isinstance(node.value.right, ast.Tuple)):
                            for event in node.value.right.elts:
                                checked += 1
                                self.assertTrue(isinstance(event, ast.Tuple) and len(event.elts) == 2,
                                                '%s:%d must append (event, handler) pairs' % (path, method.lineno))
        self.assertGreater(checked, 0)
