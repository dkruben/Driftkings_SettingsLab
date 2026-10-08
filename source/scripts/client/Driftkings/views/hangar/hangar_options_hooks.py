# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, HANGAR_OPTIONS
from Driftkings.settings.service import settings_service
"""Presentation adapter for HangarOptions; gameplay state stays in its component."""
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from gui.Scaleform.daapi.view.lobby.hangar.ammunition_panel import AmmunitionPanel
from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique
from Driftkings.core.hooks import override

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.lobby.hangar_options')


@override(Hangar, 'as_setPrestigeWidgetVisibleS')
def new__setPrestigeWidgetVisibleS(func, self, value):
    if settings_service.getComponentDict(_component().config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(_component().config).get(HANGAR_OPTIONS.SHOW_HANGAR_PRESTIGE_WIDGET, True):
        value = False
    return func(self, value)


@override(ProfileTechnique, 'as_setPrestigeVisibleS')
def new__setPrestigeVisibleS(func, self, value):
    if settings_service.getComponentDict(_component().config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(_component().config).get(HANGAR_OPTIONS.SHOW_PROFILE_PRESTIGE_WIDGET, True):
        value = False
    return func(self, value)


@override(Hangar, 'as_setEventTournamentBannerVisibleS')
def new__setEventTournamentBannerVisibleS(func, self, alias, visible):
    if settings_service.getComponentDict(_component().config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(_component().config).get(HANGAR_OPTIONS.SHOW_EVENT_TOURNAMENT_WIDGET, True):
        visible = False
    return func(self, alias, visible)


@override(AmmunitionPanel, 'as_setCustomizationBtnCounterS')
def new__setCustomizationBtnCounterS(func, self, value):
    if settings_service.getComponentDict(_component().config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(_component().config).get(HANGAR_OPTIONS.SHOW_BUTTON_COUNTERS, True):
        value = 0
    return func(self, value)


@override(Hangar, 'as_updateCarouselEventEntryStateS')
def new__updateCarouselEventEntryStateS(func, self, isVisible):
    if settings_service.getComponentDict(_component().config).get(GLOBAL.ENABLED, True) and not settings_service.getComponentDict(_component().config).get(HANGAR_OPTIONS.LOOT_BOXES_WIDGET, True):
        isVisible = False
    return func(self, isVisible)
