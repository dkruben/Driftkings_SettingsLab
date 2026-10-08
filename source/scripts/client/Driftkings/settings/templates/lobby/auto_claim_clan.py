# -*- coding: utf-8 -*-
from Driftkings._constants import AUTO_CLAIM_CLAN
from Driftkings.settings.templates.base import ComponentSettings


class AutoClaimClanSettings(ComponentSettings):
    COMPONENT = AUTO_CLAIM_CLAN.ID

    TRANSLATED_TITLE = True
    COLUMNS = ((),(),)
