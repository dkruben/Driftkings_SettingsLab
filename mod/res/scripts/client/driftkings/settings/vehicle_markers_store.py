# -*- coding: utf-8 -*-
import copy
import os

from driftkings.core.vehicle_markers.config import prepare
from driftkings.core.vehicle_markers.references import defaults as merge_defaults
from driftkings.core.vehicle_markers.schema import FILES, join, legacy_general, split
from driftkings.settings.store import JsonDocuments, read_object, recover_file

# The earlier feature-split layout; only its general switches are carried over.
LEGACY_FILES = ('general.json', 'markers.json', 'fields.json', 'colors.json',
                'healthbar.json', 'damage.json', 'icons.json')


class VehicleMarkersStore(JsonDocuments):
    def __init__(self, directory):
        super(VehicleMarkersStore, self).__init__(directory, FILES)

    def path(self, name):
        return os.path.join(self.directory, name)

    def read(self, names):
        documents = {}
        for name in names:
            recover_file(self.path(name))
            if os.path.isfile(self.path(name)):
                documents[name] = read_object(self.path(name))
        return documents

    def convert_legacy(self):
        """Publish marker files from the seven-file layout once; the old files are kept as .v2.bak."""
        if os.path.isfile(self.path(FILES[1])) or not os.path.isfile(self.path('general.json')):
            return None
        legacy = self.read(LEGACY_FILES)
        for name in LEGACY_FILES:
            if os.path.isfile(self.path(name)) and not os.path.exists(self.path(name) + '.v2.bak'):
                os.rename(self.path(name), self.path(name) + '.v2.bak')
        return {'markers.json': {'markers': legacy_general(legacy)}}

    def load(self):
        from driftkings.settings.settings_data import defaults
        self.recover()
        documents = self.convert_legacy()
        if documents is None:
            documents = self.read(FILES)
        selected = join(documents)
        result = merge_defaults(defaults('vehicle_markers'), dict((key, value) for key, value in selected.items()
                                                                 if key == 'enabled' or value))
        prepare(result)
        if any(not os.path.isfile(self.path(name)) for name in FILES):
            self.save(result)
        return result

    def save(self, data):
        prepare(data)
        self.publish([(self.path(name), part) for name, part in split(data)])
        return copy.deepcopy(data)
