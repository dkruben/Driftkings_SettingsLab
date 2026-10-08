# -*- coding: utf-8 -*-
"""Application-space lifecycle shared by login, lobby and battle controllers."""
import logging
LOG = logging.getLogger('Driftkings.Contexts')


class Contexts(object):
    def __init__(self, modules, loader=None):
        self.modules = modules
        self.loader = loader
        self.current = None
        self.active = False

    def start(self):
        if self.active:
            return
        if self.loader is None:
            from gui.shared.personality import ServicesLocator
            self.loader = ServicesLocator.appLoader
        self.loader.onGUISpaceEntered += self.enter
        self.loader.onGUISpaceLeft += self.leave
        self.active = True
        self.enter(self.loader.getSpaceID())

    def notify(self, method, space, reverse=False):
        modules = reversed(self.modules) if reverse else self.modules
        for name, module in modules:
            callback = getattr(module, method, None)
            if callback is not None:
                try:
                    callback(space)
                except Exception:
                    LOG.exception('%s failed for %s', method, name)

    def enter(self, space):
        if space is None or space == self.current:
            return
        if self.current is not None:
            self.leave(self.current)
        self.current = space
        self.notify('onContextEntered', space)

    def leave(self, space):
        if space != self.current or self.current is None:
            return
        self.current = None
        self.notify('onContextLeft', space, reverse=True)

    def stop(self):
        if not self.active:
            return
        self.leave(self.current)
        self.loader.onGUISpaceEntered -= self.enter
        self.loader.onGUISpaceLeft -= self.leave
        self.active = False
