# -*- coding: utf-8 -*-
"""An owned fullscreen Gameface window for a battle card, without OpenWG injection.

Selected per feature by 'transport': 'own_window' in the interface catalog; other battle cards stay
OpenWG children of the native battle HUD and never import this module. The window follows the
lifecycle of RandomHUDView and uses the same flags and MARKER layer as the native HUD window; its
layout document loads the feature's own assets and finds the card through subViews, exactly as the
renderer does inside the HUD. Validated in CT 2.4.2.0 #995 for DriftkingsTeamStrength."""
import weakref


def payload_model(feature, commands=()):
    """The card model of gameface.core.payload_model without the OpenWG injection."""
    from frameworks.wulf import ViewModel

    from driftkings.gameface.core import AssetsModel

    class OwnWindowModel(ViewModel):
        def __init__(self):
            super(OwnWindowModel, self).__init__(properties=2, commands=len(commands))

        def _initialize(self):
            super(OwnWindowModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            for command in commands:
                setattr(self, command, self._addCommand(command))
            self._addViewModelProperty('DriftkingsUI', AssetsModel(feature))
    return OwnWindowModel


def install(adapter, card_type):
    """One owned window per native battle HUD; the adapter keeps publishing through adapter.views."""
    from frameworks.wulf import WindowFlags, WindowLayer
    from gui.impl.battle.random.hud import RandomHUDView
    from gui.impl.gen import R
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.pub.window_impl import WindowImpl

    from driftkings.core.hooks import override

    windows = adapter.ownWindows = weakref.WeakKeyDictionary()

    class HostView(ViewComponent):
        """Root of the owned document. The card is its only child, as it was a child of the HUD."""
        def __init__(self, resource):
            self._cardResource = resource
            super(HostView, self).__init__(layoutID=resource)

        def _getChildComponents(self):
            host = self

            def create():
                # Like the client's own sub-view presenters: the position key identifies the card,
                # its layout is the empty alias. Only the root view owns the layout document.
                child = card_type(R.aliases.common.none())
                adapter.views[host] = child
                adapter.log.info('Gameface battle panel created in its own window')
                return child
            return {self._cardResource: create}

    class HostWindow(WindowImpl):
        def __init__(self, resource):
            # Same flags and layer as the native battle HUD window.
            super(HostWindow, self).__init__(WindowFlags.WINDOW | WindowFlags.WINDOW_FULLSCREEN,
                                             content=HostView(resource), layer=WindowLayer.MARKER)

    def close(hud):
        window = windows.pop(hud, None)
        if window is not None:
            try:
                window.destroy()
            except Exception:
                adapter.log.exception('Could not destroy the own %s battle window', adapter.title)

    def loading(original, hud, *args, **kwargs):
        result = original(hud, *args, **kwargs)
        try:
            if hud in windows:
                adapter.log.warning('%s own battle window already exists', adapter.title)
                return result
            resource = adapter.resourceID()
            if resource == -1:
                adapter.log.warning('%s battle resource is unavailable', adapter.title)
                return result
            window = windows[hud] = HostWindow(resource)
            window.load()
            adapter.log.info('Own battle window loading; OpenWG injection not requested')
        except Exception:
            adapter.log.exception('Could not create the own %s battle window', adapter.title)
            close(hud)
        return result

    def finalize(original, hud, *args, **kwargs):
        close(hud)
        return original(hud, *args, **kwargs)

    dispose = adapter.dispose

    def dispose_all():
        dispose()
        for hud in list(windows.keys()):
            close(hud)
    adapter.dispose = dispose_all

    for name, handler in (('_onLoading', loading), ('_finalize', finalize)):
        # Like the shared installer, these hooks are declared on behalf of the feature.
        setattr(handler, '__module__', adapter.__class__.__module__)
        override(RandomHUDView, name)(handler)
