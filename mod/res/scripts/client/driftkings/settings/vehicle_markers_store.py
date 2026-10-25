# -*- coding: utf-8 -*-
import copy
import os

from driftkings.core.vehicle_markers.config import prepare
from driftkings.settings.store import JsonDocuments, merge, read_object, recover_file

PARTS = (('markers.json', 'markers'), ('fields.json', 'customFields'), ('colors.json', 'colors'),
         ('healthbar.json', 'healthBar'), ('damage.json', 'damageText'), ('icons.json', 'icons'))
FILES = ('general.json',) + tuple(name for name, key in PARTS)


def split(data):
    general = copy.deepcopy(data)
    parts = [dict(((key, general.pop(key)),)) for name, key in PARTS]
    return [general] + parts


class VehicleMarkersStore(JsonDocuments):
    def __init__(self, directory):
        super(VehicleMarkersStore, self).__init__(directory, FILES)

    def load(self):
        from driftkings.settings.settings_data import defaults
        self.recover()
        result = {}
        for name, initial in zip(FILES, split(defaults('vehicle_markers'))):
            path = os.path.join(self.directory, name)
            recover_file(path)
            part = merge(initial, read_object(path)) if os.path.isfile(path) else initial
            result.update(part)
        prepare(result)
        if any(not os.path.isfile(os.path.join(self.directory, name)) for name in FILES):
            self.save(result)
        return result

    def save(self, data):
        prepare(data)
        self.publish([(os.path.join(self.directory, name), part) for name, part in zip(FILES, split(data))])
        return copy.deepcopy(data)
