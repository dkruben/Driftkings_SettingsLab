# -*- coding: utf-8 -*-
"""Owned UI lifecycle for the native Gameface documents and windows of Driftkings."""
from frameworks.wulf import ViewModel
from gui.impl.gen import R

from driftkings.interface_catalog import GAMEFACE, gameface_spec

# WG's native invalid resource sentinel; gui.impl.gen_utils was removed.
INVALID_RES_ID = -1

BOOTSTRAP = 'coui://gui/gameface/mods/driftkings/shared/bootstrap.js'


def resource_id(key):
    from driftkings.interface_catalog import BATTLE_HUD_HOST

    # WG 2.4.1 loads gui/gen_resources declarations into the native R tree.
    # Keep the existing callers' slash-separated keys within our own subtree.
    if key not in set(spec['resource'] for spec in GAMEFACE.values()) | {BATTLE_HUD_HOST['resource']}:
        raise ValueError('Unregistered Driftkings resource key: ' + key)
    parts = key.split('/')
    if len(parts) != 4 or parts[:2] != ['mods', 'driftkings'] or not all(parts):
        raise ValueError('Unknown Driftkings resource key: ' + key)
    accessor = R
    for part in parts:
        accessor = getattr(accessor, part)
    return accessor()


class AssetsModel(ViewModel):
    def __init__(self, name):
        self._name = name
        super(AssetsModel, self).__init__(properties=1, commands=0)

    def _initialize(self):
        super(AssetsModel, self)._initialize()
        self._addStringProperty('name', self._name)


def payload_model(feature, commands=()):
    """ViewModel class with a JSON 'payload' string and the feature's assets, without external injection."""
    return native_payload_model(feature, commands)


def native_payload_model(feature, commands=()):
    """Publish metadata/data and optional Wulf commands through the native Gameface plugin."""
    if gameface_spec(feature).get('transport') not in ('native_user_missions', 'native_battle_results', 'native_document'):
        raise ValueError('Feature has no native plugin transport: ' + feature)

    class NativePayloadModel(ViewModel):
        def __init__(self):
            super(NativePayloadModel, self).__init__(properties=2, commands=len(commands))

        def _initialize(self):
            super(NativePayloadModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self._addViewModelProperty('DriftkingsUI', AssetsModel(feature))
            for command in commands:
                setattr(self, command, self._addCommand(command))
    return NativePayloadModel
