# -*- coding: utf-8 -*-
"""Load real portable modules without executing the game's package facades."""
import importlib
import os
import sys
import types
import unittest
try:
    import builtins
except ImportError:
    import __builtin__ as builtins

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIENT = os.path.join(ROOT, 'mod', 'res', 'scripts', 'client', 'driftkings')


def module(**values):
    result = types.ModuleType('test_stub')
    result.__dict__.update(values)
    return result


class RuntimeTest(unittest.TestCase):
    def setUp(self):
        self.saved = dict((key, value) for key, value in sys.modules.items()
                          if key == 'driftkings' or key.startswith('driftkings.'))
        self.addCleanup(self.restore_modules)
        for key in self.saved:
            del sys.modules[key]
        for name, relative in (('driftkings', ''), ('driftkings.core', 'core'),
                               ('driftkings.common', 'common'), ('driftkings.common.utils', 'common/utils')):
            package = types.ModuleType(name)
            package.__path__ = [os.path.join(CLIENT, *relative.split('/'))]
            sys.modules[name] = package
        sys.modules['driftkings'].VERSION = '1.0.0'

    def restore_modules(self):
        for key in list(sys.modules):
            if key == 'driftkings' or key.startswith('driftkings.'):
                del sys.modules[key]
        sys.modules.update(self.saved)

    def load(self, relative):
        module = importlib.import_module('driftkings.' + relative)
        # Tests must not depend on the production trust anchor: start every test with no trusted keys.
        signature = sys.modules.get('driftkings.core.updater.signature')
        if signature is not None and signature is not self.__dict__.get('_signature_reset'):
            signature.TRUSTED_KEYS = ()
            self._signature_reset = signature
        return module


def source(relative, dependencies):
    """Stub import boundaries only; execute the entire production source."""
    original = builtins.__import__

    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if name in dependencies:
            return dependencies[name]
        return original(name, globals, locals, fromlist, level)

    api = dict(vars(builtins))
    api['__import__'] = importing
    path = os.path.join(CLIENT, *relative.split('/'))
    namespace = {'__name__': '_core_test', '__file__': path, '__builtins__': api}
    with open(path, 'rb') as stream:
        eval(compile(stream.read(), path, 'exec'), namespace)
    return namespace


# Standard library modules a feature may import; everything else is a game boundary.
STDLIB = frozenset(('math', 'logging', 'collections', 'functools', 're', 'json', 'weakref', 'os', 'time', 'copy',
                    'itertools', 'types', 'operator', 'codecs', 'io', 'struct', 'threading', 'sys', 'random',
                    'string', 'traceback', 'inspect', 'hashlib', 'base64', 'zlib', 'binascii', 'datetime',
                    'calendar', 'heapq', 'bisect', 'contextlib', 'abc', 'numbers', 'decimal', 'colorsys'))


class _AutoMeta(type):
    """Game classes, modules and constants: any attribute is another stub with a stable identity."""
    registry = {}

    def __getattr__(cls, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return auto(cls._dk_path + '.' + name)

    # String constants are often joined with text, e.g. NAME + '-SERVER'.
    def __add__(cls, other):
        return cls._dk_path + other

    def __radd__(cls, other):
        return other + cls._dk_path


def _instance_attribute(self, name):
    if name.startswith('__'):
        raise AttributeError(name)
    return auto(type(self)._dk_path + '().' + name)


def auto(path):
    if path not in _AutoMeta.registry:
        _AutoMeta.registry[path] = _AutoMeta(str(path.rsplit('.', 1)[-1]), (object,), {
            '_dk_path': path, '__getattr__': _instance_attribute,
            '__init__': lambda self, *args, **kwargs: None,
            '__call__': lambda self, *args, **kwargs: auto(type(self)._dk_path + '()')()})
    return _AutoMeta.registry[path]


class Hooks(object):
    """Records override/on_event wrappers so tests can call them like the client would."""
    def __init__(self):
        self.overrides, self.events = {}, {}

    def override(self, target, name=None, handler=None, *args, **kwargs):
        def record(function):
            self.overrides[(getattr(target, '__name__', str(target)), name)] = function
            return function
        return record(handler) if handler is not None else record

    def on_event(self, signal, handler=None):
        def record(function):
            self.events.setdefault(getattr(signal, '_dk_path', signal), []).append(function)
            return function
        return record(handler) if handler is not None else record

    def typed(self, target, name):
        # overrideMethod / overrideClassMethod / overrideStaticMethod: always decorators.
        return self.override(target, name)

    def get(self, target, name):
        return self.overrides[(target, name)]


# Pure helpers that must behave like production even when every other driftkings import is stubbed.
ALWAYS_REAL = ('driftkings.logger', 'driftkings.common.utils.compat')


def game_source(relative, stubs=None, real=(), extra_builtins=None):
    """Execute a feature module with every game and unlisted Driftkings import stubbed.

    `stubs` maps import names to objects; names in `real` use the actual module.
    `extra_builtins` supplies Python 2 names such as unicode. Returns (namespace, hooks).
    """
    stubs = dict(stubs or {})
    hooks = stubs.setdefault('driftkings.core.hooks', None) or Hooks()
    if isinstance(hooks, Hooks):
        stubs['driftkings.core.hooks'] = module(override=hooks.override, on_event=hooks.on_event, hooks=module(current=None),
                                                overrideMethod=hooks.typed, overrideClassMethod=hooks.typed,
                                                overrideStaticMethod=hooks.typed)
    original = builtins.__import__

    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if name in stubs:
            return stubs[name]
        if name in real or name in ALWAYS_REAL or name.split('.')[0] in STDLIB or name == '__future__':
            return original(name, globals, locals, fromlist, level)
        return auto(name) if fromlist else auto(name.split('.')[0])

    api = dict(vars(builtins))
    api.update(extra_builtins or {})
    api['__import__'] = importing
    path = os.path.join(CLIENT, *relative.split('/'))
    namespace = {'__name__': '_feature_test', '__file__': path, '__builtins__': api}
    with open(path, 'rb') as stream:
        eval(compile(stream.read(), path, 'exec'), namespace)
    return namespace, hooks


class Settings(object):
    """settings_service stand-in: one live dict per test, like getComponentDict."""
    def __init__(self, data):
        self.data = data
        self.onModSettingsChanged = module(connect=lambda *args, **kwargs: None, disconnect=lambda *args: None)

    def getComponentDict(self, config):
        return self.data

    def service(self):
        return module(settings_service=self, affects=lambda changes, *keys: True)


class Event(object):
    """Game Event stand-in: handlers attach with += and detach with -=."""
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)
        return self

    def __call__(self, *args, **kwargs):
        for handler in list(self.handlers):
            handler(*args, **kwargs)


def stub(name, **values):
    """A fresh automatic stub (not shared between tests) with some real values."""
    result = _AutoMeta(str(name), (object,), {'_dk_path': name, '__getattr__': _instance_attribute,
                                             '__init__': lambda self, *args, **kwargs: None})
    for key, value in values.items():
        setattr(result, key, value)
    return result
