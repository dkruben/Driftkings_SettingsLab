# -*- coding: utf-8 -*-
"""Central catalog for independent windows and loading-screen surfaces."""
class WindowViews(object):
    def __init__(self):
        self.definitions = []

    def registerModule(self, module):
        self.definitions.extend(getattr(module, 'getWindowViews', lambda: ())())

    def start(self):
        from gui.Scaleform.framework import g_entitiesFactories
        aliases = set()
        for definition in self.definitions:
            if definition.alias in aliases:
                raise ValueError('Duplicate window alias: ' + definition.alias)
            aliases.add(definition.alias)
            if g_entitiesFactories.getSettings(definition.alias) is None:
                g_entitiesFactories.addSettings(definition)

    def stop(self):
        # Window lifetimes belong to the corresponding app/controller. Keep factory
        # records for the client shutdown sequence; never replace another mod's entry.
        self.definitions[:] = []
