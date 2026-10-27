# -*- coding: utf-8 -*-
from functools import partial

import BigWorld
from BigWorld import callback

__all__ = ('BigWorld_callback', 'checkKeys', 'refreshCurrentVehicle', 'Sound',)


def BigWorld_callback(delay, func, *args, **kwargs):
    return callback(delay, partial(func, *args, **kwargs))


def checkKeys(keys, key=None):
    keySets = [data if not isinstance(data, int) else (data,) for data in keys]
    return (bool(keys) and all(any(BigWorld.isKeyDown(x) for x in keySet) for keySet in keySets) and (key is None or any(key in keySet for keySet in keySets)))


VKEY_ALT, VKEY_CONTROL, VKEY_SHIFT = range(-1, -4, -1)


def refreshCurrentVehicle():
    from CurrentVehicle import g_currentPreviewVehicle, g_currentVehicle
    if g_currentPreviewVehicle.item:
        from gui.shared.personality import ServicesLocator as SL
        outfit = None
        entity = SL.hangarSpace.getVehicleEntity()
        if entity and entity.appearance:
            outfit = entity.appearance.outfit
        g_currentPreviewVehicle.hangarSpace.updatePreviewVehicle(g_currentPreviewVehicle.item, outfit)
    else:
        g_currentVehicle.refreshModel()
    from HeroTank import HeroTank
    for entity in HeroTank.allCameraObjects:
        if isinstance(entity, HeroTank):
            entity.recreateVehicle()


class Sound(object):
    def __init__(self, sound_path):
        import SoundGroups
        self.__sndPath = sound_path
        self.__sndTick = SoundGroups.g_instance.getSound2D(self.__sndPath)
        self.__isPlaying = True
        self.stop()

    @property
    def isPlaying(self):
        return self.__isPlaying

    @property
    def sound(self):
        return self.__sndTick

    def play(self):
        self.stop()
        if self.__sndTick:
            self.__sndTick.play()
        self.__isPlaying = True

    def stop(self):
        if self.__sndTick:
            self.__sndTick.stop()
        self.__isPlaying = False
