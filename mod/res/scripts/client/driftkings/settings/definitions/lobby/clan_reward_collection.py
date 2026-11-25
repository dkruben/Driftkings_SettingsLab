# -*- coding: utf-8 -*-
from driftkings._constants import CLAN_REWARD_COLLECTION
from driftkings.settings.controls_schema import control
from driftkings.settings.definitions.base import SectionDefinition


class ClanRewardCollectionSettings(SectionDefinition):
    NAME = CLAN_REWARD_COLLECTION.NAME

    TRANSLATED_TITLE = True
    # Free reward collection follows the section switch; purchases have their own explicit consent switch.
    COLUMNS = ((control(CLAN_REWARD_COLLECTION.PURCHASE_PROGRESSION),), ())
