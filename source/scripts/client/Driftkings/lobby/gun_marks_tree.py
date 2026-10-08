# -*- coding: utf-8 -*-
from Driftkings._constants import GLOBAL, MARKS_ON_GUN_TECH_TREE
from Driftkings.settings.service import settings_service, affects
"""EU 2.4 Gameface implementation; the legacy NationTreeNode SWF is not used."""
import json
import logging
import weakref

from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from gui.shared.personality import ServicesLocator

from Driftkings.common import getStatisticColor
from Driftkings.settings.templates.lobby.gun_marks_tree import MarksOnGunTechTreeSettings as ConfigInterface
from Driftkings.views.hangar.gun_marks_tree import install

LOG = logging.getLogger('Driftkings.MarksOnGunTechTree')
FEATURE = 'DriftkingsMarksOnGunTechTree'
RESOURCE = 'mods/Driftkings/MarksOnGunTechTree/model'
ASSETS = 'coui://gui/gameface/mods/Driftkings/MarksOnGunTechTree/'
_views = weakref.WeakKeyDictionary()


class TechTreeController(object):
    def __init__(self):
        self.active = False

    def start(self):
        if not self.active:
            self.active = True
            settings_service.onModSettingsChanged.connect(self.onSettingsChanged, MARKS_ON_GUN_TECH_TREE)

    def stop(self):
        if self.active:
            self.active = False
            settings_service.onModSettingsChanged.disconnect(self.onSettingsChanged)

    def onSettingsChanged(self, component, changes):
        if not affects(changes, GLOBAL.ENABLED, MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE,
                       MARKS_ON_GUN_TECH_TREE.COLOR_RATING,
                       MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT,
                       MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MASTERY,
                       MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED,
                       MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_X, MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_Y,
                       MARKS_ON_GUN_TECH_TREE.BADGE_FONT_SIZE):
            return
        for child in list(_views.values()):
            try:
                child.refresh(reload=False)
            except Exception:
                LOG.exception('Could not apply tech tree settings to the active view')



config = ConfigInterface()
controller = TechTreeController()


def vehicle_marks(vehicle_id):
    """Only the account's own dossier; no network requests or other-player data."""
    dossier = ServicesLocator.itemsCache.items.getVehicleDossier(int(vehicle_id))
    vehicle = ServicesLocator.itemsCache.items.getItemByCD(int(vehicle_id))
    tier = int(vehicle.level)
    raw = dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') if tier >= 5 else 0
    percent = max(0.0, min(100.0, float(raw or 0) / 100.0))
    mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
    mastery_value = int(mastery.getValue() or 0) if mastery else 0
    return {'percent': percent, 'tier': tier, 'mastery': max(0, min(4, mastery_value))}


def make_payload(vehicle_ids, records=None):
    # Raw dossier values belong to the open view; colors follow current settings.
    records = {} if records is None else records
    data = settings_service.getComponentDict(config)
    enabled = bool(data.get(GLOBAL.ENABLED) and data.get(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE))
    vehicles = {}
    if enabled:
        for vehicle_id in vehicle_ids:
            try:
                if vehicle_id not in records:
                    records[vehicle_id] = vehicle_marks(vehicle_id)
                values = dict(records[vehicle_id])
                values['color'] = getStatisticColor('mog', values['percent'], data.get(MARKS_ON_GUN_TECH_TREE.COLOR_RATING, 0))
                vehicles[str(vehicle_id)] = values
            except Exception:
                # One unavailable dossier must not prevent the tree from opening.
                LOG.debug('Dossier unavailable for %s', vehicle_id, exc_info=True)
    return json.dumps({
        'enabled': enabled, 'vehicles': vehicles,
        'showPercent': bool(data.get(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_PERCENT)),
        'showMastery': bool(data.get(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MASTERY)),
        'colorName': bool(data.get(MARKS_ON_GUN_TECH_TREE.SHOW_IN_TECH_TREE_MARK_OF_GUN_TANK_NAME_COLORED)),
        'offsetX': data.get(MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_X, 115),
        'offsetY': data.get(MARKS_ON_GUN_TECH_TREE.BADGE_OFFSET_Y, 0),
        'fontSize': data.get(MARKS_ON_GUN_TECH_TREE.BADGE_FONT_SIZE, 14)}, separators=(',', ':'), sort_keys=True)


def init():
    try:
        install()
        controller.start()
    except Exception:
        LOG.exception('Gameface tech tree integration unavailable; keeping the standard tree')


def fini():
    controller.stop()
