# -*- coding: utf-8 -*-
from collections import namedtuple
import math
import re
import weakref

from constants import ARENA_BONUS_TYPE
from gui.battle_control.battle_constants import PERSONAL_EFFICIENCY_TYPE
from gui.Scaleform.daapi.view.battle.shared.ribbons_aggregator import RibbonsAggregator
from gui.Scaleform.daapi.view.battle.shared.ribbons_panel import BattleRibbonsPanel
from gui.Scaleform.genConsts.BATTLE_EFFICIENCY_TYPES import BATTLE_EFFICIENCY_TYPES

from driftkings._constants import BATTLE_PERFORMANCE, GLOBAL
from driftkings.common.utils import events
from driftkings.common.utils.colorratting import getRelativePerformanceColor, getStatisticColor
from driftkings.common.utils.formatting import replaceMacros
from driftkings.common.utils.wgutils import getPlayer
from driftkings.core.battle_events import battleEvents
from driftkings.core.hooks import on_event, override
from driftkings.core.wnx import calculate as calculate_wnx
from driftkings.core.wnx import get_expected as get_wnx_expected
from driftkings.logger import get_logger
from driftkings.settings.definitions.components.battle_performance import BattlePerformanceSettings as Settings
from driftkings.settings.service import affects, settings_service
from driftkings.stats.vehinfo import calculateXTE, calculateRatingScale, getVehicleInfoData
from driftkings.flash.batalha.battle_performance import _startFlash
from driftkings.gameface.hangar.battle_performance import install_results_gameface

LOG = get_logger('Driftkings.BattleEfficiency')
_results_views = weakref.WeakKeyDictionary()

DEF_RESULTS_LEN = 16
RANKED_OFFSET = 4
# Battles that update the account statistics, including bot-filled randoms.
SUPPORTED_BONUS_TYPES = set(getattr(ARENA_BONUS_TYPE, name) for name in ('REGULAR', 'RANDOM_NP2', 'WINBACK')
                            if hasattr(ARENA_BONUS_TYPE, name))
EXCLUDED_BONUS_TYPES = {
    ARENA_BONUS_TYPE.EVENT_BATTLES,
    ARENA_BONUS_TYPE.EPIC_RANDOM,
    ARENA_BONUS_TYPE.EPIC_RANDOM_TRAINING,
    ARENA_BONUS_TYPE.EPIC_BATTLE
}
DataIDs = namedtuple('DataIDs', ('damageDealt', 'spotted', 'kills', 'defAndCap_vehWOStun', 'defAndCap_vehWStun'))
data_ids = DataIDs(3, 11, 12, 14, 17)


g_flash = None
config = Settings()


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
        def ratio(value, key):
            # Expected frags, spots and defence are often below 1: only guard against zero.
            expected = float(self.expectedValues[key])
            return float(value) / expected if expected > 0 else 0.0
        rDAMAGE = ratio(damage, 'wn8expDamage')
        rSPOT = ratio(spotted, 'wn8expSpot')
        rFRAG = ratio(frags, 'wn8expFrag')
        rDEF = ratio(defence, 'wn8expDef')
        rWIN = ratio(100.0 if isWin else 0, 'wn8expWinRate')
        return rDAMAGE, rSPOT, rFRAG, rDEF, rWIN

    def damage_efficiency(self, damage):
        """Raw damage / WN8 expected damage; 1.0 means the expected damage was met."""
        if not self.vInfoOK:
            return None
        try:
            expected = float(self.expectedValues['wn8expDamage'])
            damage = float(damage)
            if expected <= 0 or damage < 0 or any(math.isnan(value) or math.isinf(value)
                                                for value in (damage, expected)):
                return None
            ratio = damage / expected
            return ratio if not math.isinf(ratio) else None
        except (KeyError, TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def calculate_wN8(rDAMAGE, rSPOT, rFRAG, rDEF, rWIN):
        rWINc = max(0.0, (rWIN - 0.71) / (1 - 0.71))
        rDAMAGEc = max(0.0, (rDAMAGE - 0.22) / (1 - 0.22))
        rSPOTc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rSPOT - 0.38) / (1 - 0.38))))
        rFRAGc = max(0.0, min(rDAMAGEc + 0.2, max(0.0, (rFRAG - 0.12) / (1 - 0.12))))
        rDEFc = max(0.0, min(rDAMAGEc + 0.1, max(0.0, (rDEF - 0.10) / (1 - 0.10))))

        WN8 = int(980 * rDAMAGEc + 210 * rDAMAGEc * rFRAGc + 155 * rFRAGc * rSPOTc + 75 * rDEFc * rFRAGc + 145 * min(1.8, rWINc))
        XWN8 = calculateRatingScale('xwn8', WN8)
        return WN8, XWN8

    def calculate_efficiency(self, damage, frags, spotted, capture, defence):
        EFF = int(max(0, int(damage * (10.0 / (self.avgTier + 2)) * (0.23 + 2 * self.avgTier / 100.0) + frags * 250 + spotted * 150 + math.log(capture + 1, 1.732) * 150 + defence * 150)))
        XEFF = calculateRatingScale('xeff', EFF)
        return EFF, XEFF

    def calculate_XTE(self, damage, frags):
        return calculateXTE(self.vehCD, damage, frags) if self.vehCD is not None else 0


