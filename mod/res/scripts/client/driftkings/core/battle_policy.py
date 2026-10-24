# -*- coding: utf-8 -*-
"""Feature restrictions, separate from passive external-mod observations."""
from driftkings.core.battle_capabilities import battle_capabilities
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.BattlePolicy')
# Features that read account progress only run where battles update it.
STATISTICS_ONLY = ('battle_marks_of_excellence', 'battle_statistics', 'high_caliber_progress')


class BattlePolicy(object):
    def __init__(self, capabilities=None):
        self.capabilities = battle_capabilities if capabilities is None else capabilities
        self._logged = {}

    def decision(self, feature, enabled=True, spg_only=False):
        context = self.capabilities
        if not enabled:
            reason = 'disabled_in_settings'
        elif not context.is_in_battle():
            reason = 'outside_battle'
        elif feature in STATISTICS_ONLY and not context.is_statistics_battle():
            reason = 'requires_statistics_battle'
        elif spg_only and not context.is_spg():
            reason = 'requires_spg'
        else:
            reason = 'allowed'
        result = (reason == 'allowed', reason)
        if self._logged.get(feature) != result:
            self._logged[feature] = result
            LOG.info('%s allowed=%s reason=%s mode=%s replay=%s',
                     feature, result[0], reason, context.current_mode(), context.is_replay())
        return result


battle_policy = BattlePolicy()
