# -*- coding: utf-8 -*-
"""Resolve declared option relationships and nested enabled sections."""
from Driftkings._constants import GLOBAL, HANDLER_VALUES


def option_dependencies(component, controls):
    fields = dict((c['varName'], c) for c in controls if c.get('varName') is not None)
    result = {}
    for parent, children in HANDLER_VALUES.get(component, {}).items():
        if parent not in fields:
            continue
        choices = fields[parent].get('optionValues')
        for child in children:
            if child not in fields:
                continue
            accepted = children[child] if isinstance(children, dict) else (True,)
            result.setdefault(child, {})[parent] = [choices.index(value) if choices is not None else value
                                                   for value in accepted]
    # Nested JSON sections use their own boolean enabled switch. This covers
    # arbitrary carousel extra fields and player-panel profiles without a list
    # of hardcoded field names or a dependency on their current values.
    paths = dict((name, tuple(item.get('path', (name,)))) for name, item in fields.items())
    for parent, path in paths.items():
        if len(path) < 2 or path[-1] != GLOBAL.ENABLED or fields[parent]['type'] != 'CheckBox':
            continue
        prefix = path[:-1]
        for child, child_path in paths.items():
            if child != parent and len(child_path) > len(prefix) and child_path[:len(prefix)] == prefix:
                result.setdefault(child, {})[parent] = [True]
    return result
