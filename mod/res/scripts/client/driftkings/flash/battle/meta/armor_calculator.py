# -*- coding: utf-8 -*-
from driftkings.flash.battle.meta.base import CrosshairMeta


class ArmorCalculatorMeta(CrosshairMeta):
    FLASH_CLASS = 'driftkings.battle.components.armor_calculator.armorcalculatorui'

    def as_armorCalculatorS(self, text):
        if self._isDAAPIInited():
            return self.flashObject.as_armorCalculator(text)
