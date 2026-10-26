# -*- coding: utf-8 -*-
"""Independent native service-record ratings component."""
from driftkings.settings.definitions.lobby.profile_ratings import ProfileRatingsSettings

config = ProfileRatingsSettings()


def init():
    from driftkings.gameface.hangar.profile_ratings import install
    from driftkings.views.hangar.profile_statistics import install as install_statistics
    install()
    install_statistics()
