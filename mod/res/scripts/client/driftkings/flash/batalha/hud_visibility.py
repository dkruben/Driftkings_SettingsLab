# -*- coding: utf-8 -*-
"""Route native DAAPI component visibility into the shared HUD state."""
from driftkings.core.hooks import override


def install(visibility):
    from gui.Scaleform.daapi.view.meta.BattlePageMeta import BattlePageMeta

    def nativeVisibility(original, page, visible, hidden):
        # Owned components are registered with DAAPI, not the native page's
        # private AS3 visibility registry. Route them to their own public API.
        from driftkings.flash.batalha.registry import BATTLE_COMPONENTS
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
        if visibility.active and alias:
            if alias in (hidden or ()):
                visibility.block('native', False)
            elif alias in (visible or ()):
                visibility.block('native', True)
        return result

    setattr(nativeVisibility, '__module__', type(visibility).__module__)
    for name in ('as_setComponentsVisibilityS', 'as_setComponentsVisibilityWithFadeS'):
        override(BattlePageMeta, name, nativeVisibility)
