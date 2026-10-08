# -*- coding: utf-8 -*-
from Driftkings._constants import BATTLE_EFFICIENCY, GLOBAL
from Driftkings.settings.service import settings_service
"""Presentation adapter for BattleEfficiency; gameplay state stays in its component."""
import json
import weakref
from Driftkings.core.hooks import override

from importlib import import_module


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('Driftkings.components.battle_efficiency')


def install_results_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent
    from gui.impl.gen_utils import INVALID_RES_ID
    from gui.impl.lobby.battle_results.random_battle_results_view import RandomBattleResultsView
    from helpers import dependency
    from skeletons.gui.battle_results import IBattleResultsService
    from Driftkings.ui.gameface import attach_assets, resource_id as resolve_resource

    feature = 'DriftkingsBattleEfficiency'
    resource = 'mods/Driftkings/BattleEfficiency/model'
    assets = 'coui://gui/gameface/mods/Driftkings/BattleEfficiency/'

    class ResultsModel(ViewModel):
        def __init__(self):
            super(ResultsModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(ResultsModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, feature, styles=[assets + 'results.css'], scripts=[assets + 'results.js'])

    class ResultsView(ViewComponent):
        def __init__(self, parent, resource_id):
            self._parentRef = weakref.ref(parent)
            self._ready = False
            self._lastPayload = None
            super(ResultsView, self).__init__(layoutID=resource_id, model=ResultsModel)
            _component()._results_views[parent] = self

        def _onLoading(self, *args, **kwargs):
            super(ResultsView, self)._onLoading(*args, **kwargs)
            self._ready = True
            parent = self._parentRef()
            if parent is not None:
                self.refresh(parent.arenaUniqueID)

        def _finalize(self):
            self._ready = False
            parent = self._parentRef()
            if parent is not None and _component()._results_views.get(parent) is self:
                _component()._results_views.pop(parent, None)
            super(ResultsView, self)._finalize()

        def refresh(self, arena_id):
            if not self._ready:
                return
            payload = {'enabled': False}
            try:
                if settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED] and settings_service.getComponentDict(_component().config)[BATTLE_EFFICIENCY.BATTLE_RESULTS_WINDOW]:
                    service = dependency.instance(IBattleResultsService)
                    controller = service.getStatsCtrl(arena_id)
                    battle_results = controller.getResults() if controller else None
                    if battle_results is not None:
                        payload = _component().make_results_payload(battle_results)
                    else:
                        _component().LOG.warning('No cached results available for battle %s', arena_id)
            except Exception:
                _component().LOG.exception('Could not build efficiency for battle %s', arena_id)
            if payload == self._lastPayload:
                return
            with self.getViewModel().transaction() as model:
                model._setString(0, json.dumps(payload))
            if self._lastPayload is None:
                _component().LOG.info('Gameface results ready: battle=%s enabled=%s', arena_id, payload.get('enabled', False))
            self._lastPayload = payload

    @override(RandomBattleResultsView, '_getChildComponents')
    def results_children(original, view, *args, **kwargs):
        children = dict(original(view, *args, **kwargs))
        try:
            resource_id = resolve_resource(resource)
            if resource_id == INVALID_RES_ID:
                raise RuntimeError('Missing resource map: ' + resource)
            children[resource_id] = lambda: ResultsView(view, resource_id)
        except Exception:
            _component().LOG.exception('Could not attach Gameface battle efficiency')
        return children
