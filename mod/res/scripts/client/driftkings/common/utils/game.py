# -*- coding: utf-8 -*-
"""Keyboard combinations shared by the battle components."""
import BigWorld

__all__ = ('checkKeys',)


def checkKeys(keys, key=None):
    keySets = [data if not isinstance(data, int) else (data,) for data in keys]
    return (bool(keys) and all(any(BigWorld.isKeyDown(x) for x in keySet) for keySet in keySets) and (key is None or any(key in keySet for keySet in keySets)))
