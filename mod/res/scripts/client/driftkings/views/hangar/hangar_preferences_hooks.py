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


from gui.impl.gen import R
from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
from gui.impl.lobby.page.prem_shop_presenter import PremShopPresenter
from gui.impl.lobby.page.referral_program_presenter import ReferralProgramPresenter
from gui.impl.lobby.user_missions.hangar_widget.presenters.event_banners_presenter import EventBannersPresenter
# WoT 2.4.1 Gameface equivalents; legacy hooks above remain for old views.
from gui.impl.lobby.user_missions.hangar_widget.presenters.quests_presenter import QuestsPresenter
from gui.impl.pub import ViewImpl


def option(key, default=True):
    data = settings_service.getComponentDict(_component().config)
    return not data.get(GLOBAL.ENABLED, True) or bool(data.get(key, default))


@override(QuestsPresenter, 'isVisible')
def quests_visible(base, self):
    return option(HANGAR_PREFERENCES.SHOW_DAILY_QUEST_WIDGET) and base(self)


@override(EventBannersPresenter, 'isVisible')
def events_visible(base, self):
    return option(HANGAR_PREFERENCES.SHOW_EVENT_BANNER) and base(self)


@override(RandomHangar, '_getChildComponents')
def hangar_children(base, self):
    children = dict(base(self))
    if not option(HANGAR_PREFERENCES.LOOT_BOXES_WIDGET):
        children.pop(R.aliases.hangar.shared.LootboxEntryPoint(), None)
    return children


@override(PremShopPresenter, '_PremShopPresenter__onPremShopUpdate')
def shop_visible(base, self):
    result = base(self)
    if not option('showPremiumShopButton'):
        self.viewModel.setIsPremiumShop(False)
    return result


@override(ReferralProgramPresenter, '_ReferralProgramPresenter__updateModel')
def referral_visible(base, self, *args):
    result = base(self, *args)
    if not option('showReferralButton'):
        self.viewModel.setEnabled(False)
    return result


@override(ReferralProgramPresenter, '_ReferralProgramPresenter__onReferralStateChanged')
def referral_state(base, self):
    result = base(self)
    if not option('showReferralButton'):
        self.viewModel.setEnabled(False)
    return result


@override(ViewImpl, 'createToolTip')
def hangar_tooltips(base, self, *args, **kwargs):
    # Limit this option to modern hangar/header/footer views, never battle UI.
    module = type(self).__module__
    data = settings_service.getComponentDict(_component().config)
    if data.get(GLOBAL.ENABLED, True) and data.get(HANGAR_PREFERENCES.HIDE_BTN_COUNTERS, False) and module.startswith((
            'gui.impl.lobby.hangar.', 'gui.impl.lobby.page.')):
        return None
    return base(self, *args, **kwargs)
