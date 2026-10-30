# -*- coding: utf-8 -*-
"""Position, shadow and lifecycle shared by configurable battle text labels."""
from driftkings.flash.core import ElementType, overlays
from driftkings.settings.service import settings_service


class BattleLabel(object):
    def __init__(self, section, settings, position_key):
        self.section = section
        self._settings = settings
        self._positionKey = position_key
        self.setup()
        overlays.updated += self._updatePosition

    def _layout(self):
        data = settings_service.getComponentDict(self._settings)
        return dict(data[self._positionKey], drag=not data['textLock'], border=not data['textLock'])

    def setup(self):
        overlays.create(self.section, ElementType.LABEL, dict(self._layout(), limit=True))
        self.createBox()

    def onApplySettings(self):
        overlays.update(self.section, self._layout())

    def createBox(self):
        shadow = settings_service.getComponentDict(self._settings)['textShadow']
        if shadow['enabled']:
            overlays.update(self.section, {'shadow': shadow})

    def destroy(self):
        overlays.updated -= self._updatePosition
        overlays.remove(self.section)

    def _updatePosition(self, alias, data):
        if alias == self.section:
            settings_service.apply(self._settings, {self._positionKey: data})


class CachedBattleLabel(BattleLabel):
    """Borderless label with cached content and a settings subscription."""
    def __init__(self, section, settings, position_key, settings_component):
        self._lastText = None
        self._lastVisible = None
        self._destroyed = False
        super(CachedBattleLabel, self).__init__(section, settings, position_key)
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, settings_component)

    def _layout(self):
        result = super(CachedBattleLabel, self)._layout()
        result['border'] = False
        return result

    def destroy(self):
        if self._destroyed:
            return
        self._destroyed = True
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        super(CachedBattleLabel, self).destroy()
        self._lastText = self._lastVisible = None
