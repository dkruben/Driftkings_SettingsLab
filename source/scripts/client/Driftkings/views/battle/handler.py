# -*- coding: utf-8 -*-
"""Create library components when the client loads a native battle page."""
import logging

import BigWorld
from frameworks.wulf import WindowLayer
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS, VIEW_BATTLE_PAGE_ALIAS_BY_ARENA_GUI_TYPE
from gui.Scaleform.framework.package_layout import PackageBusinessHandler
from gui.app_loader.settings import APP_NAME_SPACE
from gui.shared import EVENT_BUS_SCOPE

from Driftkings.views import BATTLE_COMPONENTS, BATTLE_HANDLERS

LOG = logging.getLogger('Driftkings.Views')


def battlePageAliases():
    pages = set(VIEW_ALIAS.BATTLE_PAGES)
    pages.update(VIEW_BATTLE_PAGE_ALIAS_BY_ARENA_GUI_TYPE.values())
    # Some client extensions declare their aliases before extending the mapping.
    for name in ('COMP7_BATTLE_PAGE', 'COMP7_LIGHT_BATTLE_PAGE',
                 'STRONGHOLD_BATTLE_PAGE', 'EPIC_RANDOM_PAGE'):
        alias = getattr(VIEW_ALIAS, name, None)
        if alias is not None:
            pages.add(alias)
    return tuple(sorted(pages))


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
        aliases = [alias for alias, definition in sorted(BATTLE_COMPONENTS.items())
                   if definition[1].data.get('enabled', True)]
        if not aliases:
            return
        try:
            view = self.findViewByAlias(WindowLayer.VIEW, self.pageAlias)
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
        missing = [alias for alias in aliases if not view.isFlashComponentRegistered(alias)]
        if not missing:
            return True
        if not hasattr(view.flashObject, 'as_DriftkingsCreate'):
            return False
        view.flashObject.as_DriftkingsCreate(missing)
        if getattr(view, '_isBattleLoading', False):
            # New HUD components must be restored when native loading closes.
            view._blToggling.update(alias for alias in missing if view.isFlashComponentRegistered(alias))
        return all(view.isFlashComponentRegistered(alias) for alias in aliases)
