# -*- coding: utf-8 -*-
"""Presentation adapter for MarksOnGunBattle; gameplay state stays in its component."""
from __future__ import print_function

from importlib import import_module

import BattleReplay
import GUI
from gui import g_guiResetters
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from Driftkings._constants import GLOBAL, MARKS_ON_GUN_BATTLE
from Driftkings.core.overlay import ElementType, Align
from Driftkings.core.overlay import overlays
from Driftkings.settings.service import settings_service


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.battle.gun_marks')


class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        self.active = False
        self.name = {}
        self.data = {}

    def startBattle(self):
        if self.active:
            return
        if not settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED]:
            return
        if BattleReplay.isPlaying() and not settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.SHOW_IN_REPLAY]:
            return
        self.active = True
        self.data = self.setup()
        overlays.updated += self.__updatePosition
        self.createObject(ElementType.LABEL, self.data[ElementType.LABEL])
        self.updateObject(ElementType.LABEL, {'background': settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.BACKGROUND]})
        g_guiResetters.add(self.screenResize)
        self.setupSize()

    def stopBattle(self):
        if not self.active:
            return
        self.active = False
        g_guiResetters.discard(self.screenResize)
        overlays.updated -= self.__updatePosition
        self.deleteObject(ElementType.LABEL)

    def deleteObject(self, name):
        overlays.remove(self.name[name])

    def createObject(self, name, data):
        overlays.create(self.name[name], name, data)

    def updateObject(self, name, data):
        overlays.update(self.name[name], data)

    def animateObject(self, name, data, time=1.0):
        overlays.animate(self.name[name], time, data, True)

    # noinspection PyTypeChecker
    def __updatePosition(self, alias, props):
        if str(alias) != str(_component().config.ID):
            return
        panel = settings_service.getSetting(_component().config, MARKS_ON_GUN_BATTLE.PANEL)
        changes = dict((key, props[key]) for key in ('x', 'y') if props.get(key) is not None)
        settings_service.apply(_component().config, {MARKS_ON_GUN_BATTLE.PANEL: changes})
        for key in ('x', 'y'):
            self.data[ElementType.LABEL][key] = panel[key]
        self.setupSize()

    def setup(self):
        self.name = {ElementType.LABEL: '%s' % _component().config.ID}
        self.data = {
            ElementType.LABEL: {
                'index': 10000,
                'x': -226.0,
                'y': -226.0,
                'width': 183.0,
                'height': 50.0,
                'drag': True,
                'border': True,
                'alignX': 'left',
                'alignY': 'bottom',
                'visible': True,
                'text': '',
                'shadow': {'distance': 0, 'angle': 0, 'color': 0x000000, "alpha": 90, 'blurX': 1, 'blurY': 1, 'strength': 3000, 'quality': 1}
            },
        }
        for key, value in settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL].items():
            if key in self.data[ElementType.LABEL]:
                self.data[ElementType.LABEL][key] = value
        return self.data

    def setupSize(self, h=None, w=None):
        height = settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL_SIZE].get('heightNormal', 50.0) if not _component().worker.altMode else settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL_SIZE].get('heightAlt', 80.0)
        width = settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL_SIZE].get('widthNormal', 163.0) if not _component().worker.altMode else settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL_SIZE].get('widthAlt', 163.0)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] == 1:
            height = 30.0 if not _component().worker.altMode else 45.0
            width = 152.0 if not _component().worker.altMode else 152.0
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] == 2:
            height = 30.0 if not _component().worker.altMode else 50.0
            width = 130.0 if not _component().worker.altMode else 130.0
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] == 3:
            height = 70.0 if not _component().worker.altMode else 100.0
            width = 144.0 if not _component().worker.altMode else 144.0
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] == 4:
            height = 50.0 if not _component().worker.altMode else 80.0
            width = 163.0 if not _component().worker.altMode else 163.0

        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] in (5, 6, 7, 8):
            height = 82.0 if not _component().worker.altMode else 82.0
            width = 343.0 if not _component().worker.altMode else 343.0
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] == 9:
            height = 42.0 if not _component().worker.altMode else 42.0
            width = 54.0 if not _component().worker.altMode else 115.0
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] == 10:
            height = 50.0 if not _component().worker.altMode else 90.0
            width = 183.0 if not _component().worker.altMode else 183.0
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] == 11:
            height = 130.0 if not _component().worker.altMode else 130.0
            width = 160.0 if not _component().worker.altMode else 160.0
        if h is not None and w is not None:
            height = h
            width = w
        height = height * settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] / 100.0
        width = width * settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] / 100.0

        for name in self.data:
            self.data[name]['height'] = height
            self.data[name]['width'] = width
        self.data[ElementType.LABEL]['height'] = height
        self.data[ElementType.LABEL]['width'] = width
        self.screenResize()
        x = self.data[ElementType.LABEL]['x']
        y = self.data[ElementType.LABEL]['y']
        data = {'height': height, 'width': width, 'x': x, 'y': y}
        self.updateObject(ElementType.LABEL, data)

    @staticmethod
    def textRepSize(message):
        mod = False
        text = ''
        count = 0
        for ids in message.split('\"'):
            if count:
                text += '"'
            if mod:
                text += '%s' % (int(ids) * settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.BATTLE_MESSAGE_SIZE_IN_PERCENT] / 100)
                mod = False
            else:
                text += '%s' % ids
            if 'size=' in ids:
                mod = True
            count += 1
        return text

    def set_text(self, text):
        txt = '<font face="%s" color="#FFFFFF" vspace="-3" align="baseline" >%s</font>' % (settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.FONT], text)
        self.updateObject(ElementType.LABEL, {'text': self.textRepSize(txt)})

    def setVisible(self, status):
        data = {'visible': status}
        self.updateObject(ElementType.LABEL, data)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.UI] in (5, 6, 7, 8, 11):
            data = {'background': False}
        else:
            data = {'background': settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.BACKGROUND]}
        self.updateObject(ElementType.LABEL, data)

    @staticmethod
    def screenFix(screen, value, mod, align=1):
        if align == 1:
            if value + mod > screen:
                return float(max(0, screen - mod))
            if value < 0:
                return 0.0
        if align == -1:
            if value - mod < -screen:
                return min(0, -screen + mod)
            if value > 0:
                return 0.0
        if align == 0:
            scr = screen / 2.0
            if value < scr:
                return float(scr - mod)
            if value > -scr:
                return float(-scr)
        return value

    # noinspection PyTypeChecker
    # noinspection PyArgumentEqualDefault
    def screenResize(self):
        curScr = GUI.screenResolution()
        scale = float(self.settingsCore.interfaceScale.get())
        xMo, yMo = curScr[0] / scale, curScr[1] / scale
        x = settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL].get('x', None)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['alignX'] == Align.LEFT:
            x = self.screenFix(xMo, settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['x'], settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['width'], 1)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['alignX'] == Align.RIGHT:
            x = self.screenFix(xMo, settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['x'], settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['width'], -1)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['alignX'] == Align.CENTER:
            x = self.screenFix(xMo, settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['x'], settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['width'], 0)
        if x is not None:
            if x != settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['x']:
                settings_service.apply(_component().config, {MARKS_ON_GUN_BATTLE.PANEL: {'x': x}}, persist=False)
                self.data[ElementType.LABEL]['x'] = x
        y = settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL].get('y', None)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['alignY'] == Align.TOP:
            y = self.screenFix(yMo, settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['y'], settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['height'], 1)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['alignY'] == Align.BOTTOM:
            y = self.screenFix(yMo, settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['y'], settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['height'], -1)
        if settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['alignY'] == Align.CENTER:
            y = self.screenFix(yMo, settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['y'], settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['height'], 0)
        if y is not None:
            if y != settings_service.getComponentDict(_component().config)[MARKS_ON_GUN_BATTLE.PANEL]['y']:
                settings_service.apply(_component().config, {MARKS_ON_GUN_BATTLE.PANEL: {'y': y}}, persist=False)
                self.data[ElementType.LABEL]['y'] = y
        self.updateObject(ElementType.LABEL, {'x': x, 'y': y})

    def getData(self):
        return self.data

    def getNames(self):
        return self.name
