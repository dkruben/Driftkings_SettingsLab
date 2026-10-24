# -*- coding: utf-8 -*-
"""Internal descriptor-aware hook installation; public declarations use core.hooks."""
from functools import partial, wraps
import inspect

from driftkings.core.introspection import find_attr_name

_UNSET = object()


def _descriptor(cls, name):
    # getattr binds classmethods and hides staticmethod descriptors. Inspect the
    # defining class instead, including inherited methods, on Python 2.7 and 3.
    for parent in inspect.getmro(cls):
        if name in parent.__dict__:
            return parent.__dict__[name]
    return getattr(cls, name)


def _metadata(handler):
    while isinstance(handler, partial):
        handler = handler.func
    return handler


def override(obj, prop=_UNSET, getter=None, setter=None, deleter=None):
    if prop is _UNSET:
        if getter is None:
            return partial(override, obj)
        prop = _metadata(getter).__name__
    if inspect.isclass(obj) and not prop.endswith('__') and not hasattr(obj, prop):
        prop = find_attr_name(obj, prop, True)
    original = getattr(obj, prop)
    if isinstance(original, property):
        accessors = []
        for handler, name in ((getter, 'fget'), (setter, 'fset'), (deleter, 'fdel')):
            if handler is not None and not callable(handler):
                raise TypeError('Property handler must be callable: ' + name)
            accessor = getattr(original, name)
            accessors.append(partial(handler, accessor) if handler is not None else accessor)
        setattr(obj, prop, property(*accessors, doc=original.__doc__))
        return getter
    if getter is None:
        return partial(override, obj, prop)
    if not callable(original) or not callable(getter):
        raise TypeError('Hook source and handler must be callable')
    @wraps(_metadata(getter))
    def wrapper(*args, **kwargs):
        # Keep natural tracebacks: retain both the handler and original frames.
        return getter(original, *args, **kwargs)
    installed = wrapper
    if inspect.isclass(obj):
        descriptor = _descriptor(obj, prop)
        if isinstance(descriptor, staticmethod):
            installed = staticmethod(wrapper)
        elif isinstance(descriptor, classmethod):
            installed = classmethod(wrapper)
    setattr(obj, prop, installed)
    return getter


def overrideMethod(cls, method):
    return lambda handler: override(cls, method, handler)


def overrideStaticMethod(cls, method):
    def decorate(handler):
        original = getattr(cls, method)
        @wraps(_metadata(handler))
        def wrapper(*args, **kwargs):
            return handler(original, *args, **kwargs)
        setattr(cls, method, staticmethod(wrapper))
        return handler
    return decorate


def overrideClassMethod(cls, method):
    def decorate(handler):
        original = getattr(cls, method)
        @wraps(_metadata(handler))
        def wrapper(*args, **kwargs):
            return handler(original, *args, **kwargs)
        setattr(cls, method, classmethod(wrapper))
        return handler
    return decorate
