# -*- coding: utf-8 -*-
from driftkings._constants import SERVER_TURRET_SYNC
from driftkings.settings.controls_schema import control
from driftkings.settings.definitions.base import SectionDefinition


class ServerTurretSyncSettings(SectionDefinition):
    NAME = SERVER_TURRET_SYNC.NAME

    TRANSLATED_TITLE = True
    COLUMNS = ((control(SERVER_TURRET_SYNC.SERVER_TURRET),
                control(SERVER_TURRET_SYNC.ACTIVATE_MESSAGE)), ())
