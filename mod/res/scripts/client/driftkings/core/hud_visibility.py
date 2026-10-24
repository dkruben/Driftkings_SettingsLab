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

    def nativeVisibility(self, original, page, visible, hidden):
        # Owned components are registered with DAAPI, not the native page's
        # private AS3 visibility registry. Route them to their own public API.
        from driftkings.views import BATTLE_COMPONENTS
        def route(aliases, shown):
            if aliases is None:
                return []
            native = []
            for componentAlias in aliases:
                if componentAlias not in BATTLE_COMPONENTS:
                    native.append(componentAlias)
                    continue
                component = page.components.get(componentAlias)
                if component is not None:
                    component.as_setComponentVisible(shown)
            return native
        nativeVisible = route(visible, True)
        nativeHidden = route(hidden, False)
        result = original(page, nativeVisible, nativeHidden)
        alias = getattr(page, '_fullStatsAlias', None)
        if self.active and alias:
            if alias in (hidden or ()):
                self.block('native', False)
            elif alias in (visible or ()):
                self.block('native', True)
        return result

    def start(self):
        if self.active:
            return
        self.active = True
        from driftkings.core.battle_events import battleEvents
        if not self.hooked:
            self.installHooks()
            self.hooked = True
        battleEvents.ended.connect(self.reset)

    def gamefaceShown(self, original, view, *args, **kwargs):
        result = original(view, *args, **kwargs)
        if self.active:
            self.block(view, True)
        return result

    def gamefaceHidden(self, original, view, *args, **kwargs):
        try:
            return original(view, *args, **kwargs)
        finally:
            wasShown = view in self.blockers
            self.block(view, False)
            if wasShown:
                self.block('native', False)

    def installHooks(self):
        # Core service hooks have their own lifecycle, like BattleEvents.
        from gui.Scaleform.daapi.view.meta.BattlePageMeta import BattlePageMeta

        from driftkings.core.hooks import override
        for method in ('as_setComponentsVisibilityS', 'as_setComponentsVisibilityWithFadeS'):
            override(BattlePageMeta, method, self.nativeVisibility)
        # Gameface can also close via its own lifecycle rather than a TAB key-up.
        try:
            from gui.impl.battle.battle_page.tab_view import TabView
        except ImportError:
            TabView = None
        if TabView is not None:
            override(TabView, '_onShown', self.gamefaceShown)
            override(TabView, '_onHidden', self.gamefaceHidden)
            override(TabView, '_finalize', self.gamefaceHidden)

    def stop(self):
        if not self.active:
            return
        from driftkings.core.battle_events import battleEvents
        battleEvents.ended.disconnect(self.reset)
        self.active = False
        self.reset()
        self.views.clear()


hudVisibility = HudVisibility()
