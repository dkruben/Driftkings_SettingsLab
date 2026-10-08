# -*- coding: utf-8 -*-
from Driftkings._constants import ACCOUNT_MANAGER
from Driftkings.common import ConfigNoInterface
from Driftkings.settings.templates.base import ComponentSettings


class AccountManagerSettings(ConfigNoInterface, ComponentSettings):
    COMPONENT = ACCOUNT_MANAGER.ID
