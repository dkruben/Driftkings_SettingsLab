# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_EFFICIENCY, GLOBAL
from Driftkings.settings.service import settings_service
"""Presentation adapter for BattleEfficiency; gameplay state stays in its component."""
import re
from constants import ARENA_BONUS_TYPE
from gui.Scaleform.daapi.view.battle_results_window import BattleResultsWindow
from Driftkings.common import logError, replaceMacros
from Driftkings.core.hooks import override

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.components.battle_efficiency')


@override(BattleResultsWindow, 'as_setDataS')
def new_setDataS(func, self, data):
    if not settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED] or not settings_service.getComponentDict(_component().config)[BATTLE_EFFICIENCY.BATTLE_RESULTS_WINDOW]:
        return func(self, data)

    def _normalizeString(s):
        return re.sub('<.*?>', '', s.replace(u'\xa0', '').replace(u'\u202f', '').replace(' ', '').replace('.', '').replace(',', ''))

    def _splitArenaStr(s):
        _s = s.replace(u'\xa0\u2014', '-').replace(u'\u2013', '-')
        _s = _s.split('-')
        return _s if (len(_s) == 2) else (s, '')

    calculator = _component().EfficiencyCalculator()
    try:
        common = data['common']
        if common['bonusType'] in _component().EXCLUDED_BONUS_TYPES:
            return func(self, data)
        offset = 0 if common['bonusType'] != ARENA_BONUS_TYPE.RANKED else _component().RANKED_OFFSET
        teamDict = data['team1']
        statValues = data['personal']['statValues'][0]
        stunStatus = 'vehWStun' if (len(statValues) > (_component().DEF_RESULTS_LEN + offset)) else 'vehWOStun'
        isWin = common['resultShortStr'] == 'win'
        arenaStr = _splitArenaStr(common['arenaStr'])
        mapName = arenaStr[0].strip()
        battleType = arenaStr[1].strip()

        for playerDict in teamDict:
            if playerDict['isSelf']:
                calculator.registerVInfoData(playerDict['vehicleCD'])
                break
        dataIDs = _component().getDataIds(offset)
        damageDealt = _normalizeString(statValues[dataIDs.damageDealt]['value'])
        spotted = _normalizeString(statValues[dataIDs.spotted]['value'])
        # Fix for kills parsing - safely handle the split operation
        kills_str = _normalizeString(statValues[dataIDs.kills]['value'])
        kills_parts = kills_str.split('/')
        kills = kills_parts[1] if len(kills_parts) > 1 else kills_str
        # Get the correct index for defAndCap based on stun status
        idx = dataIDs.defAndCap_vehWStun if stunStatus == 'vehWStun' else dataIDs.defAndCap_vehWOStun
        _str = _normalizeString(statValues[idx]['value'])
        # Safely handle the split operation for defAndCap
        parts = _str.split('/')
        capture = parts[0] if len(parts) > 0 else '0'
        defence = parts[1] if len(parts) > 1 else '0'
        result = calculator.calc(int(damageDealt), int(spotted), int(kills), int(defence), int(capture), isWin)
        wn8, xwn8, eff, xeff, xte, dmg, diff = result
        macro_data = {
            '{mapName}': mapName,
            '{battleType}': battleType,
            '{wn8}': str(wn8),
            '{xwn8}': str(xwn8),
            '{eff}': str(eff),
            '{xeff}': str(xeff),
            '{xte}': str(xte),
            '{dmg}': str(dmg),
            '{diff}': str(diff),
            '{c:wn8}': _component().g_battleEfficiency.read_colors('wn8', wn8),
            '{c:xwn8}': _component().g_battleEfficiency.read_colors('x', xwn8),
            '{c:eff}': _component().g_battleEfficiency.read_colors('eff', eff),
            '{c:xeff}': _component().g_battleEfficiency.read_colors('x', xeff),
            '{c:xte}': _component().g_battleEfficiency.read_colors('x', xte),
            '{c:dmg}': _component().g_battleEfficiency.read_colors('tdb', dmg),
            '{c:diff}': _component().g_battleEfficiency.read_colors('diff', diff)
        }
        msg = replaceMacros(settings_service.getComponentDict(_component().config)[BATTLE_EFFICIENCY.BATTLE_RESULTS_FORMAT], macro_data)
        data['common']['arenaStr'] = msg
    except Exception as err:
        logError(_component().config.ID, 'Battle results parsing error: {}', err)
        # Preserve the original result window if the legacy data layout changed.
        _component().LOG.exception('Legacy battle results integration failed')
    return func(self, data)
