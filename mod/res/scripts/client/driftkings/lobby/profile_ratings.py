# -*- coding: utf-8 -*-
"""Independent native service-record ratings component."""
from driftkings.settings.definitions.lobby.profile_ratings import ProfileRatingsSettings

profile_ratings_settings = ProfileRatingsSettings()


def init():
    from driftkings.flash.lobby.profile_statistics import install as install_statistics
    from driftkings.gameface.lobby.profile_ratings import install
    install()
    install_statistics()