class BattleEfficiency(object):
    def __init__(self):
        self._active = False
        self._resetStats()

    def _resetStats(self):
        self._stats = {'frags': 0, 'damage': 0, 'spotted': 0, 'defence': 0, 'capture': 0, 'wn8': 0, 'xwn8': 0, 'eff': 0, 'xeff': 0, 'xte': 0, 'diff': 0, 'dmg': 0, 'wn8effd': None}
        self._colors = {key: getStatisticColor(key, None) for key in ['wn8', 'xwn8', 'eff', 'xeff', 'xte', 'diff', 'dmg', 'wn8effd']}
        self._stats.update(assist=0, stun=0, wnx=None)
        self._colors['wnx'] = None

    def start(self):
        if not self._active:
            self._active = True
            settings_service.onModSettingsChanged.connect(self.onSettingsChanged, BATTLE_PERFORMANCE)

    def stop(self):
        if self._active:
            self._active = False
            settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
            self.stopBattle()
            g_calculator.stopBattle()

    def onSettingsChanged(self, component, changes):
        if affects(changes, GLOBAL.ENABLED, BATTLE_PERFORMANCE.FORMAT, BATTLE_PERFORMANCE.COLOR_RATTING):
            self.updateFormatString()
        if affects(changes, GLOBAL.ENABLED, BATTLE_PERFORMANCE.BATTLE_RESULTS_WINDOW,
                   BATTLE_PERFORMANCE.BATTLE_RESULTS_FORMAT, BATTLE_PERFORMANCE.COLOR_RATTING):
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
    def read_colors(rating_color, rating_value, damage=None, expected_damage=None):
        palette = settings_service.getComponentDict(config).get(BATTLE_PERFORMANCE.COLOR_RATTING, 0)
        if rating_color == 'diff':
            return getRelativePerformanceColor(damage, expected_damage, palette)
        return getStatisticColor(rating_color, rating_value, palette)

    def startBattle(self):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED] or g_flash is None:
            return
        result = g_calculator.calc(self._stats['damage'], self._stats['spotted'], self._stats['frags'], self._stats['defence'], self._stats['capture'])
        self._stats.update(dict(zip(['wn8', 'xwn8', 'eff', 'xeff', 'xte', 'dmg', 'diff'], result)))
        self._stats['wn8effd'] = g_calculator.damage_efficiency(self._stats['damage'])
        self._stats['wnx'] = calculate_wnx(self._stats['damage'], self._stats['frags'],
            self._stats['spotted'], self._stats.get('assist', 0) + self._stats.get('stun', 0),
            get_wnx_expected(g_calculator.vehCD))
        self._colors['wnx'] = None
        self.updateFormatString()

    def updateFormatString(self):
        settings = settings_service.getComponentDict(config)
        player = getPlayer()
        arena = getattr(player, 'arena', None)
        if not settings[GLOBAL.ENABLED] or arena is None or arena.bonusType not in SUPPORTED_BONUS_TYPES:
            if g_flash is not None:
                g_flash.setVisible(False)
            return
        macro_data = {}
        expected_damage = g_calculator.expectedValues.get('wn8expDamage') if g_calculator.vInfoOK else None
        for key, value in self._stats.items():
            if key == 'wn8effd':
                macro_data['{wn8effd}'] = '--' if value is None else '%.2f' % value
            elif key == 'wnx':
                macro_data['{wnx}'] = '--' if value is None else str(int(math.floor(value + .5)))
            else:
                macro_data['{%s}' % key] = str(int(value) if isinstance(value, float) else value)
            if key in self._colors:
                color_key = 'x' if key.startswith('x') else key
                color_value = self.read_colors(color_key, value, self._stats['damage'], expected_damage)
                macro_data['{c:%s}' % key] = str(color_value) if color_value is not None else ''
        format_text = replaceMacros(settings[BATTLE_PERFORMANCE.FORMAT], macro_data)
        if g_flash:
            g_flash.addText(format_text)
            g_flash.setVisible(True)


