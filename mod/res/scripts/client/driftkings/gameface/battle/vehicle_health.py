# -*- coding: utf-8 -*-
"""Own health bar as an owned Gameface child of the native battle HUD; state comes from the component."""
from importlib import import_module

from driftkings._constants import GLOBAL, VEHICLE_HEALTH
from driftkings.common.utils.formatting import percentToRgb
from driftkings.core.hud_visibility import hudVisibility
from driftkings.gameface.battle.common import BattleCardAdapter
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.views.marks_model import moved_panel

LOG = get_logger('Driftkings.OwnHealthBattle')
FEATURE = 'DriftkingsOwnHealth'
POSITION_KEYS = (GLOBAL.X, GLOBAL.Y, GLOBAL.ALIGN_X, GLOBAL.ALIGN_Y)
# Range of the x/y sliders in the settings panel.
POSITION_LIMIT = 2000


def _component():
    return import_module('driftkings.battle.vehicle_health')


class OwnHealthAdapter(BattleCardAdapter):
    def __init__(self):
        super(OwnHealthAdapter, self).__init__(FEATURE, VEHICLE_HEALTH, LOG, 'OwnHealth', active=False)

    def startBattle(self):
        if not self.active:
            self.active = True
            hudVisibility.attach(self)
        self.refresh()

    def stopBattle(self):
        if self.active:
            self.active = False
            hudVisibility.detach(self)
        self.refresh()

    def beforeDispose(self):
        self.stopBattle()

    def savePosition(self, child, args):
        # Dragged with the battle cursor (Ctrl); the position lands in the same settings as the sliders.
        settings = settings_service.getComponentDict(_component().vehicle_health_settings)
        if not self.active or not self.hudVisible or not child._guiVisible or not child._cursorVisible:
            return
        panel = moved_panel(dict((key, settings[key]) for key in POSITION_KEYS), args)
        if panel is None:
            return
        for key in (GLOBAL.X, GLOBAL.Y):
            panel[key] = max(-POSITION_LIMIT, min(POSITION_LIMIT, int(round(panel[key]))))
        settings_service.apply(_component().vehicle_health_settings, panel)

    def refresh(self):
        settings = settings_service.getComponentDict(_component().vehicle_health_settings)
        state = _component().tracker.state
        config = dict((key, settings[key]) for key in POSITION_KEYS)
        config['locked'] = False
        maximum, current = state['maximum'], state['current']
        percent = float(current) / maximum if maximum > 0 else 0.0
        enabled = bool(self.active and self.visible and self.hudVisible and settings[GLOBAL.ENABLED]
                       and state['battle'] and state['alive'] and maximum > 0)
        payload = {'percent': percent, 'text': '%d / %d' % (current, maximum),
                   'color': percentToRgb(percent, **settings[VEHICLE_HEALTH.AVG_COLOR])}
        self.publish(payload, config, enabled)
