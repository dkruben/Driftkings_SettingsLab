# -*- coding: utf-8 -*-
"""Central catalog for independent windows and loading-screen surfaces."""
class WindowViews(object):
    def __init__(self):
        self.definitions = []

    def registerModule(self, module):
        self.definitions.extend(getattr(module, 'getWindowViews', lambda: ())())

    def start(self):
        aliases = set()
        for definition in self.definitions:
            if definition.alias in aliases:
                raise ValueError('Duplicate window alias: ' + definition.alias)
            aliases.add(definition.alias)
        if not self.definitions:
            return
        from helpers import dependency
        from skeletons.gui.impl import IGuiLoader
        factory = dependency.instance(IGuiLoader).entitiesFactory
        for definition in self.definitions:
            if factory.getSettings(definition.alias) is None:
                factory.addSettings(definition)

    def stop(self):
        # Window lifetimes belong to the corresponding app/controller. Keep factory
        # records for the client shutdown sequence; never replace another mod's entry.
        self.definitions[:] = []
