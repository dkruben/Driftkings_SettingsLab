# -*- coding: utf-8 -*-
"""Real control/session logic with narrow import adapters for the game facade."""
import os
import types
try:
    import builtins
except ImportError:
    import __builtin__ as builtins


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIENT = os.path.join(ROOT, 'mod', 'res', 'scripts', 'client', 'driftkings')


def load_source(relative, dependencies):
    original_import = builtins.__import__
    dependencies = dict(dependencies)
    if 'driftkings.common.utils.compat' not in dependencies:
        compat_path = os.path.join(CLIENT, 'common', 'utils', 'compat.py')
        compat = {'__name__': '_compat_test'}
        with open(compat_path, 'rb') as stream:
            exec(compile(stream.read(), compat_path, 'exec'), compat)
        module = types.ModuleType('driftkings.common.utils.compat')  # SimpleNamespace does not exist on Python 2
        module.__dict__.update(compat)
        dependencies['driftkings.common.utils.compat'] = module
    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if name in dependencies:
            return dependencies[name]
        return original_import(name, globals, locals, fromlist, level)
    api = dict(vars(builtins))
    api['__import__'] = importing
    path = os.path.join(CLIENT, *relative.split('/'))
    namespace = {'__name__': '_settings_test', '__builtins__': api, '__file__': path}
    with open(path, 'rb') as stream:
        eval(compile(stream.read(), path, 'exec'), namespace)
    return namespace

