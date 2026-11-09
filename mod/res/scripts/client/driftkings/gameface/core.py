# -*- coding: utf-8 -*-
"""Owned UI lifecycle connected to the Gameface dependency required by ModList."""
from frameworks.wulf import ViewModel
from gui.impl.gen import R
from openwg_gameface import gf_mod_inject

from driftkings.interface_catalog import GAMEFACE, gameface_spec

# WG's native invalid resource sentinel; gui.impl.gen_utils was removed.
INVALID_RES_ID = -1

BOOTSTRAP = 'coui://gui/gameface/mods/driftkings/shared/bootstrap.js'


def resource_id(key):
    # WG 2.4.1 loads gui/gen_resources declarations into the native R tree.
    # Keep the existing callers' slash-separated keys within our own subtree.
    if key not in set(spec['resource'] for spec in GAMEFACE.values()):
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


def attach_assets(model, name):
    spec = gameface_spec(name)
    if spec['owner'] is None:
        raise ValueError('Standalone layouts load their own assets: ' + name)
    model._addViewModelProperty('DriftkingsUI', AssetsModel(name))
    # Ordered assets and disposal ownership come from the generated catalog.
    gf_mod_inject(model, name + 'Bridge', scripts=[BOOTSTRAP])


def payload_model(feature, commands=()):
    """ViewModel class with a JSON 'payload' string, the named commands and the feature's assets."""
    class PayloadModel(ViewModel):
        def __init__(self):
            super(PayloadModel, self).__init__(properties=3, commands=len(commands))

        def _initialize(self):
            super(PayloadModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            for command in commands:
                setattr(self, command, self._addCommand(command))
            attach_assets(self, feature)
    return PayloadModel


def native_payload_model(feature):
    """Clock PoC: publish metadata/data without requesting OpenWG injection."""
    if gameface_spec(feature).get('transport') != 'native_user_missions':
        raise ValueError('Feature has no native plugin transport: ' + feature)

    class NativePayloadModel(ViewModel):
        def __init__(self):
            super(NativePayloadModel, self).__init__(properties=2, commands=0)

        def _initialize(self):
            super(NativePayloadModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self._addViewModelProperty('DriftkingsUI', AssetsModel(feature))
    return NativePayloadModel
