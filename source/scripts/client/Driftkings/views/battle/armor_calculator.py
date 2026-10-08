# -*- coding: utf-8 -*-
"""Presentation adapter for ArmorCalculator; gameplay state stays in its component."""
from collections import defaultdict

from aih_constants import CTRL_MODE_NAME
from gui.battle_control import avatar_getter
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from Driftkings._constants import ARMOR_CALCULATOR
from Driftkings.meta.battle.armor_calculator import ArmorCalculatorMeta
from Driftkings.settings.service import settings_service
from Driftkings.ui.common.events import g_events


class ArmorCalculator(ArmorCalculatorMeta):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        super(ArmorCalculator, self).__init__(ARMOR_CALCULATOR.ID)
        self.calcMacro = defaultdict(lambda: 'macros not found')

    def _populate(self):
        super(ArmorCalculator, self)._populate()
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged += self.as_onCrosshairPositionChangedS
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, "onCameraChanged"):
            handler.onCameraChanged += self.onCameraChanged
        g_events.onArmorChanged += self.onArmorChanged
        g_events.onMarkerColorChanged += self.onMarkerColorChanged

    def _dispose(self):
        ctrl = self.sessionProvider.shared.crosshair
        if ctrl is not None:
            ctrl.onCrosshairPositionChanged -= self.as_onCrosshairPositionChangedS
        handler = avatar_getter.getInputHandler()
        if handler is not None and hasattr(handler, "onCameraChanged"):
            handler.onCameraChanged -= self.onCameraChanged
        g_events.onArmorChanged -= self.onArmorChanged
        g_events.onMarkerColorChanged -= self.onMarkerColorChanged
        super(ArmorCalculator, self)._dispose()

    def onMarkerColorChanged(self, color):
        self.calcMacro['color'] = settings_service.getConfig(self.ID).i18n['UI_colors'].get(color, '#FFD700')
        self.calcMacro['message'] = self.getSettings()[ARMOR_CALCULATOR.MESSAGES].get(color, '')

    def onCameraChanged(self, ctrlMode, *_, **__):
        _CTRL_MODE = {CTRL_MODE_NAME.KILL_CAM, CTRL_MODE_NAME.POSTMORTEM, CTRL_MODE_NAME.DEATH_FREE_CAM,
                      CTRL_MODE_NAME.RESPAWN_DEATH, CTRL_MODE_NAME.VEHICLES_SELECTION, CTRL_MODE_NAME.LOOK_AT_KILLER}
        if ctrlMode in _CTRL_MODE:
            self.as_armorCalculatorS('')

    def onArmorChanged(self, data):
        if data is None:
            return self.as_armorCalculatorS('')
        armor, piercingPower, caliber, ricochet, noDamage = data
        labels = settings_service.getConfig(self.ID).i18n
        self.calcMacro['ricochet'] = labels['UI_ricochet'] if ricochet else ''
        self.calcMacro['noDamage'] = labels['UI_noDamage'] if noDamage else ''
        self.calcMacro['countedArmor'] = armor
        self.calcMacro['piercingPower'] = piercingPower
        self.calcMacro['piercingReserve'] = piercingPower - armor
        self.calcMacro['caliber'] = caliber
        self.as_armorCalculatorS(self.getSettings()[ARMOR_CALCULATOR.TEMPLATE] % self.calcMacro)
