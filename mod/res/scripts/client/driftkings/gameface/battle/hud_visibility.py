# -*- coding: utf-8 -*-
"""Native TAB lifecycle feeds the shared HUD visibility service."""
from driftkings.core.hooks import override


def install(visibility):
    # Keep the service's original hook owner and activation lifetime.
    try:
        from gui.impl.battle.battle_page.tab_view import TabView
    except ImportError:
        return

    def shown(original, view, *args, **kwargs):
        result = original(view, *args, **kwargs)
        if visibility.active:
            visibility.block(view, True)
        return result

    def hidden(original, view, *args, **kwargs):
        try:
            return original(view, *args, **kwargs)
        finally:
            wasShown = view in visibility.blockers
            visibility.block(view, False)
            if wasShown:
                visibility.block('native', False)

    for handler in (shown, hidden):
        setattr(handler, '__module__', type(visibility).__module__)
    override(TabView, '_onShown', shown)
    override(TabView, '_onHidden', hidden)
    override(TabView, '_finalize', hidden)
