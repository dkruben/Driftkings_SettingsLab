# -*- coding: utf-8 -*-
import logging
import math
import weakref
from collections import namedtuple

from Avatar import PlayerAvatar
from constants import ARENA_BONUS_TYPE
from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE

from Driftkings._constants import BATTLE_EFFICIENCY, GLOBAL
from Driftkings.common import getPlayer, getStatisticColor, replaceMacros
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service, affects
from Driftkings.settings.templates.components.battle_efficiency import BattleEfficiencySettings as ConfigInterface
from Driftkings.stats import getVehicleInfoData, calculateXvmScale, calculateXTE
from Driftkings.views.battle.battle_efficiency import _startFlash
from Driftkings.views.hangar.battle_efficiency import install_results_gameface

LOG = logging.getLogger('Driftkings.BattleEfficiency')
_results_views = weakref.WeakKeyDictionary()

DEF_RESULTS_LEN = 16
RANKED_OFFSET = 4
SUPPORTED_BONUS_TYPES = {ARENA_BONUS_TYPE.REGULAR}
EXCLUDED_BONUS_TYPES = {
    ARENA_BONUS_TYPE.EVENT_BATTLES,
    ARENA_BONUS_TYPE.EPIC_RANDOM,
    ARENA_BONUS_TYPE.EPIC_RANDOM_TRAINING,
    ARENA_BONUS_TYPE.EPIC_BATTLE
}
DataIDs = namedtuple('DataIDs', ('damageDealt', 'spotted', 'kills', 'defAndCap_vehWOStun', 'defAndCap_vehWStun'))
data_ids = DataIDs(3, 11, 12, 14, 17)


g_flash = None
config = ConfigInterface()


def getDataIds(offset):
    if not offset:
        return data_ids
    else:
        return DataIDs(*(value + offset for value in data_ids))


class EfficiencyCalculator(object):

    def __init__(self):
        self.avgTier = 5
        self.expectedValues = {}
        self.vehCD = None
        self.vInfoOK = False

    def stopBattle(self):
        self.expectedValues = {}
        self.vehCD = None
        self.vInfoOK = False

    def registerVInfoData(self, veh_cd):
        if not veh_cd:
            return
        self.vehCD = veh_cd
        v_info_data = getVehicleInfoData(veh_cd) or {}
        self.avgTier = v_info_data.get('level', 5)
        expected_keys = ('wn8expDamage', 'wn8expSpot', 'wn8expFrag', 'wn8expDef', 'wn8expWinRate')
        self.expectedValues = {item: v_info_data.get(item, None) for item in expected_keys}
        self.vInfoOK = None not in self.expectedValues.values()

    def calc(self, damage, spotted, frags, defence, capture, isWin=False):
        if not self.vInfoOK:
            return 0, 0, 0, 0, 0, 0, 0
        damage = int(damage or 0)
        spotted = int(spotted or 0)
        frags = int(frags or 0)
        defence = int(defence or 0)
        capture = int(capture or 0)
        rDAMAGE, rSPOT, rFRAG, rDEF, rWIN = self.calculate_ratios(damage, spotted, frags, defence, isWin)
        WN8, XWN8 = self.calculate_wN8(rDAMAGE, rSPOT, rFRAG, rDEF, rWIN)
        DIFF = int(damage - self.expectedValues['wn8expDamage'])
        DMG = damage
        EFF, XEFF = self.calculate_efficiency(damage, frags, spotted, capture, defence)
        XTE = self.calculate_XTE(damage, frags)
        return WN8, XWN8, EFF, XEFF, XTE, DMG, DIFF

    def calculate_ratios(self, damage, spotted, frags, defence, isWin):
        rDAMAGE = float(damage) / max(1.0, float(self.expectedValues['wn8expDamage']))
        rSPOT = float(spotted) / max(1.0, float(self.expectedValues['wn8expSpot']))
        rFRAG = float(frags) / max(1.0, float(self.expectedValues['wn8expFrag']))
        rDEF = float(defence) / max(1.0, float(self.expectedValues['wn8expDef']))
        rWIN = (100.0 if isWin else 0) / max(1.0, float(self.expectedValues['wn8expWinRate']))
        return rDAMAGE, rSPOT, rFRAG, rDEF, rWIN

    @staticmethod
    def calculate_wN8(rDAMAGE, rSPOT, rFRAG, rDEF, rWIN):
        rWINc = max(0.0, (rWIN - 0.71) / (1 - 0.71))
        rDAMAGEc = max(0.0, (rDAMAGE - 0.22) / (1 - 0.22))
        rSPOTc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rSPOT - 0.38) / (1 - 0.38))))
        rFRAGc = max(0.0, min(rDAMAGEc + 0.2, max(0.0, (rFRAG - 0.12) / (1 - 0.12))))
        rDEFc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rDEF - 0.10) / (1 - 0.10))))

        WN8 = int(980 * rDAMAGEc + 210 * rDAMAGEc * rFRAGc + 155 * rFRAGc * rSPOTc + 75 * rDEFc * rFRAGc + 145 * min(1.8, rWINc))
        XWN8 = calculateXvmScale('xwn8', WN8)
        return WN8, XWN8

    def calculate_efficiency(self, damage, frags, spotted, capture, defence):
        EFF = int(max(0, int(damage * (10.0 / (self.avgTier + 2)) * (0.23 + 2 * self.avgTier / 100.0) + frags * 250 + spotted * 150 + math.log(capture + 1, 1.732) * 150 + defence * 150)))
        XEFF = calculateXvmScale('xeff', EFF)
        return EFF, XEFF

    def calculate_XTE(self, damage, frags):
        return calculateXTE(self.vehCD, damage, frags) if self.vehCD is not None else 0


