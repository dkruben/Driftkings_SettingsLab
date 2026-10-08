# -*- coding: utf-8 -*-
from Driftkings._constants import BANKS_LOADER
from Driftkings.common import ConfigNoInterface
from Driftkings.settings.templates.base import ComponentSettings


class BanksLoaderSettings(ConfigNoInterface, ComponentSettings):
    COMPONENT = BANKS_LOADER.ID
