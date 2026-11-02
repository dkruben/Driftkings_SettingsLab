# -*- coding: utf-8 -*-
"""Presentation adapter for InfoPanel; gameplay state stays in its component."""
from importlib import import_module
import re
from xml.sax.saxutils import escape

import GUI
from gui import g_guiResetters
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore

from driftkings._constants import TARGET_INFORMATION
from driftkings.flash.core import Align, ElementType, overlays
from driftkings.settings.service import affects, settings_service


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.battle.target_information')


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
        if ElementType is not None:
            self.createObject(ElementType.LABEL, self.data[ElementType.LABEL])
            self.applyConfig()
        g_guiResetters.add(self.screenResize)
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, TARGET_INFORMATION)

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
        if affects(changes, TARGET_INFORMATION.TEXT_LOCK, TARGET_INFORMATION.TEXT_POSITION,
                   TARGET_INFORMATION.TEXT_SHADOW, TARGET_INFORMATION.BACKGROUND_ENABLED,
                   TARGET_INFORMATION.BACKGROUND_ALPHA):
            self.applyConfig()
        if affects(changes, TARGET_INFORMATION.TEXT_FORMAT):
            self.addText(self._text)

    def deleteObject(self, name):
        overlays.remove(self.name[name])

    def createObject(self, name, data):
        overlays.create(self.name[name], name, data)

    def updateObject(self, name, data):
        if self.active:
            overlays.update(self.name[name], data)

    def __updatePosition(self, alias, props):
        if not self.active or str(alias) != str(_component().target_information_settings.NAME):
            return
        position = dict(settings_service.getComponentDict(_component().target_information_settings)[TARGET_INFORMATION.TEXT_POSITION])
        changed = False
        for key in ('x', 'y'):
            value = props.get(key)
            if value is not None and value != position[key]:
                position[key] = value
                changed = True
        if changed:
            settings_service.apply(_component().target_information_settings,
                                   {TARGET_INFORMATION.TEXT_POSITION: position})

    def setup(self):
        settings = settings_service.getComponentDict(_component().target_information_settings)
        self.name = {ElementType.LABEL: '%s' % _component().target_information_settings.NAME}
        self.data = {
            ElementType.LABEL: {
                'x': 0,
                'y': 0,
                'drag': not settings[TARGET_INFORMATION.TEXT_LOCK],
                'border': False,
                'alignX': 'center',
                'alignY': 'center',
                'visible': False,
                'text': '',
                'multiline': True,
                'shadow': {
                    'distance': settings[TARGET_INFORMATION.TEXT_SHADOW]['distance'],
                    'angle': settings[TARGET_INFORMATION.TEXT_SHADOW]['angle'],
                    'color': settings[TARGET_INFORMATION.TEXT_SHADOW]['color'],
                    'alpha': settings[TARGET_INFORMATION.TEXT_SHADOW]['alpha'],
                    'blurX': settings[TARGET_INFORMATION.TEXT_SHADOW]['blurX'],
                    'blurY': settings[TARGET_INFORMATION.TEXT_SHADOW]['blurY'],
                    'strength': settings[TARGET_INFORMATION.TEXT_SHADOW]['strength'],
                    'quality': settings[TARGET_INFORMATION.TEXT_SHADOW]['quality']
                }
            }
        }
        for key, value in settings[TARGET_INFORMATION.TEXT_POSITION].items():
            if key in self.data[ElementType.LABEL]:
                self.data[ElementType.LABEL][key] = value
        return self.data

    def applyConfig(self):
        if overlays is None or ElementType is None or ElementType.LABEL not in self.name:
            return
        shadow = dict(settings_service.getComponentDict(_component().target_information_settings)[TARGET_INFORMATION.TEXT_SHADOW])
        label_data = dict(settings_service.getComponentDict(_component().target_information_settings)[TARGET_INFORMATION.TEXT_POSITION])
        label_data.update({
            'drag': not settings_service.getComponentDict(_component().target_information_settings)[TARGET_INFORMATION.TEXT_LOCK],
            'border': False,
            'background': False,
            'alpha': 1.0,
            'customBackground': {
                'color': '#20252B', 'borderColor': '#49535D',
                'border': True, 'fill': True, 'thickness': 1,
                'margin': 12, 'ellipseWidth': 10,
                'alpha': max(0.0,
                             min(1.0,
                                 settings_service.getComponentDict(_component().target_information_settings)[TARGET_INFORMATION.BACKGROUND_ALPHA])) if settings_service.getComponentDict(_component().target_information_settings)[TARGET_INFORMATION.BACKGROUND_ENABLED] else 0.0
            },
            'shadow': shadow
        })
        self.data[ElementType.LABEL].update(label_data)
        self.updateObject(ElementType.LABEL, label_data)

    def addText(self, text=''):
        self._text = text
        # structured tab tags are not native TextField HTML tags.
        text = re.sub(r'<tab\s*/?>', '\t', text, flags=re.IGNORECASE)
        text = re.sub(r'<br\s*/?>', '<br>', text, flags=re.IGNORECASE)
        style = settings_service.getComponentDict(_component().target_information_settings).get(TARGET_INFORMATION.TEXT_FORMAT, {})
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

    setText = addText
    show = setVisible

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
        config = _component().target_information_settings
        # Each apply replaces the position dict, so it is read again before the y axis.
        x = self._fitAxis(config, 'x', 'alignX', curScr[0] / scale, (Align.LEFT, Align.RIGHT, Align.CENTER))
        y = self._fitAxis(config, 'y', 'alignY', curScr[1] / scale, (Align.TOP, Align.BOTTOM, Align.CENTER))
        self.updateObject(ElementType.LABEL, {'x': x, 'y': y})

    def _fitAxis(self, config, key, alignKey, screen, aligns):
        position = settings_service.getComponentDict(config)[TARGET_INFORMATION.TEXT_POSITION]
        value = position.get(key, None)
        modes = dict(zip(aligns, (1, -1, 0)))
        if position[alignKey] in modes:
            value = self.screenFix(screen, position[key], modes[position[alignKey]])
        if value is not None and value != position[key]:
            settings_service.apply(config, {TARGET_INFORMATION.TEXT_POSITION: {key: value}}, persist=False)
            self.data[ElementType.LABEL][key] = value
        return value

    def getData(self):
        return self.data

    def getNames(self):
        return self.name
