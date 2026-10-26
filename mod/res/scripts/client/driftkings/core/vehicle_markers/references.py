# -*- coding: utf-8 -*-
"""Local reusable definitions only; no external files, code execution or mutable aliases."""
import copy
import re

from driftkings.core.vehicle_markers.layouts import merge

PATH = re.compile(r'^def(?:\.[A-Za-z0-9_-]+)+$')
try:
    STRING = basestring
except NameError:
    STRING = str


def resolve(value, document=None):
    document = value if document is None else document
    budget = [100000]

    def target(path, trail, depth):
        if not isinstance(path, STRING) or not PATH.match(path) or path in trail:
            raise ValueError('Invalid or circular marker reference: ' + str(path))
        item = document
        for key in path.split('.'):
            if not isinstance(item, dict) or key not in item:
                raise ValueError('Unknown marker reference: ' + path)
            item = item[key]
        return visit(item, trail + (path,), depth + 1)

    def visit(item, trail, depth):
        budget[0] -= 1
        if budget[0] < 0 or depth > 48:
            raise ValueError('Marker reference expansion exceeds limits')
        if isinstance(item, dict):
            if '$ref' in item:
                pointer = item['$ref']
                if isinstance(pointer, dict):
                    if set(pointer) != set(('path',)):
                        raise ValueError('Expected a local reference path')
                    pointer = pointer['path']
                base = target(pointer, trail, depth)
                override = dict((key, visit(child, trail, depth + 1)) for key, child in item.items() if key != '$ref')
                if override and not isinstance(base, dict):
                    raise ValueError('Reference overrides require an object')
                return merge(base, override) if override else copy.deepcopy(base)
            return dict((key, visit(child, trail, depth + 1)) for key, child in item.items())
        if isinstance(item, list):
            return [visit(child, trail, depth + 1) for child in item]
        if isinstance(item, STRING) and item.startswith('${') and item.endswith('}'):
            return target(item[2:-1], trail, depth)
        return copy.deepcopy(item)

    return visit(value, (), 0)


def defaults(base, value):
    """Do not turn defaults into explicit overrides of a referenced template."""
    if isinstance(value, dict):
        if '$ref' in value:
            return copy.deepcopy(value)
        result = copy.deepcopy(base) if isinstance(base, dict) else {}
        for key, child in value.items():
            result[key] = defaults(result.get(key), child)
        return result
    return copy.deepcopy(value)
