# -*- coding: utf-8 -*-
"""Texts at a fixed place on the battle screen (battle efficiency, team strength) as owned Gameface
children of the native battle HUD. Each module keeps its settings: the position (x/y in interface units
from the alignX/alignY edge, as in the retired Flash overlay), the base text style, the shadow and the
text lock; an unlocked text can be dragged with Ctrl."""
from importlib import import_module

from driftkings._constants import BATTLE_PERFORMANCE, BATTLE_STATISTICS, GLOBAL
from driftkings.core.hud_visibility import hudVisibility
from driftkings.gameface.battle.common import BattleCardAdapter
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.views.marks_model import moved_panel

POSITION_KEYS = (GLOBAL.X, GLOBAL.Y, GLOBAL.ALIGN_X, GLOBAL.ALIGN_Y)
TEXT_LOCK = 'textLock'
TEXT_SHADOW = 'textShadow'


class ScreenTextAdapter(BattleCardAdapter):
    """One text on the screen: the component formats it and decides when it shows, JS places it."""
    COMPONENT = None
    SETTINGS = None
    # Settings key of the position object.
    POSITION = None

    def __init__(self, feature, namespace, title):
        super(ScreenTextAdapter, self).__init__(feature, namespace, get_logger('Driftkings.' + title), title, active=False)
        self.text = ''
        self.shown = False

    def config(self):
        return getattr(import_module(self.COMPONENT), self.SETTINGS)

    def settings(self):
        return settings_service.getComponentDict(self.config())

    def style(self, settings):
        raise NotImplementedError

    def startBattle(self):
        if not self.active:
            self.active = True
            hudVisibility.attach(self)
        self.refresh()

    def stopBattle(self):
        if self.active:
            self.active = False
            hudVisibility.detach(self)
        self.text = ''
        self.shown = False
        self.refresh()

    def beforeDispose(self):
        self.stopBattle()

    def setText(self, text):
        text = text or ''
        if text != self.text:
            self.text = text
            self.refresh()

    def show(self, shown):
        shown = bool(shown)
        if shown != self.shown:
            self.shown = shown
            self.refresh()

    def savePosition(self, child, args):
        # Dragged with the battle cursor (Ctrl); the position lands in the module's own position object,
        # with the anchor of the nearest screen edge.
        settings = self.settings()
        if not self.active or not self.hudVisible or not child._guiVisible or not child._cursorVisible or settings.get(TEXT_LOCK):
            return
        current = settings[self.POSITION]
        panel = moved_panel(dict((key, current[key]) for key in POSITION_KEYS if key in current), args)
        if panel is None:
            return
        for key in (GLOBAL.X, GLOBAL.Y):
            panel[key] = int(round(panel[key]))
        settings_service.apply(self.config(), {self.POSITION: panel})

    def refresh(self):
        settings = self.settings()
        position = settings[self.POSITION]
        config = dict((key, position[key]) for key in POSITION_KEYS if key in position)
        config.update(alpha=position.get('alpha', 1.0), shadow=settings.get(TEXT_SHADOW), locked=bool(settings.get(TEXT_LOCK)))
        enabled = bool(self.active and self.visible and self.hudVisible and settings[GLOBAL.ENABLED] and self.shown and self.text)
        self.publish({'text': self.text, 'style': self.style(settings)}, config, enabled)


class BattleEfficiencyAdapter(ScreenTextAdapter):
    COMPONENT = 'driftkings.components.battle_performance'
    SETTINGS = 'battle_performance_settings'
    POSITION = BATTLE_PERFORMANCE.POSITION

    def __init__(self):
        super(BattleEfficiencyAdapter, self).__init__('DriftkingsBattleEfficiency', BATTLE_PERFORMANCE, 'BattleEfficiencyHud')

    def style(self, settings):
        # The Flash view wrapped the template in <font size face color><p align>.
        style = settings[BATTLE_PERFORMANCE.TEXT_STYLE]
        return {'font': style.get('font'), 'size': style.get('size'), 'color': style.get('color'), 'align': style.get('align')}


class TeamStrengthAdapter(ScreenTextAdapter):
    COMPONENT = 'driftkings.battle.battle_statistics'
    SETTINGS = 'battle_statistics_settings'
    POSITION = BATTLE_STATISTICS.TEXT_POSITION

    def __init__(self):
        super(TeamStrengthAdapter, self).__init__('DriftkingsTeamStrength', BATTLE_STATISTICS, 'TeamStrength')

    def style(self, settings):
        # The Flash view wrapped the text in <font face size color> with optional <b>/<i>.
        style = settings[BATTLE_STATISTICS.TEXT_FORMAT]
        return {'font': style.get('font'), 'size': style.get('size'), 'color': style.get('color'),
                'bold': bool(style.get('bold')), 'italic': bool(style.get('italic')), 'align': 'left'}
