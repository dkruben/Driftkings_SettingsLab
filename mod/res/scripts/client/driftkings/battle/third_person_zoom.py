# -*- coding: utf-8 -*-
"""Independent arcade, postmortem and artillery camera configuration."""
from AvatarInputHandler.control_modes import PostMortemControlMode
from AvatarInputHandler.DynamicCameras.ArcadeCamera import ArcadeCamera
from AvatarInputHandler.DynamicCameras.ArtyCamera import ArtyCamera
from AvatarInputHandler.DynamicCameras.StrategicCamera import StrategicCamera

from driftkings._constants import MinMax
from driftkings.core.camera_settings import options
from driftkings.core.hooks import override
from driftkings.logger import get_logger
from driftkings.settings.definitions.battle.third_person_zoom import ThirdPersonZoomSettings as Settings
from driftkings.settings.service import settings_service

LOG = get_logger('Driftkings.Camera')
config = Settings()


def _options(mode):
    return options(settings_service.getComponentDict(config), mode)


def _arcadeMode(camera):
    return 'postmortem' if getattr(camera, '_ArcadeCamera__postmortemMode', False) else 'arcade'


@override(ArcadeCamera, 'create')
def new_create_arcade(original, self, onChangeControlMode=None, postmortemMode=False, smartPointCalculator=True):
    # Native create sets this flag after construction/config reading. Select the
    # correct profile before it consumes startDist or updates camera properties.
    self._ArcadeCamera__postmortemMode = postmortemMode
    data = _options(_arcadeMode(self))
    if data is not None:
        limits = MinMax(data['min'], data['max'])
        self._cfg.update(startDist=data['startDist'], distRange=limits,
                         scrollSensitivity=data['scrollSensitivity'])
        self._distRange = limits
    result = original(self, onChangeControlMode, postmortemMode, smartPointCalculator)
    if data is not None:
        self._updateProperties()
    return result


@override(ArcadeCamera, '_readBaseCfg')
def new_read_arcade_base_cfg(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    data = _options(_arcadeMode(self))
    if data is not None:
        self._baseCfg['distRange'] = MinMax(data['min'], data['max'])
        self._baseCfg['scrollSensitivity'] = data['scrollSensitivity']
    return result


@override(ArcadeCamera, '_readUserCfg')
def new_read_arcade_user_cfg(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    data = _options(_arcadeMode(self))
    if data is not None:
        self._userCfg['startDist'] = data['startDist']
    return result


@override(ArcadeCamera, '_updateProperties')
def new_update_arcade_properties(original, self, state=None):
    data = _options(_arcadeMode(self))
    if data is not None:
        limits = MinMax(data['min'], data['max'])
        if state is not None:
            state = state._replace(distRange=limits, scrollSensitivity=data['scrollSensitivity'])
        else:
            self._cfg.update(distRange=limits, scrollSensitivity=data['scrollSensitivity'])
    return original(self, state=state)


def _readArtillery(original, camera, mode, *args, **kwargs):
    result = original(camera, *args, **kwargs)
    data = _options(mode)
    if data is not None:
        camera._baseCfg['distRange'] = (data['min'], data['max'])
        camera._baseCfg['scrollSensitivity'] = data['scrollSensitivity']
    # With useClientDefaults, leave the values just read by WG untouched.
    return result


@override(StrategicCamera, '_readBaseCfg')
def new_read_strategic_base_cfg(original, self, *args, **kwargs):
    return _readArtillery(original, self, 'strategic', *args, **kwargs)


@override(ArtyCamera, '_readBaseCfg')
def new_read_arty_base_cfg(original, self, *args, **kwargs):
    return _readArtillery(original, self, 'arty', *args, **kwargs)


@override(PostMortemControlMode, 'enable')
def new_enable_post_mortem(original, self, **kwargs):
    data = _options('postmortem')
    if data is not None and 'postmortemParams' in kwargs:
        kwargs['postmortemParams'] = (self.camera.angles, data['startDist'])
        kwargs.setdefault('transitionDuration', 1.0)
    return original(self, **kwargs)
