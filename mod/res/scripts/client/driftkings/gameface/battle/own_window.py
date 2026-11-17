# -*- coding: utf-8 -*-
"""
One owned fullscreen Gameface window for battle cards, without OpenWG injection.
Selected per feature by 'transport': 'own_window' in the interface catalog; other battle cards stay
OpenWG children of the native battle HUD and never import this module. Every selected card shares a
single window per native battle HUD. The window follows the lifecycle of RandomHUDView and uses the
same flags and MARKER layer as the native HUD window; its neutral infrastructure document loads
the assets of all selected features once, and each renderer finds its own card
through subViews, exactly as it does inside the HUD. Each card keeps its own model, adapter and
state. The neutral host identity awaits CT validation."""
import weakref

# Installed cards, in installation order: (adapter, card view type).
_cards = []
# RandomHUDView -> the single owned window of that HUD.
_windows = weakref.WeakKeyDictionary()
_types = {}


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


def _window_type():
    if 'window' in _types:
        return _types['window']
    from frameworks.wulf import WindowFlags, WindowLayer
    from gui.impl.gen import R
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.pub.window_impl import WindowImpl

    class HostView(ViewComponent):
        """Root of the owned document. The cards are its children, as they were children of the HUD."""
        def __init__(self, resource):
            super(HostView, self).__init__(layoutID=resource)

        def _getChildComponents(self):
            result = {}
            for adapter, card_type in list(_cards):
                try:
                    resource = adapter.resourceID()
                    if resource == -1 or resource in result:
                        adapter.log.warning('%s battle resource is unavailable or already has an owner', adapter.title)
                        continue
                    result[resource] = self._factory(adapter, card_type)
                except Exception:
                    adapter.log.exception('Could not attach %s to the own battle window', adapter.title)
            return result

        def _factory(self, adapter, card_type):
            host = self

            def create():
                # Like the client's own sub-view presenters: the position key identifies the card,
                # its layout is the empty alias. Only the root view owns the layout document.
                try:
                    child = card_type(R.aliases.common.none())
                except Exception:
                    # One failing card must not take the window and the other cards with it.
                    adapter.log.exception('Could not create the %s battle panel', adapter.title)
                    return None
                adapter.views[host] = child
                adapter.log.info('Gameface battle panel created in its own window')
                return child
            return create

    class HostWindow(WindowImpl):
        def __init__(self, resource):
            # Same flags and layer as the native battle HUD window.
            super(HostWindow, self).__init__(WindowFlags.WINDOW | WindowFlags.WINDOW_FULLSCREEN,
                                             content=HostView(resource), layer=WindowLayer.MARKER)
    _types['window'] = HostWindow
    return HostWindow


def _close(hud, log):
    window = _windows.pop(hud, None)
    if window is not None:
        try:
            window.destroy()
        except Exception:
            log.exception('Own battle window destroy failed; handle removed without retry; '
                          'window release not confirmed (window=%r)', window)


def _open(hud, log):
    """Create the window of this HUD once; every selected feature calls this from its own hook."""
    if hud in _windows:
        return
    try:
        from driftkings.gameface.core import resource_id
        from driftkings.interface_catalog import BATTLE_HUD_HOST
        resource = resource_id(BATTLE_HUD_HOST['resource'])
        if resource == -1:
            log.warning('Own battle window document is unavailable')
            return
        window = _windows[hud] = _window_type()(resource)
        window.load()
        log.info('Own battle window loading; OpenWG injection not requested (%d panels)', len(_cards))
    except Exception:
        log.exception('Could not create the own battle window')
        _close(hud, log)


def install(adapter, card_type):
    """Add the card to the shared window; the adapter keeps publishing through adapter.views."""
    from gui.impl.battle.random.hud import RandomHUDView

    from driftkings.core.hooks import override

    if not any(card[0] is adapter for card in _cards):
        _cards.append((adapter, card_type))
    adapter.ownWindows = _windows

    def loading(original, hud, *args, **kwargs):
        result = original(hud, *args, **kwargs)
        _open(hud, adapter.log)
        return result

    def finalize(original, hud, *args, **kwargs):
        _close(hud, adapter.log)
        return original(hud, *args, **kwargs)

    dispose = adapter.dispose
    disposing = [False]

    def dispose_card():
        # The adapter destroys its own card; the window goes with the last card.
        if disposing[0] or not any(card[0] is adapter for card in _cards):
            return
        disposing[0] = True
        try:
            try:
                dispose()
            except Exception:
                adapter.log.exception('%s adapter dispose failed; retiring registration; release not confirmed',
                                      adapter.title)
        finally:
            try:
                _cards[:] = [card for card in _cards if card[0] is not adapter]
                if not _cards:
                    for hud in list(_windows.keys()):
                        _close(hud, adapter.log)
            finally:
                disposing[0] = False
    adapter.dispose = dispose_card

    for name, handler in (('_onLoading', loading), ('_finalize', finalize)):
        # Hooks run only while their owner is active, so each feature declares its own pair: the
        # window is created by whichever selected feature is active, and only once per HUD.
        setattr(handler, '__module__', adapter.__class__.__module__)
        override(RandomHUDView, name)(handler)
