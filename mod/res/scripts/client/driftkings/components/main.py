# -*- coding: utf-8 -*-
"""General (main) settings shared by the whole mod, starting with the hangar clock."""
from driftkings.logger import get_logger
from driftkings.settings.definitions.components.main import MainSettings as Settings
from driftkings.gameface.lobby.main import ClockController, install_clock_gameface

LOG = get_logger('driftkings.components.main')

config = Settings()

# Hangar clock: one Gameface child per hangar, no global Flash timer.

g_clockController = ClockController()


def init():
    try:
        install_clock_gameface()
        g_clockController.start()
    except Exception:
        LOG.error('Gameface clock integration unavailable; rebuild the Driftkings UI resources')


def fini():
    g_clockController.stop()
