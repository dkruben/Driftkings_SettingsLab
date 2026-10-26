# -*- coding: utf-8 -*-
"""Shared, transactional publication for owned Gameface cards."""
import json


def publish_card(view, payload):
    """Publish only changed output, committing the cache after the transaction."""
    if view._lastPayload == payload:
        return False
    encoded = json.dumps(payload, separators=(',', ':'), allow_nan=False)
    with view.getViewModel().transaction() as model:
        model._setString(0, encoded)
    view._lastPayload = payload
    return True


