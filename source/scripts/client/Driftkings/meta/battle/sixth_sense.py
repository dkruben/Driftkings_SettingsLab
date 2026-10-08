# -*- coding: utf-8 -*-
from .base import BattleMeta


class SixthSenseMeta(BattleMeta):
    FLASH_CLASS = 'driftkings.battle.components.sixth_sense.SixthSenseUI'

    def as_showS(self, seconds):
        if self._isDAAPIInited():
            return self.flashObject.as_show(seconds)

    def as_hideS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_hide()

    def getTimerString(self, timeLeft):
        raise NotImplementedError

    def playSound(self):
        raise NotImplementedError
