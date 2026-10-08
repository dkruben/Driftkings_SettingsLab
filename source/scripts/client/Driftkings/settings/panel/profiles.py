# -*- coding: utf-8 -*-
"""Portable validated snapshots. Import stages edits; only Apply changes mods."""
import copy
import os
import re

from Driftkings.settings.panel.storage import ConfigStore


class Profiles(object):
    def __init__(self, api):
        self.api = api
        self.store = ConfigStore(os.path.join(api.root, 'profiles'))

    def names(self):
        root = self.store.root
        if not os.path.isdir(root):
            return []
        return sorted(name[:-5] for name in os.listdir(root) if re.match(r'^[A-Za-z0-9_-]{1,64}\.json$', name))

    def name(self, value):
        if not isinstance(value, type(u'')) and not isinstance(value, str):
            raise ValueError('Invalid profile name')
        if not re.match(r'^[A-Za-z0-9_-]{1,64}\Z', value) or value.upper() in ('CON', 'PRN', 'AUX', 'NUL') or re.match(r'^(COM|LPT)[0-9]$', value.upper()):
            raise ValueError('Invalid profile name')
        return value

    def export(self, session):
        return {'format': 'dk.settings.profile', 'version': 1, 'mods': {
            mod.id: {c.id: session.value(mod.id, c.id) for c in mod.value_controls() if not c.secret}
            for mod in self.api.registry.ordered()}}

    def stage(self, session, document):
        if not isinstance(document, dict) or document.get('format') != 'dk.settings.profile' or document.get('version') != 1:
            raise ValueError('Invalid profile format')
        mods = document.get('mods')
        if not isinstance(mods, dict):
            raise ValueError('Invalid profile values')
        drafts = copy.deepcopy(session.drafts)
        for mod_id, values in mods.items():
            if mod_id not in self.api.registry.mods or not isinstance(values, dict):
                raise ValueError('Unknown mod in profile')
            mod = self.api.registry.mods[mod_id]
            for key, value in values.items():
                control = mod.index.get(key)
                if control is None or not control.has_value or control.secret:
                    raise ValueError('Unknown or private setting')
                normalized = control.validate(value)
                if normalized == mod.values[key]:
                    drafts.setdefault(mod_id, {}).pop(key, None)
                else:
                    drafts.setdefault(mod_id, {})[key] = normalized
        session.history.append(copy.deepcopy(session.drafts))
        session.history = session.history[-50:]
        session.drafts = drafts

    def save(self, name, session):
        self.store.write(self.name(name), self.export(session))

    def load(self, name, session):
        self.stage(session, self.store.read(self.name(name)))

    def rename(self, name, target):
        name, target = self.name(name), self.name(target)
        if target in self.names():
            raise ValueError('Profile already exists')
        self.store.write(target, self.store.read(name))
        self.delete(name)

    def delete(self, name):
        name = self.name(name)
        # Keep a bounded backup before deleting this exact profile file.
        data = self.store.read(name)
        self.store.write(name, data)
        os.remove(os.path.join(self.store.root, name + '.json'))
