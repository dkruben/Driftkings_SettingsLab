# -*- coding: utf-8 -*-
"""Read-only battle context queries; no subscriptions, hooks or module rules."""
import logging
import sys

from Driftkings.core.mod_compatibility import read

LOG = logging.getLogger('Driftkings.BattleCapabilities')


def call(obj, name, *args):
    method = read(obj, name)
    if not callable(method):
        return None
    try:
        return method(*args)
    except Exception:
        return None


class BattleCapabilities(object):
    def __init__(self, player=None, session=None, modules=None):
        self._player = player
        self._session = session
        self.modules = sys.modules if modules is None else modules
        self._last_mode = None

    def player(self):
        try:
            return self._player() if self._player is not None else call(self.modules.get('BigWorld'), 'player')
        except Exception:
            return None

    def session(self):
        if self._session is not None:
            try:
                return self._session()
            except Exception:
                return None
        try:
            from helpers import dependency
            from skeletons.gui.battle_session import IBattleSessionProvider
            return dependency.instance(IBattleSessionProvider)
        except Exception:
            return None

    def is_in_battle(self):
        return read(self.player(), 'arena') is not None

    def _visitor(self):
        return read(self.session(), 'arenaVisitor') if self.is_in_battle() else None

    def _match(self, enum, value, names):
        constants = read(self.modules.get('constants'), enum)
        return value is not None and any(read(constants, name) is not None and value == read(constants, name) for name in names)

    def _bonus(self):
        visitor = self._visitor()
        value = call(visitor, 'getArenaBonusType')
        return value if value is not None else read(read(self.player(), 'arena'), 'bonusType')

    def _gui(self):
        return read(self._visitor(), 'gui')

    def is_comp7(self):
        return self.is_in_battle() and self._match('ARENA_BONUS_TYPE', self._bonus(), ('COMP7', 'TOURNAMENT_COMP7', 'TRAINING_COMP7', 'COMP7_LIGHT'))

    def is_frontline(self):
        return self.is_in_battle() and (call(self._gui(), 'isEpicBattle') is True or
            self._match('ARENA_BONUS_TYPE', self._bonus(), ('EPIC_BATTLE', 'EPIC_BATTLE_TRAINING')))

    def is_random(self):
        if not self.is_in_battle() or self.is_comp7() or self.is_event():
            return False
        bonus = read(self.modules.get('constants'), 'ARENA_BONUS_TYPE')
        value = self._bonus()
        random_range = read(bonus, 'RANDOM_RANGE', ())
        try:
            return value in random_range if value is not None and random_range else call(self._gui(), 'isRandomBattle') is True
        except Exception:
            return False

    def is_replay(self):
        replay = self.modules.get('BattleReplay')
        return self.is_in_battle() and (call(replay, 'isPlaying') is True or call(replay, 'isLoading') is True)

    def is_white_tiger(self):
        # Extension-specific APIs may be absent in this EU extraction. Do not
        # classify every EVENT_BATTLES arena as White Tiger.
        return self.is_in_battle() and (call(self._gui(), 'isWhiteTigerBattle') is True or
            self._match('ARENA_BONUS_TYPE', self._bonus(), ('WHITE_TIGER',)))

    def is_event(self):
        return self.is_in_battle() and (self.is_white_tiger() or call(self._gui(), 'isEventBattle') is True or
            self._match('ARENA_BONUS_TYPE', self._bonus(), ('EVENT_BATTLES', 'EVENT_BATTLES_2', 'EVENT_RANDOM', 'TOURNAMENT_EVENT')))

    def is_special(self):
        return self.current_mode() in ('comp7', 'frontline', 'event', 'white_tiger', 'special')

    def is_spg(self):
        if not self.is_in_battle():
            return False
        dp = call(self.session(), 'getArenaDP')
        return call(call(dp, 'getVehicleInfo'), 'isSPG') is True

    def current_mode(self):
        if not self.is_in_battle():
            account_type = read(self.modules.get('Account'), 'PlayerAccount')
            try:
                in_hangar = account_type is not None and isinstance(self.player(), account_type)
            except Exception:
                in_hangar = False
            mode = 'hangar' if in_hangar else 'unknown'
        elif self.is_white_tiger():
            mode = 'white_tiger'
        elif self.is_comp7():
            mode = 'comp7'
        elif self.is_frontline():
            mode = 'frontline'
        elif self.is_event():
            mode = 'event'
        elif self.is_random():
            mode = 'random'
        else:
            value = self._bonus()
            enum = read(self.modules.get('constants'), 'ARENA_BONUS_TYPE')
            try:
                known = value in read(enum, 'RANGE', ()) and value != read(enum, 'UNKNOWN')
            except Exception:
                known = False
            mode = 'special' if known else 'unknown'
        if mode != self._last_mode:
            self._last_mode = mode
            LOG.info('mode=%s', mode)
        return mode

    def supports_gameface_overlay(self, view=None, resource_key=None):
        # Require an actual initialized Wulf battle view supplied by the caller,
        # plus a resource resolved in the currently loaded OpenWG resource map.
        if not self.is_in_battle() or self.current_mode() in ('unknown', 'hangar') or view is None or not resource_key:
            return False
        gameface = self.modules.get('openwg_gameface')
        if not callable(read(gameface, 'gf_mod_inject')):
            return False
        try:
            from frameworks.wulf import View, ViewStatus
            if not isinstance(view, View) or read(view, 'viewStatus') != ViewStatus.LOADED or read(view, 'proxy') is None:
                return False
            # Recognize a real client battle-view type in its inheritance chain,
            # rather than treating arbitrary lobby/settings Wulf views as overlays.
            if not any(read(cls, '__module__', '').startswith('gui.impl.battle.') for cls in type(view).__mro__):
                return False
            resource = call(gameface, 'res_id_by_key', resource_key)
            return isinstance(resource, (int, float)) and not isinstance(resource, bool) and resource > 0 and resource == read(view, 'layoutID')
        except Exception:
            return False


battle_capabilities = BattleCapabilities()
current_mode = battle_capabilities.current_mode
is_random = battle_capabilities.is_random
is_comp7 = battle_capabilities.is_comp7
is_frontline = battle_capabilities.is_frontline
is_replay = battle_capabilities.is_replay
is_event = battle_capabilities.is_event
is_white_tiger = battle_capabilities.is_white_tiger
is_special = battle_capabilities.is_special
is_spg = battle_capabilities.is_spg
is_in_battle = battle_capabilities.is_in_battle
supports_gameface_overlay = battle_capabilities.supports_gameface_overlay
