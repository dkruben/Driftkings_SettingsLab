# -*- coding: utf-8 -*-
from collections import namedtuple

from AvatarInputHandler.DynamicCameras.ArcadeCamera import ArcadeCamera
from AvatarInputHandler.DynamicCameras.ArtyCamera import ArtyCamera
from AvatarInputHandler.DynamicCameras.StrategicCamera import StrategicCamera
from AvatarInputHandler.control_modes import PostMortemControlMode
from debug_utils import LOG_CURRENT_EXCEPTION

from Driftkings._constants import ARCADE_ZOOM, GLOBAL
from Driftkings.common import logError
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service
from Driftkings.settings.templates.battle.arcade_zoom import ArcadeZoomSettings as Settings

MinMax = namedtuple('MinMax', ('min', 'max'))


class CameraConfigState(object):
    def __init__(self):
        self.initialized = set()

    def prepare(self, camera):
        name = camera.__class__.__name__
        if name in self.initialized:
            return
        camera._baseCfg.clear()
        camera._userCfg.clear()
        camera._cfg.clear()
        self.initialized.add(name)


config = Settings()
camera_state = CameraConfigState()


@override(ArcadeCamera, '_readConfigs')
@override(StrategicCamera, '_readConfigs')
@override(ArtyCamera, '_readConfigs')
def new_read_configs(func, self, dataSection):
    try:
        camera_state.prepare(self)
    except Exception as e:
        logError(config.ID, "Error in new_read_configs: {}", e)
        LOG_CURRENT_EXCEPTION()
    finally:
        return func(self, dataSection)


@override(ArcadeCamera, '_readBaseCfg')
def new_read_arcade_base_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        cfg = self._baseCfg
        cfg['distRange'] = MinMax(settings_service.getComponentDict(config)[ARCADE_ZOOM.MIN], settings_service.getComponentDict(config)[ARCADE_ZOOM.MAX])
        cfg['scrollSensitivity'] = settings_service.getComponentDict(config)[ARCADE_ZOOM.SCROLL_SENSITIVITY]


@override(ArcadeCamera, '_readUserCfg')
def new_read_arcade_user_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        cfg = self._userCfg
        cfg['startDist'] = settings_service.getComponentDict(config)[ARCADE_ZOOM.START_DEAD_DIST]


@override(ArcadeCamera, '_updateProperties')
def new_update_arcade_properties(func, self, state=None):
    try:
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and state is not None:
            dist_range = MinMax(settings_service.getComponentDict(config)[ARCADE_ZOOM.MIN], settings_service.getComponentDict(config)[ARCADE_ZOOM.MAX])
            scroll_sensitivity = settings_service.getComponentDict(config)[ARCADE_ZOOM.SCROLL_SENSITIVITY]
            state = state._replace(distRange=dist_range, scrollSensitivity=scroll_sensitivity)
    except Exception as e:
        logError(config.ID, 'Error in new_update_arcade_properties: {}', e)
        LOG_CURRENT_EXCEPTION()
    finally:
        return func(self, state=state)


@override(StrategicCamera, '_readBaseCfg')
def new_read_strategic_base_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        cfg = self._baseCfg
        cfg['distRange'] = (settings_service.getComponentDict(config)[ARCADE_ZOOM.MIN], settings_service.getComponentDict(config)[ARCADE_ZOOM.MAX])
        cfg['scrollSensitivity'] = settings_service.getComponentDict(config)[ARCADE_ZOOM.SCROLL_SENSITIVITY]


@override(ArtyCamera, '_readBaseCfg')
def new_read_arty_base_cfg(func, self, *args, **kwargs):
    func(self, *args, **kwargs)
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        cfg = self._baseCfg
        cfg['distRange'] = (settings_service.getComponentDict(config)[ARCADE_ZOOM.MIN], settings_service.getComponentDict(config)[ARCADE_ZOOM.MAX])
        cfg['scrollSensitivity'] = settings_service.getComponentDict(config)[ARCADE_ZOOM.SCROLL_SENSITIVITY]


@override(PostMortemControlMode, 'enable')
def new_enable_post_mortem(func, self, **kwargs):
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        if 'postmortemParams' in kwargs:
            kwargs['postmortemParams'] = (self.camera.angles, settings_service.getComponentDict(config)[ARCADE_ZOOM.START_DEAD_DIST])
            kwargs.setdefault('transitionDuration', 1.0)
    return func(self, **kwargs)
