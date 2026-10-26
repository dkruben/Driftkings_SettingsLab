# -*- coding: utf-8 -*-
import copy
import os
import shutil

from driftkings.core.vehicle_markers.config import prepare
from driftkings.core.vehicle_markers.layouts import migrate
from driftkings.core.vehicle_markers.references import defaults as merge_defaults
from driftkings.settings.store import JsonDocuments, read_object, recover_file

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
        raw = {}
        for name in FILES:
            path = os.path.join(self.directory, name)
            recover_file(path)
            if os.path.isfile(path):
                raw.update(read_object(path))
        converted = migrate(raw)
        selected = dict((key, converted[key]) for key in raw)
        selected['schemaVersion'] = 2
        result = merge_defaults(defaults('vehicle_markers'), selected)
        prepare(result)
        legacy = bool(raw) and raw.get('schemaVersion', 1) == 1
        if legacy:
            for name in FILES:
                path = os.path.join(self.directory, name)
                if os.path.isfile(path) and not os.path.exists(path + '.v1.bak'):
                    shutil.copy2(path, path + '.v1.bak')
        if legacy or any(not os.path.isfile(os.path.join(self.directory, name)) for name in FILES):
            self.save(result)
        return result

    def save(self, data):
        data = migrate(data)
        prepare(data)
        self.publish([(os.path.join(self.directory, name), part) for name, part in zip(FILES, split(data))])
        return copy.deepcopy(data)
