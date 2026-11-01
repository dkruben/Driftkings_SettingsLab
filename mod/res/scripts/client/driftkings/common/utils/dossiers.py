# -*- coding: utf-8 -*-
"""Shared reads of WG vehicle dossiers, and the dossier behind each slotted achievement."""
from collections import OrderedDict

from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement

from driftkings.common.utils.numbers import nonnegative_number, ratio
from driftkings.core.hooks import override

_dossiers = OrderedDict()
_MAX_DOSSIERS = 256


def total_record(dossier, name):
    """Raw value of a record in the dossier's total achievement block (marksOnGun, movingAvgDamage...)."""
    return dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, name)


def damage_rating(dossier):
    """Mark-of-excellence percentage; the dossier stores hundredths."""
    return total_record(dossier, 'damageRating') / 100.0


def mastery_achievement(dossier):
    """The earned mastery badge achievement, or None."""
    mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
    return mastery if mastery is not None and mastery.isInDossier() else None


def mastery_rank(dossier):
    """Mastery badge 1-4, or 0. ClassProgressAchievement.NO_LVL is 5; clamping would turn it into Ace (4)."""
    mastery = mastery_achievement(dossier)
    rank = mastery.getValue() if mastery is not None else 0
    return int(rank) if rank in (1, 2, 3, 4) else 0


def average_assists(stats):
    """Per-battle track, radio and stun assistance, as the native profile shows them."""
    track = stats._getAvgValue(stats.getBattlesCountVer2, stats.getDamageAssistedTrack)
    radio = stats._getAvgValue(stats.getBattlesCountVer2, stats.getDamageAssistedRadio)
    return track, radio, stats.getAvgDamageAssistedStun()


def wnx_assistance(stats):
    """Radio + track + stun per battle for WNX; None when any total is missing."""
    totals = [nonnegative_number(getattr(stats, method)())
              for method in ('getDamageAssistedRadio', 'getDamageAssistedTrack', 'getDamageAssistedStun')]
    return ratio(sum(totals), stats.getBattlesCountVer2()) if None not in totals else None


@override(MarkOnGunAchievement, '__init__')
def _rememberDossier(func, self, dossier, value=None):
    result = func(self, dossier, value)
    _dossiers[id(self)] = (self, dossier)
    while len(_dossiers) > _MAX_DOSSIERS:
        _dossiers.popitem(last=False)
    return result


def getAchievementDossier(achievement):
    item = _dossiers.get(id(achievement))
    return item[1] if item is not None and item[0] is achievement else None


class DossierService(object):
    def start(self):
        pass

    def stop(self):
        _dossiers.clear()
