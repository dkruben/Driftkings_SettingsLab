# -*- coding: utf-8 -*-
"""Minimap JSON documents, with recoverable publication of all four files."""
import copy
import os

from driftkings.settings.store import JsonDocuments, merge, read_object, recover_file

FILES = ('minimap.json', 'minimap_labels.json', 'minimap_circles.json', 'minimap_lines.json')
SECTIONS = (None, ('labels', 'health', 'lostMarker'), ('circles', 'extraCircles'), ('lines',))


def split(data):
    general = copy.deepcopy(data)
    parts = []
    for keys in SECTIONS[1:]:
        parts.append(dict((key, general.pop(key)) for key in keys))
    return [general] + parts


class MinimapStore(JsonDocuments):
    def __init__(self, directory):
        super(MinimapStore, self).__init__(directory, FILES)

    def load(self, initial):
        from driftkings.core.minimap import validate
        from driftkings.settings.loader import validate_types
        self.recover()
        data = {}
        for name, defaults in zip(FILES, split(initial)):
            path = os.path.join(self.directory, name)
            recover_file(path)
            part = merge(defaults, read_object(path)) if os.path.isfile(path) else defaults
            validate_types(defaults, part, name)
            data.update(part)
        validate(data)
        if any(not os.path.isfile(os.path.join(self.directory, name)) for name in FILES):
            self.save(data)
        return data

    def save(self, data):
        from driftkings.core.minimap import validate
        validate(data)
        self.publish([(os.path.join(self.directory, name), part) for name, part in zip(FILES, split(data))])
        return copy.deepcopy(data)