g_battleEfficiency = BattleEfficiency()
g_calculator = EfficiencyCalculator()


@on_event(battleEvents.appearanceDetailed)
def new_onAppearanceReady(self, vehicle):
    if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
        return
    if vehicle.id == self.playerVehicleID:
        g_calculator.registerVInfoData(vehicle.typeDescriptor.type.compactDescr)
        g_battleEfficiency.startBattle()


class _EfficiencyListener(object):
    """Subscribes to the native personal efficiency controller for one battle."""

    def __init__(self):
        self.ctrl = None

    def attach(self):
        self.detach()
        player = getPlayer()
        ctrl = getattr(getattr(getattr(player, 'guiSessionProvider', None), 'shared', None), 'personalEfficiencyCtrl', None)
        if ctrl is not None:
            ctrl.onTotalEfficiencyUpdated += self.onTotalEfficiencyUpdated
            self.ctrl = ctrl

    def detach(self):
        if self.ctrl is not None:
            self.ctrl.onTotalEfficiencyUpdated -= self.onTotalEfficiencyUpdated
            self.ctrl = None

    @staticmethod
    def onTotalEfficiencyUpdated(diff):
        if not settings_service.getComponentDict(config)[GLOBAL.ENABLED]:
            return
        changed = False
        if PERSONAL_EFFICIENCY_TYPE.DAMAGE in diff:
            g_battleEfficiency.stats['damage'] = diff[PERSONAL_EFFICIENCY_TYPE.DAMAGE]
            changed = True
        if PERSONAL_EFFICIENCY_TYPE.ASSIST_DAMAGE in diff:
            g_battleEfficiency.stats['assist'] = diff[PERSONAL_EFFICIENCY_TYPE.ASSIST_DAMAGE]
            changed = True
        if PERSONAL_EFFICIENCY_TYPE.STUN in diff:
            g_battleEfficiency.stats['stun'] = diff[PERSONAL_EFFICIENCY_TYPE.STUN]
            changed = True
        if changed:
            g_battleEfficiency.startBattle()


g_efficiencyListener = _EfficiencyListener()


@on_event(events.PlayerAvatar.startGUI.after)
def new_startGUI(*args):
    g_efficiencyListener.attach()
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


@on_event(events.PlayerAvatar.destroyGUI.after)
def new_destroyGUI(*args):
    g_efficiencyListener.detach()
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
    expected_damage = calculator.expectedValues.get('wn8expDamage') if calculator.vInfoOK else None
    result_values = dict(zip(RESULT_KEYS, values))
    result_values['wn8effd'] = calculator.damage_efficiency(summary.damageDealt)
    assistance = getattr(summary, 'damageAssisted', None)
    stun = getattr(summary, 'damageAssistedStun', None)
    result_values['wnx'] = calculate_wnx(summary.damageDealt, summary.kills, summary.spotted,
        assistance + stun if assistance is not None and stun is not None else None,
        get_wnx_expected(summary.vehicle.intCD))
    for key, value in result_values.items():
        macros['{%s}' % key] = '--' if value is None else ('%.2f' % value if key == 'wn8effd' else str(value))
        if key == 'wnx' and value is not None:
            macros['{wnx}'] = str(int(math.floor(value + .5)))
        macros['{c:%s}' % key] = g_battleEfficiency.read_colors(key, value, summary.damageDealt, expected_damage)
    # Historical templates also advertised this shared X-scale color macro.
    macros['{c:x}'] = macros['{c:xwn8}']
    template = settings_service.getComponentDict(config)[BATTLE_PERFORMANCE.BATTLE_RESULTS_FORMAT]
    # The native BattleInfo already owns the map and mode. Remove the legacy
    # header before expanding macros, preserving the user's rating template.
    template = re.sub(u'\\{mapName\\}\\s*[-\u2013\u2014]?\\s*\\{battleType\\}\\s*', '', template)
    template = template.replace('{mapName}', '').replace('{battleType}', '')
    return {'enabled': True, 'html': replaceMacros(template, macros)}


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
