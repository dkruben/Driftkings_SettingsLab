# -*- coding: utf-8 -*-
"""Create library components when the client loads a native battle page."""
import BigWorld
from frameworks.wulf import WindowLayer
from gui.app_loader.settings import APP_NAME_SPACE
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS, VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE
from gui.Scaleform.framework.package_layout import PackageBusinessHandler
from gui.shared import EVENT_BUS_SCOPE

from driftkings.flash.batalha.registry import BATTLE_COMPONENTS, BATTLE_HANDLERS
from driftkings.interface_catalog import selected_components, surface_aliases
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Views')


def battlePageAliases():
    pages = set(VIEW_ALIAS.BATTLE_PAGES)
    # Each WG configuration contains separate page/HUD aliases; Wulf-only
    # layouts may leave the page slot empty. Listen for every actual alias.
    for config in VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE.values():
        pages.update(alias for alias in config if alias is not None)
    # Some client extensions declare their aliases before extending the mapping.
    for name in ('COMP7_BATTLE_PAGE', 'COMP7_LIGHT_BATTLE_PAGE',
                 'STRONGHOLD_BATTLE_PAGE', 'EPIC_RANDOM_PAGE'):
        alias = getattr(VIEW_ALIAS, name, None)
        if alias is not None:
            pages.add(alias)
    return tuple(sorted(pages))


def battlePageCandidates(alias):
    # The 2.4.1 Wulf HUD event follows the legacy Scaleform page event.
    # It must not redirect our Flash component factory onto the Wulf HUD.
    # Client extensions can register a page-only tuple, without a Wulf HUD.
    pages = [config[0] for config in VIEW_BATTLE_PAGE_CONFIG_BY_ARENA_GUI_TYPE.values()
             if len(config) >= 2 and config[1] == alias and config[0] is not None]
    result = []
    for page in sorted(set(pages)) + [alias]:
        if page not in result:
            result.append(page)
    return tuple(result)


class BattleViewHandler(PackageBusinessHandler):
    def __init__(self):
        listeners = tuple((alias, self.onPageLoading) for alias in battlePageAliases())
        super(BattleViewHandler, self).__init__(listeners, appNS=APP_NAME_SPACE.SF_BATTLE,
                                               scope=EVENT_BUS_SCOPE.BATTLE)
        self.pending = None
        self.pageAlias = None
        self.attempts = 0
        self.active = False
        self.reportedError = False

    def init(self):
        super(BattleViewHandler, self).init()
        self.active = True
        BATTLE_HANDLERS.add(self)

    def fini(self):
        self.close()
        super(BattleViewHandler, self).fini()

    def close(self):
        self.active = False
        self._cancel()
        self.pageAlias = None
        BATTLE_HANDLERS.discard(self)

    def _cancel(self):
        if self.pending is not None:
            BigWorld.cancelCallback(self.pending)
            self.pending = None

    def onPageLoading(self, event):
        if not self.active:
            return
        if self.pending is not None and self.pageAlias in battlePageCandidates(event.alias):
            return
        self._cancel()
        self.pageAlias = event.alias
        self.attempts = 0
        self.reportedError = False
        # Let the client's own LOAD_VIEW handler create/reload the page first.
        self.pending = BigWorld.callback(0, self._findPage)

    def _findPage(self):
        self.pending = None
        if not self.active:
            return
        aliases = selected_components(BATTLE_COMPONENTS)
        if not aliases:
            return
        try:
            for alias in battlePageCandidates(self.pageAlias):
                view = self.findViewByAlias(WindowLayer.VIEW, alias)
                if view is not None and view._isDAAPIInited() and self.onViewFound(view, aliases):
                    return
        except Exception:
            if not self.reportedError:
                LOG.exception('Could not create battle components on %s', self.pageAlias)
                self.reportedError = True
        self.attempts += 1
        if self.attempts < 80:
            self.pending = BigWorld.callback(0.1, self._findPage)
        else:
            LOG.warning('Battle library not ready on page %s after 80 attempts', self.pageAlias)

    def onViewFound(self, view, aliases):
        battle = hasattr(view.flashObject, 'as_DriftkingsCreate')
        method = 'as_DriftkingsCreate' if battle else 'as_DriftkingsCreateRatings'
        requested = surface_aliases(aliases, 'battle' if battle else 'ratings')
        if not requested:
            return False
        missing = [alias for alias in requested if not view.isFlashComponentRegistered(alias)]
        if not missing:
            return True
        if not hasattr(view.flashObject, method):
            return False
        getattr(view.flashObject, method)(missing)
        if battle and getattr(view, '_isBattleLoading', False):
            # Keep the existing DAAPI visibility routing for owned components.
            registered = [alias for alias in missing if view.isFlashComponentRegistered(alias)]
            view.as_setComponentsVisibilityS(None, registered)
            view._blToggling.update(registered)
        return all(view.isFlashComponentRegistered(alias) for alias in requested)