class BattleEfficiency(object):
    def __init__(self):
        self._active = False
        self._resetStats()

    def _resetStats(self):
        self._stats = {'frags': 0, 'damage': 0, 'spotted': 0, 'defence': 0, 'capture': 0, 'wn8': 0, 'xwn8': 0, 'eff': 0, 'xeff': 0, 'xte': 0, 'diff': 0, 'dmg': 0}
        self._colors = {key: getStatisticColor(key, None) for key in ['wn8', 'xwn8', 'eff', 'xeff', 'xte', 'diff', 'dmg']}

    def start(self):
        if not self._active:
            self._active = True
            settings_service.onModSettingsChanged.connect(self.onSettingsChanged, BATTLE_EFFICIENCY)

    def stop(self):
        if self._active:
            self._active = False
            settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
            self.stopBattle()
            g_calculator.stopBattle()

    def onSettingsChanged(self, component, changes):
        if affects(changes, GLOBAL.ENABLED, BATTLE_EFFICIENCY.FORMAT, BATTLE_EFFICIENCY.COLOR_RATTING):
            self.updateFormatString()
        if affects(changes, GLOBAL.ENABLED, BATTLE_EFFICIENCY.BATTLE_RESULTS_WINDOW,
                   BATTLE_EFFICIENCY.BATTLE_RESULTS_FORMAT, BATTLE_EFFICIENCY.COLOR_RATTING):
            for view, child in list(_results_views.items()):
                try:
                    child.refresh(view.arenaUniqueID)
                except Exception:
                    LOG.exception('Could not refresh battle efficiency results')

    def stopBattle(self):
        self._resetStats()
        if g_flash is not None:
            g_flash.setVisible(False)

    @property
    def stats(self):
        return self._stats

    @staticmethod
    def read_colors(rating_color, rating_value):
        return getStatisticColor(rating_color, rating_value, settings_service.getComponentDict(config).get(BATTLE_EFFICIENCY.COLOR_RATTING, 0))

    def startBattle(self):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED] or g_flash is None:
            return
        result = g_calculator.calc(self._stats['damage'], self._stats['spotted'], self._stats['frags'], self._stats['defence'], self._stats['capture'])
        self._stats.update(dict(zip(['wn8', 'xwn8', 'eff', 'xeff', 'xte', 'dmg', 'diff'], result)))
        self.updateFormatString()

    def updateFormatString(self):
        player = getPlayer()
        arena = getattr(player, 'arena', None)
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED] or arena is None or arena.bonusType not in SUPPORTED_BONUS_TYPES:
            if g_flash is not None:
                g_flash.setVisible(False)
            return
        macro_data = {}
        for key, value in self._stats.items():
            macro_data['{%s}' % key] = str(int(value) if isinstance(value, float) else value)
            if key in self._colors:
                color_key = 'x' if key.startswith('x') else key
                color_value = self.read_colors(color_key, value)
                macro_data['{c:%s}' % key] = str(color_value) if color_value is not None else ''
        format_text = replaceMacros(settings_service.getComponentDict(config)[BATTLE_EFFICIENCY.FORMAT], macro_data)
        if g_flash:
            g_flash.addText(format_text)
            g_flash.setVisible(True)


g_battleEfficiency = BattleEfficiency()
g_calculator = EfficiencyCalculator()


@override(PlayerAvatar, 'vehicle_onAppearanceReady')
def new_onAppearanceReady(func, self, vehicle):
    func(self, vehicle)
    if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        return
    if vehicle.id == self.playerVehicleID:
        g_calculator.registerVInfoData(vehicle.typeDescriptor.type.compactDescr)


