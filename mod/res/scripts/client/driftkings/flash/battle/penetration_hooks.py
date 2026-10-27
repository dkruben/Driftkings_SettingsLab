# -*- coding: utf-8 -*-
from gui.Scaleform.daapi.view.battle.shared.crosshair import plugins
from gui.Scaleform.genConsts.CROSSHAIR_VIEW_ID import CROSSHAIR_VIEW_ID

from driftkings._constants import GLOBAL, PENETRATION_INDICATOR
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.hooks import override
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.ui import g_events

LOG = get_logger('driftkings.battle.penetration_indicator')

def configure(section, resolver, allied_resolver):
    global config, _ShotResult, _ShotResultAll
    config, _ShotResult, _ShotResultAll = section, resolver, allied_resolver


class ShotResultIndicatorPlugin(plugins.ShotResultIndicatorPlugin):

    def __init__(self, parentObj):
        super(ShotResultIndicatorPlugin, self).__init__(parentObj)
        self.__player = getPlayer()
        self.__data = None
        self.__resolver = _ShotResultAll if settings_service.getComponentDict(config)[PENETRATION_INDICATOR.DISPLAY_ON_ALLIES] else _ShotResult

    def _getShotResolverResult(self, gunMarker):
        # The client's own resolver decides the colour; allies are included when the option asks for it.
        team = 0 if self.__resolver is _ShotResultAll else self.__playerTeam
        return self.__shotResultResolver.getShotResult(gunMarker, team, self.__piercingMultiplier)

    def __onGunMarkerStateChanged(self, markerType, gunMarkerState, supportMarkersInfo):
        if not self.__isEnabled:
            return
        shot_result = self._getShotResult(gunMarkerState, supportMarkersInfo)
        data = self.__resolver._getShotResult(gunMarkerState, self.__piercingMultiplier, self.__player)
        if shot_result in self.__colors:
            color = self.__colors[shot_result]
            if self.__cache[markerType] != shot_result and self._parentObj.setGunMarkerColor(markerType, color):
                self.__cache[markerType] = shot_result
                g_events.onMarkerColorChanged(color)
            if self.__data != data:
                self.__data = data
                g_events.onArmorChanged(data)

    def __setMapping(self, keys):
        super(ShotResultIndicatorPlugin, self).__setMapping(keys)
        self.__mapping[CROSSHAIR_VIEW_ID.STRATEGIC] = True

    def start(self):
        super(ShotResultIndicatorPlugin, self).start()
        self.__player = getPlayer()


@override(plugins, 'createPlugins')
def createPlugins(func, *args):
    _plugins = func(*args)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        _plugins['shotResultIndicator'] = ShotResultIndicatorPlugin
    return _plugins


