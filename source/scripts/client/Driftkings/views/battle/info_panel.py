# -*- coding: utf-8 -*-
from Driftkings._constants import INFO_PANEL
"""Presentation adapter for InfoPanel; gameplay state stays in its component."""
from Driftkings.settings.service import settings_service, affects
import GUI
import re
from xml.sax.saxutils import escape
from Driftkings.core.overlay import overlays
from Driftkings.core.overlay import ElementType, Align
from gui import g_guiResetters
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.battle.info_panel')


class Flash(object):
    settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self):
        self.name = {}
        self.data = {}
        self.active = False
        self._text = ''

    def startBattle(self):
        if self.active or overlays is None:
            return
        self.active = True
        self.data = self.setup()
        overlays.updated += self.__updatePosition
        if overlays is not None and ElementType is not None:
            self.createObject(ElementType.LABEL, self.data[ElementType.LABEL])
            self.applyConfig()
        g_guiResetters.add(self.screenResize)
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, INFO_PANEL)

    def stopBattle(self):
        if not self.active:
            return
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        g_guiResetters.discard(self.screenResize)
        if overlays is not None:
            overlays.updated -= self.__updatePosition
        if overlays is not None and ElementType is not None:
            self.deleteObject(ElementType.LABEL)
        self.active = False
        self._text = ''
        self.name = {}
        self.data = {}

    def onSettingsChanged(self, component, changes):
        if not self.active:
            return
        if affects(changes, INFO_PANEL.TEXT_LOCK, INFO_PANEL.TEXT_POSITION,
                   INFO_PANEL.TEXT_SHADOW, INFO_PANEL.BACKGROUND_ENABLED, INFO_PANEL.BACKGROUND_ALPHA):
            self.applyConfig()
        if affects(changes, INFO_PANEL.TEXT_FORMAT):
            self.addText(self._text)

    def deleteObject(self, name):
        overlays.remove(self.name[name])

    def createObject(self, name, data):
        overlays.create(self.name[name], name, data)

    def updateObject(self, name, data):
        if self.active:
            overlays.update(self.name[name], data)

    def __updatePosition(self, alias, props):
        if not self.active or str(alias) != str(_component().config.ID):
            return
        position = dict(settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION])
        changed = False
        for key in ('x', 'y'):
            value = props.get(key)
            if value is not None and value != position[key]:
                position[key] = value
                changed = True
        if changed:
            settings_service.apply(_component().config, {INFO_PANEL.TEXT_POSITION: position})

    def setup(self):
        self.name = {ElementType.LABEL: '%s' % _component().config.ID}
        self.data = {
            ElementType.LABEL: {
                'x': 0,
                'y': 0,
                'drag': not settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_LOCK],
                'border': False,
                'alignX': 'center',
                'alignY': 'center',
                'visible': False,
                'text': '',
                'multiline': True,
                'shadow': {
                    'distance': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['distance'],
                    'angle': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['angle'],
                    'color': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['color'],
                    'alpha': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['alpha'],
                    'blurX': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['blurX'],
                    'blurY': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['blurY'],
                    'strength': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['strength'],
                    'quality': settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW]['quality']
                }
            }
        }
        for key, value in settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION].items():
            if key in self.data[ElementType.LABEL]:
                self.data[ElementType.LABEL][key] = value
        return self.data

    def applyConfig(self):
        if overlays is None or ElementType is None or ElementType.LABEL not in self.name:
            return
        shadow = dict(settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_SHADOW])
        label_data = dict(settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION])
        label_data.update({
            'drag': not settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_LOCK],
            'border': False,
            'background': False,
            'alpha': 1.0,
            'customBackground': {
                'color': 0x20252B, 'borderColor': 0x49535D,
                'border': True, 'fill': True, 'thickness': 1,
                'margin': 12, 'ellipseWidth': 10,
                'alpha': max(0.0, min(1.0, settings_service.getComponentDict(_component().config)[INFO_PANEL.BACKGROUND_ALPHA])) if settings_service.getComponentDict(_component().config)[INFO_PANEL.BACKGROUND_ENABLED] else 0.0
            },
            'shadow': shadow
        })
        self.data[ElementType.LABEL].update(label_data)
        self.updateObject(ElementType.LABEL, label_data)

    def addText(self, text=''):
        self._text = text
        # XVM-style tab tags are not native TextField HTML tags.
        text = re.sub(r'<tab\s*/?>', '\t', text, flags=re.IGNORECASE)
        text = re.sub(r'<br\s*/?>', '<br>', text, flags=re.IGNORECASE)
        style = settings_service.getComponentDict(_component().config).get(INFO_PANEL.TEXT_FORMAT, {})
        if style and text:
            # Old defaults used -12 and collapsed 14px text onto adjacent lines.
            # Apply the fix at presentation time, including existing profiles.
            leading = max(0, float(style.get('leading', 0)))
            text = "<textformat leading='%s'><font face='%s' size='%s' color='%s'><p align='%s'>%s</p></font></textformat>" % (
                leading, escape(style.get('font', '$FieldFont'), {"'": '&apos;'}),
                style.get('size', 14), style.get('color', '#FCFCFC'), style.get('align', 'left'), text)
        self.updateObject(ElementType.LABEL, {'text': text})

    def setVisible(self, status):
        data = {'visible': status}
        self.updateObject(ElementType.LABEL, data)

    @staticmethod
    def screenFix(screen, value, align=1):
        if align == 1:
            return float(max(0.0, min(value, screen)))
        if align == -1:
            return float(min(0.0, max(value, -screen)))
        if align == 0:
            scr = screen / 2.0
            return float(max(-scr, min(value, scr)))
        return value

    def screenResize(self):
        if not self.active:
            return
        curScr = GUI.screenResolution()
        scale = max(0.1, float(self.settingsCore.interfaceScale.get()))
        xMo, yMo = curScr[0] / scale, curScr[1] / scale
        x = settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION].get('x', None)
        if settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['alignX'] == Align.LEFT:
            x = self.screenFix(xMo, settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['x'], 1)
        elif settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['alignX'] == Align.RIGHT:
            x = self.screenFix(xMo, settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['x'], -1)
        elif settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['alignX'] == Align.CENTER:
            x = self.screenFix(xMo, settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['x'], 0)
        if x is not None and x != settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['x']:
            settings_service.apply(_component().config, {INFO_PANEL.TEXT_POSITION: {'x': x}}, persist=False)
            self.data[ElementType.LABEL]['x'] = x
        y = settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION].get('y', None)
        if settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['alignY'] == Align.TOP:
            y = self.screenFix(yMo, settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['y'], 1)
        elif settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['alignY'] == Align.BOTTOM:
            y = self.screenFix(yMo, settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['y'], -1)
        elif settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['alignY'] == Align.CENTER:
            y = self.screenFix(yMo, settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['y'], 0)
        if y is not None and y != settings_service.getComponentDict(_component().config)[INFO_PANEL.TEXT_POSITION]['y']:
            settings_service.apply(_component().config, {INFO_PANEL.TEXT_POSITION: {'y': y}}, persist=False)
            self.data[ElementType.LABEL]['y'] = y
        self.updateObject(ElementType.LABEL, {'x': x, 'y': y})

    def getData(self):
        return self.data

    def getNames(self):
        return self.name
