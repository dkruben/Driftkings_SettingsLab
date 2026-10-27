# -*- coding: utf-8 -*-
"""Hide additional battle visuals while the native roster is open."""
import weakref


class HudVisibility(object):
    def __init__(self):
        self.views = weakref.WeakSet()
        self.blockers = set()
        self.active = False
        self.hooked = False

    @property
    def visible(self):
        return not self.blockers

    def attach(self, view):
        self.views.add(view)
        view.setBattleHudVisible(self.visible)

    def detach(self, view):
        self.views.discard(view)

    def block(self, source, shown):
        previous = self.visible
        if shown:
            self.blockers.add(source)
        else:
            self.blockers.discard(source)
        if self.visible != previous:
            self.publish()

    def publish(self):
        for view in tuple(self.views):
            view.setBattleHudVisible(self.visible)

    def reset(self, *args):
        self.blockers.clear()
        self.publish()

    def start(self):
        if self.active:
            return
        self.active = True
        from driftkings.core.battle_events import battleEvents
        if not self.hooked:
            self.installHooks()
            self.hooked = True
        battleEvents.ended.connect(self.reset)

    def installHooks(self):
        # Core service hooks have their own lifecycle, like BattleEvents.
        from driftkings.flash.battle.hud_visibility import install as install_flash
        install_flash(self)
        from driftkings.gameface.battle.hud_visibility import install
        install(self)

    def stop(self):
        if not self.active:
            return
        from driftkings.core.battle_events import battleEvents
        battleEvents.ended.disconnect(self.reset)
        self.active = False
        self.reset()
        self.views.clear()


hudVisibility = HudVisibility()
