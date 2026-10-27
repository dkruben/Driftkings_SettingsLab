# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, VEHICLE_CAROUSEL
from driftkings.core import carousel as layout
from driftkings.core.carousel_options import from_carousel
from driftkings.core.hooks import override
from driftkings.interface_catalog import gameface_spec
from driftkings.settings.service import affects, settings_service

"""Presentation adapter for CarouselStats; gameplay state stays in its component."""
from importlib import import_module
import weakref

from CurrentVehicle import g_currentVehicle
from gui.shared.personality import ServicesLocator

from driftkings.common.utils.compat import string_types
from driftkings.gameface.lobby.common import card_payload, HangarController, install_card, publish_card

FEATURE = 'DriftkingsCarouselStats'
RESOURCE = gameface_spec(FEATURE)['resource']


def _component():
    # Resolve live state after component initialization; avoid circular imports.
    return import_module('driftkings.lobby.vehicle_carousel')


def get_view_config(config, row_models):
    carousel = settings_service.getComponentDict(config)[VEHICLE_CAROUSEL.CAROUSEL]
    result = from_carousel(carousel)
    native = next(iter(row_models.values()), 1)
    result.update(cellType=carousel['cellType'], effectiveRows=layout.row_count(carousel, native))
    for mode in ('normal', 'small'):
        result[mode] = dict((key, carousel[mode][key]) for key in ('width', 'height', 'gap'))
    items = ServicesLocator.itemsCache.items
    total = items.stats.vehicleSlots
    free = items.inventory.getFreeSlots(total)
    result.update(totalSlots=total, freeSlots=free, usedSlots=max(0, total-free))
    return result


class CarouselController(HangarController):
    def start(self):
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, VEHICLE_CAROUSEL)
        # Dossier synchronization can finish while the hangar view is destroyed.
        ServicesLocator.itemsCache.onSyncCompleted += self.onItemsSyncCompleted

    def stop(self):
        ServicesLocator.itemsCache.onSyncCompleted -= self.onItemsSyncCompleted
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)

    def onItemsSyncCompleted(self, *args):
        _component().g_data.invalidate()
        for child in list(self.views.values()):
            child.refresh()

    def onSettingsChanged(self, component, changes):
        self.onApplySettings(changes)

    def onApplySettings(self, changes=None):
        all_settings = changes is None
        self.updatingSettings = True
        try:
            if all_settings or affects(changes, GLOBAL.ENABLED, (VEHICLE_CAROUSEL.CAROUSEL, 'rows'),
                                        (VEHICLE_CAROUSEL.CAROUSEL, 'cellType')):
                for model, native in list(_component().g_rowModels.items()):
                    model.setCarouselRowCount(native)
            if all_settings or affects(changes, GLOBAL.ENABLED, (VEHICLE_CAROUSEL.CAROUSEL, 'nations_order')):
                for presenter in list(_component().g_filterPresenters):
                    presenter._VehicleFiltersDataProvider__updateModel()
        finally:
            self.updatingSettings = False
        super(CarouselController, self).onApplySettings(changes)


