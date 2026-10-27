# -*- coding: utf-8 -*-
"""Owned Gameface child of WG 2.4.1 RandomHUDView; no Scaleform overlay."""
from importlib import import_module

from driftkings._constants import BATTLE_MARKS_OF_EXCELLENCE, GLOBAL
from driftkings.core.hud_visibility import hudVisibility
from driftkings.core.marks_state import marks_state
from driftkings.gameface.battle.common import BattleCardAdapter
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.views.marks_model import moved_panel, number_locale

LOG = get_logger('Driftkings.MarksOnGunBattle')
FEATURE = 'DriftkingsMarksOnGunBattle'


def _component():
    return import_module('driftkings.battle.battle_marks_of_excellence')


class BattleMarksAdapter(BattleCardAdapter):
    def __init__(self):
        super(BattleMarksAdapter, self).__init__(FEATURE, BATTLE_MARKS_OF_EXCELLENCE, LOG, 'MarksOnGun', active=False)

    def startBattle(self):
        if self.active:
            return
        import BattleReplay
        settings = settings_service.getComponentDict(_component().config)
        if not settings[GLOBAL.ENABLED] or (BattleReplay.isPlaying() and not settings[BATTLE_MARKS_OF_EXCELLENCE.SHOW_IN_REPLAY]):
            return
        marks_state.clear('battle')
        self.active = True
        self.visible = True
        hudVisibility.attach(self)
        self.refresh()

    def stopBattle(self):
        self.active = False
        hudVisibility.detach(self)
        marks_state.clear('battle')
        self.refresh()

    def onStateChanged(self, context):
        if context == 'battle':
            self.refresh()

    def set_marks(self, payload):
        if not marks_state.publish('battle', payload):
            # Visibility can change without a numeric update.
            self.refresh()

    def unavailable(self, vehicle_id):
        self.visible = True
        marks_state.publish('battle', {'state': 'unavailable', 'vehicleId': vehicle_id})
        self.refresh()

    def connectSignals(self):
        marks_state.changed.connect(self.onStateChanged)
        super(BattleMarksAdapter, self).connectSignals()

    def disconnectSignals(self):
        marks_state.changed.disconnect(self.onStateChanged)
        super(BattleMarksAdapter, self).disconnectSignals()

    def beforeDispose(self):
        self.stopBattle()

    def savePosition(self, child, args):
        settings = settings_service.getComponentDict(_component().config)
        if not self.active or settings.get(BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, {}).get('locked', True):
            return
        panel = moved_panel(settings[BATTLE_MARKS_OF_EXCELLENCE.PANEL], args)
        if panel is None:
            return
        settings_service.apply(_component().config, {BATTLE_MARKS_OF_EXCELLENCE.PANEL: panel})

    def refresh(self):
        settings = settings_service.getComponentDict(_component().config)
        config = dict(settings.get(BATTLE_MARKS_OF_EXCELLENCE.GAMEFACE, {}))
        config.update(settings[BATTLE_MARKS_OF_EXCELLENCE.PANEL])
        config.update(scale=settings[BATTLE_MARKS_OF_EXCELLENCE.BATTLE_MESSAGE_SIZE_IN_PERCENT] / 100.0,
                      showStars=settings.get(BATTLE_MARKS_OF_EXCELLENCE.SHOW_MARKS, True), showTrend=settings.get(BATTLE_MARKS_OF_EXCELLENCE.SHOW_DELTA, True),
                      showCombined=settings.get(BATTLE_MARKS_OF_EXCELLENCE.SHOW_DAMAGE, True), showProgress=settings.get(BATTLE_MARKS_OF_EXCELLENCE.SHOW_PROGRESS, True))
        if not settings[BATTLE_MARKS_OF_EXCELLENCE.BACKGROUND]:
            config['backgroundOpacity'] = 0
        config['showTargetDamage'] = bool(config.get('showTargetDamage', True) and settings.get(BATTLE_MARKS_OF_EXCELLENCE.SHOW_TARGETS, True))
        config['showRequiredDamage'] = bool(config.get('showRequiredDamage', True) and settings.get(BATTLE_MARKS_OF_EXCELLENCE.SHOW_TARGETS, True))
        config.update(number_locale(_component().config.lang))
        enabled = bool(self.active and self.visible and self.hudVisible and settings[GLOBAL.ENABLED]
                       and config.get('enabled', True) and config.get('visible', True))
        payload = marks_state.snapshot('battle')
        if payload.get('trend'):
            payload['trend'] = dict(payload['trend'])
            payload['trend']['text'] = payload['trend']['text'].replace('.', config['decimalSeparator'])
        payload.update(config=config,
                       labels=dict((key[7:], value) for key, value in _component().config.i18n.items() if key.startswith('UI_mog_')))
        payload['labels']['title'] = _component().config.i18n['UI_description']
        self.publish(payload, config, enabled)
