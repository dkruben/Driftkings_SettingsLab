# -*- coding: utf-8 -*-
"""Presentation adapter for MarksOnGunTechTree; gameplay state stays in its component."""
from importlib import import_module

from frameworks.wulf import ViewModel, ViewSettings
from gui.impl.pub import ViewImpl

from driftkings.core.hooks import override
from driftkings.interface_catalog import gameface_spec


FEATURE = 'DriftkingsMarksOnGunTechTree'
RESOURCE = gameface_spec(FEATURE)['resource']


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.lobby.tech_tree_marks_of_excellence')


def install():
    from gui.impl.lobby.tech_tree.tech_tree_view import TechTreeView

    from driftkings.gameface.core import attach_assets, INVALID_RES_ID
    from driftkings.gameface.core import resource_id as resolve_resource
    for name in ('_onLoading', '_finalize', '_TechTreeView__fillNodeOverrides', '_TechTreeView__updateNodeOverrides'):
        if not callable(getattr(TechTreeView, name, None)):
            raise RuntimeError('Unsupported TechTreeView API: ' + name)

    class MarksModel(ViewModel):
        def __init__(self):
            super(MarksModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(MarksModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, FEATURE)

    class MarksView(ViewImpl):
        def __init__(self, resource_id):
            self.vehicle_ids = ()
            self._records = {}
            self._lastPayload = None
            super(MarksView, self).__init__(ViewSettings(resource_id, model=MarksModel()))

        def refresh(self, vehicle_ids=None, reload=True):
            if vehicle_ids is not None:
                self.vehicle_ids = tuple(vehicle_ids)
            if reload or vehicle_ids is not None:
                self._records.clear()
            payload = _component().make_payload(self.vehicle_ids, self._records)
            if payload == self._lastPayload:
                return
            with self.getViewModel().transaction() as model:
                model._setString(0, payload)
            self._lastPayload = payload

    @override(TechTreeView, '_onLoading')
    def new__on_loading(original, view, *args, **kwargs):
        try:
            resource_id = resolve_resource(RESOURCE)
            if resource_id == INVALID_RES_ID:
                _component().LOG.warning('Missing resource map entry: %s', RESOURCE)
            else:
                child = MarksView(resource_id)
                _component()._views[view] = child
                view.setChildView(resource_id, child)
                _component().LOG.info('Attached Gameface tech tree badges (resource %s)', resource_id)
        except Exception:
            _component().LOG.exception('Could not attach tech tree badges')
        return original(view, *args, **kwargs)

    @override(TechTreeView, '_TechTreeView__fillNodeOverrides')
    def new__fill_nodes(original, view, model, nodes):
        result = original(view, model, nodes)
        child = _component()._views.get(view)
        if child is not None:
            try:
                child.refresh(nodes.keys())
            except Exception:
                _component().LOG.exception('Could not refresh tech tree badges')
        return result

    @override(TechTreeView, '_TechTreeView__updateNodeOverrides')
    def new__update_nodes(original, view, nodes):
        result = original(view, nodes)
        child = _component()._views.get(view)
        if child is not None:
            try:
                child.refresh()
            except Exception:
                _component().LOG.exception('Could not update tech tree badges')
        return result

    @override(TechTreeView, '_finalize')
    def new__finalize(original, view, *args, **kwargs):
        _component()._views.pop(view, None)
        return original(view, *args, **kwargs)
