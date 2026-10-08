# -*- coding: utf-8 -*-
"""Position, shadow and lifecycle shared by configurable battle text labels."""
from Driftkings.core.overlay import overlays, ElementType
from Driftkings.settings.service import settings_service


class BattleLabel(object):
    def __init__(self, ID, component, position_key):
        self.ID = ID
        self._component = component
        self._positionKey = position_key
        self.setup()
        overlays.updated += self._updatePosition

    def _layout(self):
        data = settings_service.getComponentDict(self._component().config)
        return dict(data[self._positionKey], drag=not data['textLock'], border=not data['textLock'])

    def setup(self):
        overlays.create(self.ID, ElementType.LABEL, dict(self._layout(), limit=True))
        self.createBox()

    def onApplySettings(self):
        overlays.update(self.ID, self._layout())

    def createBox(self):
        shadow = settings_service.getComponentDict(self._component().config)['textShadow']
        if shadow['enabled']:
            overlays.update(self.ID, {'shadow': shadow})

    def destroy(self):
        overlays.updated -= self._updatePosition
        overlays.remove(self.ID)

    def _updatePosition(self, alias, data):
        if alias == self.ID:
            settings_service.apply(self._component().config, {self._positionKey: data})
