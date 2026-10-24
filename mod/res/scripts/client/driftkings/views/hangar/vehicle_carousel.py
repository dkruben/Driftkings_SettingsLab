# -*- coding: utf-8 -*-
from driftkings._constants import GLOBAL, VEHICLE_CAROUSEL
from driftkings.core import carousel as layout
from driftkings.core.carousel_options import from_carousel
from driftkings.settings.service import affects, settings_service

"""Presentation adapter for CarouselStats; gameplay state stays in its component."""
from importlib import import_module
import weakref

from CurrentVehicle import g_currentVehicle
from gui.shared.personality import ServicesLocator

from driftkings.views.hangar.common import card_payload, HangarController, install_card, publish_card


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

    from driftkings.ui.gameface import attach_assets

    class CarouselModel(ViewModel):
        def __init__(self):
            super(CarouselModel, self).__init__(properties=3, commands=1)

        def _initialize(self):
            super(CarouselModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self.onRequestVehicles = self._addCommand('onRequestVehicles')
            attach_assets(self, _component().FEATURE)

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
            if not isinstance(ids, basestring) or len(ids) > 2048:
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

    install_card(_component, CarouselView, __name__)
