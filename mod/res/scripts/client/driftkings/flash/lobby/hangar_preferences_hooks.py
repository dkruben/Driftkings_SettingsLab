# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, HANGAR_PREFERENCES
from driftkings.settings.service import settings_service

"""Presentation adapter for HangarOptions; gameplay state stays in its component."""
from importlib import import_module

from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique

from driftkings.core.hooks import override


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.lobby.hangar_preferences')


@override(Hangar, 'as_setPrestigeWidgetVisibleS')
def new__setPrestigeWidgetVisibleS(func, self, value):
    settings = settings_service.getComponentDict(_component().config)
    if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_HANGAR_PRESTIGE_WIDGET, True):
        value = False
    return func(self, value)


@override(ProfileTechnique, 'as_setPrestigeVisibleS')
def new__setPrestigeVisibleS(func, self, value):
    settings = settings_service.getComponentDict(_component().config)
    if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_PROFILE_PRESTIGE_WIDGET, True):
        value = False
    return func(self, value)


@override(Hangar, 'as_setEventTournamentBannerVisibleS')
def new__setEventTournamentBannerVisibleS(func, self, alias, visible):
    settings = settings_service.getComponentDict(_component().config)
    if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_EVENT_TOURNAMENT_WIDGET, True):
        visible = False
    return func(self, alias, visible)


@override(AmmunitionPanel, 'as_setCustomizationBtnCounterS')
def new__setCustomizationBtnCounterS(func, self, value):
    settings = settings_service.getComponentDict(_component().config)
    if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.SHOW_BUTTON_COUNTERS, True):
        value = 0
    return func(self, value)


@override(Hangar, 'as_updateCarouselEventEntryStateS')
def new__updateCarouselEventEntryStateS(func, self, isVisible):
    settings = settings_service.getComponentDict(_component().config)
    if settings.get(GLOBAL.ENABLED, True) and not settings.get(HANGAR_PREFERENCES.LOOT_BOXES_WIDGET, True):
        isVisible = False
    return func(self, isVisible)


