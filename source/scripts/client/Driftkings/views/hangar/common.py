# -*- coding: utf-8 -*-
"""Shared lifecycle for component-owned Gameface hangar cards."""
import json
import weakref


class HangarController(object):
    def __init__(self):
        self.views = weakref.WeakKeyDictionary()
        self.visible = weakref.WeakKeyDictionary()

    def onApplySettings(self, changes=None):
        for child in list(self.views.values()):
            handler = getattr(child, 'refreshSettings', None)
            if changes is not None and handler is not None:
                handler(changes)
            else:
                child.refresh()

    def setVisible(self, parent, visible):
        self.visible[parent] = visible
        child = self.views.get(parent)
        if child is not None:
            child.refresh()


def card_payload(previous, config_only, visible, config, build):
    """Reuse vehicle data for layout changes; rebuild after a hidden state."""
    if visible and config_only and previous and previous.get('config', {}).get('visible'):
        payload = dict(previous)
        payload['config'] = config()
    else:
        payload = build() if visible else {'config': config()}
    payload['config']['visible'] = visible
    return payload


def publish_card(view, payload):
    """Publish only changed output, committing the cache after the transaction."""
    if view._lastPayload == payload:
        return False
    encoded = json.dumps(payload, separators=(',', ':'), allow_nan=False)
    with view.getViewModel().transaction() as model:
        model._setString(0, encoded)
    view._lastPayload = payload
    return True


def install_card(component, view_type, owner):
    from gui.impl.gen_utils import INVALID_RES_ID
    from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
    from Driftkings.core.hooks import override
    from Driftkings.ui.gameface import resource_id as resolve_resource

    def get_children(original, parent, *args, **kwargs):
        children = dict(original(parent, *args, **kwargs))
        try:
            resource_id = resolve_resource(component().RESOURCE)
            if resource_id == INVALID_RES_ID:
                component().LOG.warning('Missing Gameface resource: %s. Rebuild the Driftkings resource map for this client.', component().RESOURCE)
            else:
                children[resource_id] = lambda: view_type(parent, resource_id)
        except Exception:
            component().LOG.exception('Could not attach Gameface hangar card')
        return children

    def on_shown(original, parent, *args, **kwargs):
        result = original(parent, *args, **kwargs)
        component().g_controller.setVisible(parent, True)
        return result

    def on_hidden(original, parent, *args, **kwargs):
        component().g_controller.setVisible(parent, False)
        return original(parent, *args, **kwargs)

    for name, handler in (('_getChildComponents', get_children),
                          ('_onShown', on_shown), ('_onHidden', on_hidden)):
        # Each card keeps its own hook owner and can be disabled independently.
        handler.__module__ = owner
        override(RandomHangar, name)(handler)
