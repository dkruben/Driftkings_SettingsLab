# -*- coding: utf-8 -*-
"""EU 2.4 Gameface implementation; the legacy NationTreeNode SWF is not used."""
import json
import weakref

from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from gui.shared.personality import ServicesLocator

from driftkings._constants import GLOBAL, TECH_TREE_MARKS_OF_EXCELLENCE
from driftkings.common.utils.colorratting import getStatisticColor
from driftkings.core.settings_controller import SettingsController
from driftkings.interface_catalog import gameface_spec
from driftkings.logger import get_logger
from driftkings.settings.definitions.lobby.tech_tree_marks_of_excellence import \
    TechTreeMarksOfExcellenceSettings as Settings
from driftkings.settings.service import affects, settings_service
from driftkings.views.hangar.tech_tree_marks_of_excellence import install

LOG = get_logger('Driftkings.MarksOnGunTechTree')
FEATURE = 'DriftkingsMarksOnGunTechTree'
RESOURCE = gameface_spec(FEATURE)['resource']
_views = weakref.WeakKeyDictionary()


class TechTreeController(SettingsController):
    SETTINGS_SECTION = TECH_TREE_MARKS_OF_EXCELLENCE


    def onSettingsChanged(self, component, changes):
        if not affects(changes, GLOBAL.ENABLED, TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE,
                       TECH_TREE_MARKS_OF_EXCELLENCE.COLOR_RATING,
                       TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT,
                       TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MASTERY,
                       TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED,
                       TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_OFFSET_X, TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_OFFSET_Y,
                       TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_FONT_SIZE):
            return
        for child in list(_views.values()):
            try:
                child.refresh(reload=False)
            except Exception:
                LOG.exception('Could not apply tech tree settings to the active view')


config = Settings()
controller = TechTreeController()


def vehicle_marks(vehicle_id):
    """Only the account's own dossier; no network requests or other-player data."""
    dossier = ServicesLocator.itemsCache.items.getVehicleDossier(int(vehicle_id))
    vehicle = ServicesLocator.itemsCache.items.getItemByCD(int(vehicle_id))
    tier = int(vehicle.level)
    raw = dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') if tier >= 5 else 0
    percent = max(0.0, min(100.0, float(raw or 0) / 100.0))
    mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
    rank = mastery.getValue() if mastery is not None and mastery.isInDossier() else 0
    mastery_value = int(rank) if rank in (1, 2, 3, 4) else 0
    return {'percent': percent, 'tier': tier, 'mastery': mastery_value}


def make_payload(vehicle_ids, records=None):
    # Raw dossier values belong to the open view; colors follow current settings.
    records = {} if records is None else records
    data = settings_service.getComponentDict(config)
    enabled = bool(data.get(GLOBAL.ENABLED) and data.get(TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE))
    vehicles = {}
    if enabled:
        for vehicle_id in vehicle_ids:
            try:
                if vehicle_id not in records:
                    records[vehicle_id] = vehicle_marks(vehicle_id)
                values = dict(records[vehicle_id])
                values['color'] = getStatisticColor('mog', values['percent'], data.get(TECH_TREE_MARKS_OF_EXCELLENCE.COLOR_RATING, 0))
                vehicles[str(vehicle_id)] = values
            except Exception:
                # One unavailable dossier must not prevent the tree from opening.
                LOG.debug('Dossier unavailable for %s', vehicle_id, exc_info=True)
    return json.dumps({
        GLOBAL.ENABLED: enabled, 'vehicles': vehicles,
        'showPercent': bool(data.get(TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT)),
        'showMastery': bool(data.get(TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MASTERY)),
        'colorName': bool(data.get(TECH_TREE_MARKS_OF_EXCELLENCE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED)),
        'offsetX': data.get(TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_OFFSET_X, 115),
        'offsetY': data.get(TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_OFFSET_Y, 0),
        'fontSize': data.get(TECH_TREE_MARKS_OF_EXCELLENCE.BADGE_FONT_SIZE, 14)}, separators=(',', ':'), sort_keys=True)


def init():
    try:
        install()
        controller.start()
    except Exception:
        LOG.exception('Gameface tech tree integration unavailable; keeping the standard tree')


def fini():
    controller.stop()
