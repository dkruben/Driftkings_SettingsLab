# -*- coding: utf-8 -*-
"""Footer-owned settings entry point; the existing controller owns the window."""
from importlib import import_module
import json
import weakref

from gui.impl.lobby.page.lobby_footer import LobbyFooter
from gui.impl.pub.view_component import ViewComponent
from skeletons.gui.app_loader import GuiGlobalSpaceID

from driftkings.core.hooks import override
from driftkings.gameface.core import payload_model, resource_id
from driftkings.interface_catalog import gameface_spec
from driftkings.logger import get_logger

LOG = get_logger('Driftkings.Launcher')
FEATURE = 'DriftkingsFooterLauncher'
LauncherModel = payload_model(FEATURE, ('onOpen',))
# These CT variants replace _initChildren without calling the base method.
FOOTERS = (
    ('comp7.gui.impl.lobby.page.lobby_footer', 'Comp7LobbyFooter'),
    ('comp7_light.gui.impl.lobby.page.lobby_footer', 'Comp7LightLobbyFooter'),
    ('last_stand.gui.impl.lobby.page.ls_lobby_footer', 'LSLobbyFooter'),
    ('battle_royale.gui.Scaleform.daapi.view.lobby.footer.battle_royale_lobby_footer', 'BattleRoyaleLobbyFooter'),
)



class LauncherView(ViewComponent):
    def __init__(self, launcher):
        self.launcher = launcher
        super(LauncherView, self).__init__(layoutID=launcher.resource(), model=LauncherModel)

    def _onLoading(self, *args, **kwargs):
        super(LauncherView, self)._onLoading(*args, **kwargs)
        self.launcher.views.add(self)
        self.refresh()

    def _getEvents(self):
        return tuple(super(LauncherView, self)._getEvents()) + ((self.getViewModel().onOpen, self.open),)

    def open(self, *args):
        owner = self.launcher
        if owner is not None and owner.visible():
            owner.controller.open()

    def refresh(self):
        owner = self.launcher
        self.getViewModel()._setString(0, json.dumps({
            'visible': owner.visible(), 'title': owner.title}, ensure_ascii=True))

    def _finalize(self):
        if self.launcher is not None:
            self.launcher.views.discard(self)
        self.launcher = None
        super(LauncherView, self)._finalize()


class FooterLauncher(object):
    def __init__(self, controller, title):
        self.controller = controller
        self.title = title
        self.views = weakref.WeakSet()
        self.parents = weakref.WeakSet()
        self.active = False
        self.installed = False

    @staticmethod
    def resource():
        return resource_id(gameface_spec(FEATURE)['resource'])

    def visible(self):
        return bool(self.active and self.controller.space == GuiGlobalSpaceID.LOBBY)

    def start(self):
        if self.active:
            return
        self.active = True
        if not self.installed:
            owner = self

            def footer_children(original, footer, *args, **kwargs):
                result = original(footer, *args, **kwargs)
                if not owner.active:
                    return result
                child = None
                try:
                    resource = owner.resource()
                    if footer.getChildView(resource) is None:
                        child = LauncherView(owner)
                        footer.setChildView(resource, child)
                        if footer.getChildView(resource) is child:
                            owner.parents.add(footer)
                            LOG.debug('Footer launcher attached')
                        else:
                            child.destroy()
                            child = None
                            LOG.warning('Footer rejected launcher child; settings shortcut remains available')
                except Exception:
                    LOG.exception('Could not attach footer launcher; settings shortcut remains available')
                    if child is not None:
                        child.destroy()
                return result

            targets = [LobbyFooter]
            for path, name in FOOTERS:
                try:
                    targets.append(getattr(import_module(path), name))
                except ImportError:
                    LOG.debug('Optional footer unavailable: %s', path)
                except AttributeError:
                    LOG.warning('Optional footer contract unavailable: %s.%s', path, name)
            for target in targets:
                override(target, '_initChildren')(footer_children)
            self.installed = True
        self.refresh()

    def refresh(self):
        for view in tuple(self.views):
            view.refresh()

    def stop(self):
        self.active = False
        self.refresh()
        resource = self.resource()
        for parent in tuple(self.parents):
            child = parent.getChildView(resource)
            if child is not None and getattr(child, 'launcher', None) is self:
                child.destroy()
        self.parents.clear()
        self.views.clear()
