# -*- coding: utf-8 -*-
"""Owned UI lifecycle connected to the Gameface dependency required by ModList."""
import json

from frameworks.wulf import ViewModel
from openwg_gameface import gf_mod_inject, res_id_by_key

BOOTSTRAP = 'coui://gui/gameface/mods/Driftkings/shared/bootstrap.js'


def resource_id(key):
    # Resolve the map actually loaded by OpenWG, including other mods' resources.
    return res_id_by_key(key)


class AssetsModel(ViewModel):
    def __init__(self, name, styles, scripts):
        self._name = name
        self._styles = json.dumps(styles or [])
        self._scripts = json.dumps(scripts or [])
        super(AssetsModel, self).__init__(properties=3, commands=0)

    def _initialize(self):
        super(AssetsModel, self)._initialize()
        self._addStringProperty('name', self._name)
        self._addStringProperty('styles', self._styles)
        self._addStringProperty('scripts', self._scripts)


def attach_assets(model, name, styles=None, scripts=None):
    model._addViewModelProperty('DriftkingsUI', AssetsModel(name, styles, scripts))
    # OpenWG injects only our bootstrap; it retains ordered loading and cleanup.
    gf_mod_inject(model, name + 'Bridge', scripts=[BOOTSTRAP])