def install_gameface():
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent

    from driftkings.gameface.core import attach_assets

    class CarouselModel(ViewModel):
        def __init__(self):
            super(CarouselModel, self).__init__(properties=3, commands=1)

        def _initialize(self):
            super(CarouselModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self.onRequestVehicles = self._addCommand('onRequestVehicles')
            attach_assets(self, FEATURE)

    class CarouselView(ViewComponent):
        def __init__(self, parent, resource_id):
            self._hangarRef = weakref.ref(parent)
            self._carouselActive = False
            self._vehicleIds = ()
            self._lastPayload = None
            super(CarouselView, self).__init__(layoutID=resource_id, model=CarouselModel)
            _component().g_controller.views[parent] = self

        def _getEvents(self):
            return ((g_currentVehicle.onChanged, self.refresh),
                    (ServicesLocator.itemsCache.onSyncCompleted, self.invalidate),
                    (self.getViewModel().onRequestVehicles, self.requestVehicles))

        def _onLoading(self, *args, **kwargs):
            super(CarouselView, self)._onLoading(*args, **kwargs)
            self._carouselActive = True
            # Never reuse a pre-battle dossier when a new hangar card is loaded.
            self.invalidate()

        def _finalize(self):
            self._carouselActive = False
            parent = self._hangarRef()
            if parent is not None and _component().g_controller.views.get(parent) is self:
                _component().g_controller.views.pop(parent, None)
            super(CarouselView, self)._finalize()

        def invalidate(self, *args):
            _component().g_data.invalidate()
            self.refresh()

        def requestVehicles(self, args):
            if not isinstance(args, dict):
                return
            ids = args.get('ids', '')
            if not isinstance(ids, string_types) or len(ids) > 2048:
                return
            requested = tuple(sorted(set(int(x) for x in ids.split(',')[:120] if x.isdigit())))
            if requested == self._vehicleIds and self._lastPayload is not None:
                return
            self._vehicleIds = requested
            self.refresh()

        def refreshSettings(self, changes):
            rebuild = affects(changes, GLOBAL.ENABLED, VEHICLE_CAROUSEL.COLOR_RATING, VEHICLE_CAROUSEL.SHOW_ICONS,
                              (VEHICLE_CAROUSEL.CAROUSEL, 'normal'), (VEHICLE_CAROUSEL.CAROUSEL, 'small'),
                              (VEHICLE_CAROUSEL.CAROUSEL, 'sorting_criteria'))
            self.refresh(config_only=not rebuild)

        def refresh(self, *args, **kwargs):
            if not self._carouselActive:
                return
            try:
                parent = self._hangarRef()
                visible = bool(parent is not None and _component().g_controller.visible.get(parent, False)
                               and settings_service.getComponentDict(_component().config)[GLOBAL.ENABLED])
                payload = card_payload(self._lastPayload, kwargs.get('config_only', False), visible,
                                       lambda: get_view_config(_component().config, _component().g_rowModels),
                                       lambda: _component().g_data.build_panel_model(self._vehicleIds))
                publish_card(self, payload)
            except Exception:
                self._lastPayload = None
                _component().LOG.exception('Could not update Gameface hangar card')
                with self.getViewModel().transaction() as model:
                    model._setString(0, '{"config":{"visible":false}}')

    install_card(_component, CarouselView, __name__, RESOURCE)


def install_carousel_layout():
    component = _component()
    config = component.config
    LOG = component.LOG
    g_rowModels = component.g_rowModels
    g_filterPresenters = component.g_filterPresenters
    g_controller = component.g_controller
    from gui.impl.gen.view_models.views.lobby.hangar.sub_views.vehicle_filter_model import VehicleFilterModel
    @override(VehicleFilterModel, 'setCarouselRowCount')
    def set_rows(original, model, value):
        try:
            g_rowModels[model] = value
        except TypeError:
            LOG.debug('Carousel model is not weak-referenceable; row count not tracked')
        rows = layout.row_count(settings_service.getComponentDict(config)[VEHICLE_CAROUSEL.CAROUSEL], value) if settings_service.getComponentDict(config)[GLOBAL.ENABLED] else value
        # The client model/toggle remains single or double; our Gameface bridge
        # expands effectiveRows to three/four without saving invalid client prefs.
        result = original(model, min(2, rows))
        if not getattr(g_controller, 'updatingSettings', False):
            for child in list(g_controller.views.values()):
                child.refresh()
        return result

    from gui.impl.lobby.hangar.presenters.vehicle_filters_presenter import VehicleFiltersDataProvider
    @override(VehicleFiltersDataProvider, '_VehicleFiltersDataProvider__updateModel')
    def update_filters(original, presenter):
        result = original(presenter)
        g_filterPresenters.add(presenter)
        order = settings_service.getComponentDict(config)[VEHICLE_CAROUSEL.CAROUSEL]['nations_order'] if settings_service.getComponentDict(config)[GLOBAL.ENABLED] else []
        if order:
            with presenter.viewModel.transaction() as model:
                target = model.getNationsOrder()
                existing = list(target)
                ordered = [value for value in order if value in existing] + [value for value in existing if value not in order]
                target.clear()
                for value in ordered:
                    target.addString(value)
        return result

    @override(VehicleFiltersDataProvider, '_finalize')
    def finalize_filters(original, presenter, *args, **kwargs):
        g_filterPresenters.discard(presenter)
        return original(presenter, *args, **kwargs)

    from gui.impl.gen import R
    from gui.impl.lobby.hangar.presenters.vehicle_inventory_presenter import VehicleInventoryPresenter
    @override(VehicleInventoryPresenter, 'createToolTipContent')
    def tooltip(original, presenter, event, contentID):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[VEHICLE_CAROUSEL.CAROUSEL]['suppressCarouselTooltips'] and contentID == R.views.mono.hangar.vehicle_tooltip():
            return None
        return original(presenter, event, contentID)



def restore_carousel_layout():
    component = _component()
    g_rowModels = component.g_rowModels
    g_filterPresenters = component.g_filterPresenters
    for model, native in list(g_rowModels.items()):
        model.setCarouselRowCount(native)
    g_rowModels.clear()
    for presenter in list(g_filterPresenters):
        presenter._VehicleFiltersDataProvider__updateModel()
    g_filterPresenters.clear()
