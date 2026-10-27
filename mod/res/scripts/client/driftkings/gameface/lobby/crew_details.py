# -*- coding: utf-8 -*-
"""Progression summaries owned by native crew personal views and tooltips."""
import weakref

from gui.shared.personality import ServicesLocator

from driftkings._constants import GLOBAL
from driftkings.core.crew_progression import nonnegative
from driftkings.core.hooks import override
from driftkings.gameface.lobby import crew_progression as hangar_bridge
from driftkings.gameface.lobby.common import publish_card
from driftkings.interface_catalog import gameface_spec
from driftkings.lobby.crew_progression import collect_tankman
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service
from driftkings.views.crew_progression_model import integer, progression_kinds, progression_lines, translated

FEATURE = 'DriftkingsCrewDetails'
RESOURCE = gameface_spec(FEATURE)['resource']
LOG = get_logger('Driftkings.CrewDetails')
_installed = False


def build_model(parent, surface):
    config = hangar_bridge._config
    settings = settings_service.getComponentDict(config)
    option = {'tooltip': 'showCrewTooltips', 'barracks': 'showBarracksProgression'}.get(surface, 'showCrewDetails')
    enabled = bool(hangar_bridge.g_controller.active and settings[GLOBAL.ENABLED] and settings.get(option, True))
    result = {'config': {'visible': False}, 'surface': surface, 'lines': []}
    if not enabled:
        return result
    if surface == 'barracks':
        return build_barracks_model(parent, settings, config)
    if surface == 'tooltip':
        tankman_id = parent.tankmanID
    else:
        tankman = parent.context.tankman
        tankman_id = tankman.invID if tankman is not None else None
    if tankman_id is None:
        return result
    items = ServicesLocator.itemsCache.items
    tankman = items.getTankman(tankman_id)
    if tankman is None:
        return result
    row = collect_tankman(tankman, items)
    # Use the native descriptor; no old reset/retraining XP thresholds.
    total = nonnegative(tankman.descriptor.totalXP())
    lines = []
    kinds = []
    if total is not None:
        lines.append(translated(config.i18n, 'UI_crew_totalXP').format(xp=integer(total, config.lang)))
        kinds.append('total')
    lines.extend(progression_lines(row, settings, config.lang, config.i18n))
    kinds.extend(progression_kinds(row, settings))
    result.update(config={'visible': bool(lines)}, id=tankman_id, lines=lines, kinds=kinds,
                  title=translated(config.i18n, 'UI_crew_progressionTitle'))
    return result


def build_barracks_model(parent, settings, config):
    """Only the native filtered/paginated cards; recruits have no training data."""
    items = ServicesLocator.itemsCache.items
    rows = []
    for card in parent.viewModel.getTankmanList():
        if card.getTankmanKind().value != 'tankman':
            continue
        tankman_id = card.getTankmanID()
        tankman = items.getTankman(tankman_id)
        if tankman is None:
            continue
        row = collect_tankman(tankman, items)
        lines = progression_lines(row, settings, config.lang, config.i18n)
        if lines:
            rows.append({'id': tankman_id, 'lines': lines, 'kinds': progression_kinds(row, settings)})
    return {'config': {'visible': True}, 'surface': 'barracks', 'rows': rows}


def install():
    global _installed
    if _installed:
        return
    from frameworks.wulf import ViewModel
    from gui.impl.lobby.crew.barracks_view import BarracksView
    from gui.impl.lobby.crew.container_vews.personal_file.personal_file_view import PersonalFileView
    from gui.impl.lobby.crew.container_vews.service_record.service_record_view import ServiceRecordView
    from gui.impl.lobby.crew.tooltips.tankman_tooltip import TankmanTooltip
    from gui.impl.pub.view_component import ViewComponent

    from driftkings.gameface.core import attach_assets, INVALID_RES_ID, resource_id

    class DetailsModel(ViewModel):
        def __init__(self):
            super(DetailsModel, self).__init__(properties=3, commands=0)

        def _initialize(self):
            super(DetailsModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            attach_assets(self, FEATURE)

    class DetailsView(ViewComponent):
        def __init__(self, parent, layout_id, surface):
            self._parentRef = weakref.ref(parent)
            self._surface = surface
            self._detailsActive = False
            self._lastPayload = None
            super(DetailsView, self).__init__(layoutID=layout_id, model=DetailsModel)
            hangar_bridge.g_controller.views[parent] = self

        def _getEvents(self):
            return ((ServicesLocator.itemsCache.onSyncCompleted, self.refresh),)

        def _onLoading(self, *args, **kwargs):
            super(DetailsView, self)._onLoading(*args, **kwargs)
            self._detailsActive = True
            self.refresh()

        def _finalize(self):
            self._detailsActive = False
            parent = self._parentRef()
            if parent is not None and hangar_bridge.g_controller.views.get(parent) is self:
                hangar_bridge.g_controller.views.pop(parent, None)
            super(DetailsView, self)._finalize()

        def refresh(self, *args, **kwargs):
            parent = self._parentRef()
            if not self._detailsActive or parent is None:
                return
            try:
                publish_card(self, build_model(parent, self._surface))
            except Exception:
                LOG.exception('Could not update crew details for %s', self._surface)
                publish_card(self, {'config': {'visible': False}, 'surface': self._surface, 'lines': []})

    def handlers(surface):
        def loading(original, view, *args, **kwargs):
            result = original(view, *args, **kwargs)
            child = None
            try:
                layout_id = resource_id(RESOURCE)
                if layout_id == INVALID_RES_ID:
                    LOG.warning('Missing crew details Gameface resource: %s', RESOURCE)
                elif view.getChildView(layout_id) is None:
                    child = DetailsView(view, layout_id, surface)
                    view.setChildView(layout_id, child)
            except Exception:
                LOG.exception('Could not attach crew details for %s', surface)
                if child is not None:
                    child.destroy()
            return result

        def filled(original, view, *args, **kwargs):
            result = original(view, *args, **kwargs)
            child = hangar_bridge.g_controller.views.get(view)
            if child is not None:
                child.refresh()
            return result
        return loading, filled

    for target, surface, fill in ((TankmanTooltip, 'tooltip', '_fillModel'),
                                  (PersonalFileView, 'personal_file', '_fillViewModel'),
                                  (ServiceRecordView, 'service_record', '_fillViewModel'),
                                  (BarracksView, 'barracks', '_fillVisibleCards')):
        loading, filled = handlers(surface)
        override(target, '_onLoading')(loading)
        override(target, fill)(filled)
    _installed = True
