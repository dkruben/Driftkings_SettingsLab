# -*- coding: utf-8 -*-
"""Native Gameface hangar preference hooks; gameplay stays in the component."""
from importlib import import_module

from driftkings._constants import GLOBAL, HANGAR_PREFERENCES
from driftkings.core.hooks import override
from driftkings.settings.service import settings_service


def _component():
    return import_module('driftkings.lobby.hangar_preferences')


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
