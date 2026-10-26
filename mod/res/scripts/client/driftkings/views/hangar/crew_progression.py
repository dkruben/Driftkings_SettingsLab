# -*- coding: utf-8 -*-
"""Owned data bridge for annotations beside native crew slots."""
import sys
import weakref

from CurrentVehicle import g_currentVehicle
from gui.shared.personality import ServicesLocator

from driftkings._constants import CREW_MANAGEMENT, GLOBAL
from driftkings.interface_catalog import gameface_spec
from driftkings.lobby.crew_progression import collect_rows
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.views.crew_progression_model import progression_kinds, progression_lines
from driftkings.gameface.hangar.common import HangarController, install_card, publish_card

FEATURE = 'DriftkingsCrewProgression'
RESOURCE = gameface_spec(FEATURE)['resource']
LOG = get_logger('Driftkings.CrewProgressionView')
_config = None
_installed = False


def build_model(visible):
    settings = settings_service.getComponentDict(_config)
    enabled = bool(visible and settings[GLOBAL.ENABLED] and settings.get('showCrewProgression', True) and settings.get('showCrewTooltips', True))
    result = {'config': {'visible': enabled}, 'rows': []}
    if not enabled or not g_currentVehicle.isPresent():
        return result
    vehicle = g_currentVehicle.item
    result['vehicleId'] = vehicle.intCD
    for row in collect_rows(vehicle, ServicesLocator.itemsCache.items):
        lines = progression_lines(row, settings, _config.lang, _config.i18n)
        if lines:
            kinds = progression_kinds(row, settings)
            result['rows'].append({'slot': row['slot'], 'id': row['id'], 'lines': lines, 'kinds': kinds})
    return result


class CrewController(HangarController):
    def __init__(self):
        super(CrewController, self).__init__()
        self.active = False

    def start(self):
        if self.active:
            return
        self.active = True
        settings_service.onModSettingsChanged.connect(self.onSettingsChanged, CREW_MANAGEMENT)
        self.onApplySettings()

    def stop(self):
        if not self.active:
            return
        self.active = False
        settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)
        for child in list(self.views.values()):
            child.refresh()
        self.visible.clear()

    def onSettingsChanged(self, component, changes):
        self.onApplySettings(changes)


g_controller = CrewController()


def install(config):
    global _config, _installed
    _config = config
    if _installed:
        return
    _installed = True
    from frameworks.wulf import ViewModel
    from gui.impl.pub.view_component import ViewComponent

    from driftkings.gameface.core import attach_assets

    class CrewModel(ViewModel):
        def __init__(self):
            super(CrewModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(CrewModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, FEATURE)

    class CrewView(ViewComponent):
        def __init__(self, parent, resource_id):
            self._parentRef = weakref.ref(parent)
            self._crewActive = False
            self._lastPayload = None
            super(CrewView, self).__init__(layoutID=resource_id, model=CrewModel)
            g_controller.views[parent] = self

        def _getEvents(self):
            return ((g_currentVehicle.onChanged, self.refresh),
                    (ServicesLocator.itemsCache.onSyncCompleted, self.refresh))

        def _onLoading(self, *args, **kwargs):
            super(CrewView, self)._onLoading(*args, **kwargs)
            self._crewActive = True
            self.refresh()

        def _finalize(self):
            self._crewActive = False
            parent = self._parentRef()
            if parent is not None and g_controller.views.get(parent) is self:
                g_controller.views.pop(parent, None)
                g_controller.visible.pop(parent, None)
            super(CrewView, self)._finalize()

        def refresh(self, *args, **kwargs):
            if not self._crewActive:
                return
            parent = self._parentRef()
            visible = bool(g_controller.active and parent is not None and
                           g_controller.visible.get(parent, False))
            try:
                publish_card(self, build_model(visible))
            except Exception:
                LOG.exception('Could not publish crew progression')
                publish_card(self, {'config': {'visible': False}, 'rows': []})

    install_card(lambda: sys.modules[__name__], CrewView, __name__)
    from driftkings.views.hangar import crew_details
    crew_details.install()