@override(PlayerAvatar, '_PlayerAvatar__startGUI')
def new_startGUI(func, *args):
    func(*args)
    g_battleEfficiency.startBattle()


@override(RibbonsAggregator, 'suspend')
def new_suspend(func, self):
    if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        func(self)
        return
    self.resume()


@override(BattleRibbonsPanel, '_BattleRibbonsPanel__addRibbon')
def new_addRibbon(func, self, ribbonID, ribbonType='', leftFieldStr='', **kwargs):
    func(self, ribbonID, ribbonType, leftFieldStr, **kwargs)
    if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        return
    if ribbonType not in (BATTLE_EFFICIENCY_TYPES.DETECTION, BATTLE_EFFICIENCY_TYPES.DESTRUCTION, BATTLE_EFFICIENCY_TYPES.DEFENCE, BATTLE_EFFICIENCY_TYPES.CAPTURE):
        return
    if ribbonType == BATTLE_EFFICIENCY_TYPES.DETECTION:
        g_battleEfficiency.stats['spotted'] += 1 if (len(leftFieldStr.strip()) == 0) else int(leftFieldStr[1:])
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DESTRUCTION:
        g_battleEfficiency.stats['frags'] += 1
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.DEFENCE:
        g_battleEfficiency.stats['defence'] = min(100, g_battleEfficiency.stats['defence'] + int(leftFieldStr))
    elif ribbonType == BATTLE_EFFICIENCY_TYPES.CAPTURE:
        g_battleEfficiency.stats['capture'] = int(leftFieldStr)
    g_battleEfficiency.startBattle()


@override(DamageLogPanel, '_onTotalEfficiencyUpdated')
def new_onTotalEfficiencyUpdated(func, self, diff):
    func(self, diff)
    if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        return
    if PERSONAL_EFFICIENCY_TYPE.DAMAGE in diff:
        g_battleEfficiency.stats['damage'] = diff[PERSONAL_EFFICIENCY_TYPE.DAMAGE]
        g_battleEfficiency.startBattle()


@override(PlayerAvatar, '_PlayerAvatar__destroyGUI')
def new_destroyGUI(func, *args):
    func(*args)
    g_battleEfficiency.stopBattle()
    g_calculator.stopBattle()


RESULT_KEYS = ('wn8', 'xwn8', 'eff', 'xeff', 'xte', 'dmg', 'diff')


def make_results_payload(battle_results):
    """Read named raw result fields, independent of translated UI table positions."""
    from gui.battle_results.pbs_helpers.common import getArenaNameStr
    from gui.battle_results.settings import PLAYER_TEAM_RESULT
    reusable, results = battle_results.reusable, battle_results.results
    if reusable.common.arenaBonusType not in SUPPORTED_BONUS_TYPES:
        return {'enabled': False}
    summary = reusable.vehicles.getVehicleSummarizeInfo(reusable.getPlayerInfo(), results['vehicles'])
    if summary.vehicle is None:
        return {'enabled': False}
    calculator = EfficiencyCalculator()
    calculator.registerVInfoData(summary.vehicle.intCD)
    values = calculator.calc(summary.damageDealt, summary.spotted, summary.kills, summary.droppedCapturePoints, summary.capturePoints, reusable.getPersonalTeamResult() == PLAYER_TEAM_RESULT.WIN)
    # Expected data can be unavailable for new vehicles: do not present fake zero ratings.
    if not calculator.vInfoOK:
        values = (None, None, None, None, None, summary.damageDealt, None)
    macros = {'{mapName}': getArenaNameStr(reusable), '{battleType}': reusable.common.arenaType.getGamePlayName()}
    for key, value in zip(RESULT_KEYS, values):
        macros['{%s}' % key] = '--' if value is None else str(value)
        macros['{c:%s}' % key] = g_battleEfficiency.read_colors(key, value)
    # Historical templates also advertised this shared X-scale color macro.
    macros['{c:x}'] = macros['{c:xwn8}']
    return {'enabled': True, 'html': replaceMacros(settings_service.getComponentDict(config)[BATTLE_EFFICIENCY.BATTLE_RESULTS_FORMAT], macros)}


def init():
    _startFlash()
    g_battleEfficiency.start()
    try:
        install_results_gameface()
    except Exception:
        LOG.exception('Gameface results integration unavailable; legacy integration retained')


def fini():
    global g_flash
    g_battleEfficiency.stop()
    if g_flash is not None:
        g_flash.destroy()
        g_flash = None
from Driftkings.views.hangar import battle_efficiency_hooks
