# -*- coding: utf-8 -*-
"""Declare hooks during import; Core installs them and owns their lifetime."""
from functools import partial, wraps
from inspect import isclass


class HookRegistry(object):
    def __init__(self):
        self.pending = {}
        self.active = set()
        self.current = None

    def declare(self, owner, installer, handler):
        owner = self.current or owner
        metadata = handler
        while isinstance(metadata, partial):
            metadata = metadata.func
        @wraps(metadata)
        def guarded(original, *args, **kwargs):
            if owner in self.active:
                return handler(original, *args, **kwargs)
            # Classmethod hooks receive cls explicitly although original is bound.
            if args and isclass(getattr(original, '__self__', None)) and isclass(args[0]):
                return original(*args[1:], **kwargs)
            return original(*args, **kwargs)
        operation = lambda: installer(guarded)
        if owner in self.active:
            operation()
        else:
            self.pending.setdefault(owner, []).append(operation)
        return handler

    def activate(self, owner):
        if owner in self.active:
            return
        self.active.add(owner)
        try:
            for operation in self.pending.pop(owner, ()):
                operation()
        except Exception:
            self.active.discard(owner)
            raise

    def deactivate(self, owner):
        # Leave wrappers in the chain, forwarding originals without mod behavior.
        self.active.discard(owner)
        self.pending.pop(owner, None)


hooks = HookRegistry()
_UNSET = object()


def override(obj, prop=_UNSET, getter=None, setter=None, deleter=None):
    if getter is None and setter is None and deleter is None:
        return lambda handler: override(obj, handler.__name__ if prop is _UNSET else prop, handler)
    from Driftkings.common.utils.monkeypatch import override as install
    if prop is _UNSET:
        prop = getter.__name__
    for kind, handler in (('getter', getter), ('setter', setter), ('deleter', deleter)):
        if handler is not None:
            installer = lambda guarded, kind=kind: install(obj, prop, **{kind: guarded})
            function = handler
            while isinstance(function, partial):
                function = function.func
            hooks.declare(getattr(function, '__module__', hooks.current), installer, handler)
    return getter


def _typed(kind, cls, method):
    def decorator(handler):
        def installer(guarded):
            from Driftkings.common.utils import monkeypatch
            getattr(monkeypatch, kind)(cls, method)(guarded)
        return hooks.declare(handler.__module__, installer, handler)
    return decorator


def overrideMethod(cls, method):
    return _typed('overrideMethod', cls, method)


def overrideStaticMethod(cls, method):
    return _typed('overrideStaticMethod', cls, method)


def overrideClassMethod(cls, method):
    return _typed('overrideClassMethod', cls, method)
