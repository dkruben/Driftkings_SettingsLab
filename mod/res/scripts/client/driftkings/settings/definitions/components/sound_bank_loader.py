# -*- coding: utf-8 -*-
from driftkings._constants import SOUND_BANK_LOADER
from driftkings.settings.controls_schema import control
from driftkings.settings.definitions.base import SectionDefinition


class SoundBankLoaderSettings(SectionDefinition):
    NAME = SOUND_BANK_LOADER.NAME

    COLUMNS = ([control(SOUND_BANK_LOADER.DEBUG)], [])
