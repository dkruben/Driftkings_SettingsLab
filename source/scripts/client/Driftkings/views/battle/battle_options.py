# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_OPTIONS, GLOBAL
from Driftkings.settings.service import settings_service
"""Presentation adapter for BattleOptions; gameplay state stays in its component."""
import locale
from string import printable
from time import strftime
from PlayerEvents import g_playerEvents
from Driftkings.core.overlay import overlays
from Driftkings.core.overlay import ElementType, Align
from Driftkings.ui import CyclicTimerEvent

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.battle.battle_options')


class BattleClock(object):
    def __init__(self):
        self.coding = None
        self.timerEvent = CyclicTimerEvent(1.0, self.updateTimeData)
        self.active = False

    def createUI(self):
        overlays.create(_component().config.ID, ElementType.LABEL, {'x': 200, 'y': 1, 'alignX': Align.LEFT, 'alignY': Align.TOP, 'text': '', 'border': False, 'limit': False})

    def start(self):
        if self.active:
            return
        self.active = True
        g_playerEvents.onAvatarReady += self.updateDecoder
        if settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED] and settings_service.getComponentDict(_component().config)[BATTLE_OPTIONS.IN_BATTLE]:
            self.timerEvent.start()

    def stop(self):
        if not self.active:
            return
        self.active = False
        g_playerEvents.onAvatarReady -= self.updateDecoder
        self.timerEvent.stop()

    @staticmethod
    def checkDecoder(string):
        for char in string:
            if char not in printable:
                return locale.getpreferredencoding()
        return None

    def updateDecoder(self):
        self.coding = self.checkDecoder(strftime(settings_service.getComponentDict(_component().config)[BATTLE_OPTIONS.FORMAT]))

    def updateTimeData(self):
        time = strftime(settings_service.getComponentDict(_component().config)[BATTLE_OPTIONS.FORMAT])
        if self.coding is not None:
            time = time.decode(self.coding)
        overlays.update(_component().config.ID, {'text': time})


def destroy_clock():
    overlays.remove(_component().config.ID)
