# -*- coding: utf-8 -*-
"""Fail-closed, read-only install policy using the existing client context."""
from Driftkings.core.battle_capabilities import battle_capabilities


class InstallContext(object):
    def __init__(self, lobby, loader, hangar, replay, capabilities=battle_capabilities):
        self.lobby, self.loader, self.hangar = lobby, loader, hangar
        self.replay, self.capabilities = replay, capabilities
        self._subscriptions = []

    def subscribe(self, callback):
        if self._subscriptions:
            return
        for name in ('onSpaceCreating', 'onSpaceCreate', 'onSpaceDestroy', 'onVehicleChangeStarted',
                     'onVehicleChanged', 'onSpaceRefreshCompleted'):
            event = getattr(self.hangar, name, None)
            if event is not None:
                event += callback
                self._subscriptions.append((event, callback))

    def unsubscribe(self, callback):
        for event, handler in self._subscriptions:
            event -= handler
        self._subscriptions = []

    def blocked_reason(self, space):
        try:
            if space != self.lobby or self.loader.getSpaceID() != self.lobby:
                return 'unsafeContext'
            if self.capabilities.player() is None:
                return 'unknownContext'
            if self.capabilities.is_in_battle() is not False:
                return 'battleContext'
            if self.capabilities.current_mode() != 'hangar':
                return 'unknownContext'
            playing, loading = self.replay.isPlaying(), self.replay.isLoading()
            if playing is True or loading is True:
                return 'replayContext'
            if playing is not False or loading is not False:
                return 'unknownContext'
            if (self.hangar.inited is not True or self.hangar.spaceInited is not True or
                    self.hangar.isModelLoaded is not True):
                return 'loadingContext'
            return None
        except Exception:
            return 'unknownContext'


def runtime_context():
    import BattleReplay
    from helpers import dependency
    from gui.shared.personality import ServicesLocator
    from skeletons.gui.app_loader import GuiGlobalSpaceID
    from skeletons.gui.shared.utils import IHangarSpace
    return InstallContext(GuiGlobalSpaceID.LOBBY, ServicesLocator.appLoader,
                          dependency.instance(IHangarSpace), BattleReplay)
