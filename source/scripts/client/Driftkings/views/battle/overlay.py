# -*- coding: utf-8 -*-
"""Native DAAPI transport for the shared Driftkings battle scene."""
from Driftkings._constants import BATTLE_ALIASES
from Driftkings.core.overlay import overlays
from Driftkings.meta.battle.overlay import OverlayMeta

ALIAS = BATTLE_ALIASES.OVERLAY


class OverlayConfig(object):
    data = {'enabled': True}


class OverlayView(OverlayMeta):
    def _populate(self):
        super(OverlayView, self)._populate()
        overlays.attach(self)

    def _dispose(self):
        overlays.detach(self)
        super(OverlayView, self)._dispose()

    def onElementMoved(self, alias, x, y):
        overlays.moved(self, alias, x, y)
