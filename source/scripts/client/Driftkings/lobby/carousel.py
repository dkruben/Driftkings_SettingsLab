# -*- coding: utf-8 -*-
"""Configurable own-vehicle statistics on EU Gameface carousel cards."""
import logging
import math
import weakref

import BigWorld
from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from gui.shared.personality import ServicesLocator
from gui.shared.utils.requesters import REQ_CRITERIA

from Driftkings.common import getStatisticColor
from Driftkings.core.hooks import override
from Driftkings.core import carousel as layout
from Driftkings.core.carousel_assets import CarouselImages
from Driftkings.core.carousel_tiers import battle_tiers
from Driftkings.core.carousel_options import STAT_SORT_KEYS
from Driftkings.stats import getVehicleInfoData, calculateXvmScale
from Driftkings._constants import CAROUSEL_STATS, GLOBAL
from Driftkings.settings.service import settings_service

LOG = logging.getLogger('Driftkings.CarouselStats')
FEATURE = 'DriftkingsCarouselStats'
RESOURCE = 'mods/Driftkings/CarouselStats/model'
ASSETS = 'coui://gui/gameface/mods/Driftkings/CarouselStats/'
g_controller = None
ICONS = {
    'damage': 'library/efficiency/48x48/damage.png',
    'assist': 'library/efficiency/48x48/help.png',
    'blocked': 'library/efficiency/48x48/armor.png',
    'wins': 'library/dossier/wins40x32.png',
    'battles': 'library/dossier/battles40x32.png'
}
COLOR_KEYS = {
    'wn8': 'wn8', 'eff': 'eff', 'xwn8': 'x', 'xeff': 'x',
    'winRate': 'winrate', 'avgDamage': 'tdb', 'marks': 'mog',
    'damageRatio': 'damageRatio', 'damageHP': 'damageHP',
    'hitRate': 'hitsRatio', 'avgFrags': 'tfb', 'avgSpotted': 'tsb',
    'battles': 't_battles'
}
CLASS_COLORS = {
    'lightTank': '#53B329', 'mediumTank': '#1EA2D2',
    'heavyTank': '#957D5B', 'AT-SPG': '#F13439', 'SPG': '#B87AB2'
}


def number(value, default=None):
    try:
        result = float(value)
        return default if math.isnan(result) or math.isinf(result) else result
    except (TypeError, ValueError, OverflowError):
        return default


def bounded(value, low, high, default):
    return max(low, min(high, number(value, default)))


def ratio(numerator, denominator):
    numerator, denominator = number(numerator), number(denominator)
    return numerator / denominator if numerator is not None and denominator and denominator > 0 else None


def ratings(values, expected, tier):
    result = {'eff': None, 'wn8': None, 'xeff': None, 'xwn8': None}
    if not values.get('battles'):
        return result
    damage, frags, spots, defence, capture = [values.get(k) for k in ('avgDamage', 'avgFrags', 'avgSpotted', 'avgDefence', 'avgCapture')]
    if all(v is not None for v in (damage, frags, spots, defence, capture)) and tier > 0:
        # Classic Efficiency Rating, using this vehicle's tier and random-battle averages.
        result['eff'] = (damage * 10.0 / (tier + 2) * (0.23 + 0.02 * tier)
                         + frags * 250 + spots * 150 + math.log(1 + max(0, capture), 1.732) * 150 + defence * 150)
    keys = ('wn8expDamage', 'wn8expFrag', 'wn8expSpot', 'wn8expDef', 'wn8expWinRate')
    exp = [number((expected or {}).get(k)) for k in keys]
    raw = (damage, frags, spots, defence, values.get('winRate'))
    if all(x is not None and x > 0 for x in exp) and all(x is not None for x in raw):
        rd, rf, rs, rb, rw = [x / y for x, y in zip(raw, exp)]
        d = max(0, (rd - .22) / .78)
        f = max(0, min(d + .2, (rf - .12) / .88))
        s = max(0, min(d + .1, (rs - .38) / .62))
        b = max(0, min(d + .1, (rb - .10) / .90))
        w = max(0, (rw - .71) / .29)
        result['wn8'] = 980*d + 210*d*f + 155*f*s + 75*b*f + 145*min(1.8,w)
    for key in ('eff', 'wn8'):
        if result[key] is not None:
            scaled = number(calculateXvmScale(key, result[key]))
            result['x'+key] = scaled if scaled is not None and scaled >= 0 else None
    return result


def collect(vehicle):
    expected = getVehicleInfoData(vehicle.intCD) or {}
    low, high = battle_tiers(vehicle.level, vehicle.type, expected.get('key', getattr(vehicle, 'name', '')))
    values = {'battles': 0, 'vehicle': vehicle.shortUserName, 'level': vehicle.level, 'premium': vehicle.isPremium,
              'nation': vehicle.nationName, 'type': vehicle.type,
              'classColor': CLASS_COLORS.get(vehicle.type, '#957D5B'),
              'wn8expd': number(expected.get('wn8expDamage')), 'battletiermin': low, 'battletiermax': high}
    dossier = ServicesLocator.itemsCache.items.getVehicleDossier(vehicle.intCD)
    if dossier is None:
        return values
    stats = dossier.getRandomStats()
    battles = number(stats.getBattlesCount(), 0)
    values['battles'] = battles
    methods = {'avgDamage': 'getAvgDamage', 'avgReceived': 'getAvgDamageReceived',
               'avgAssist': 'getDamageAssistedEfficiency', 'avgBlocked': 'getAvgDamageBlocked',
               'avgStun': 'getAvgDamageAssistedStun', 'avgFrags': 'getAvgFrags',
               'avgSpotted': 'getAvgEnemiesSpotted'}
    for key, method in methods.items():
        values[key] = number(getattr(stats, method)()) if battles else None
    values['winRate'] = number(stats.getWinsEfficiency()) if battles else None
    if values['winRate'] is not None:
        values['winRate'] *= 100
    values['hitRate'] = ratio(stats.getHitsCount(), stats.getShotsCount()) if battles else None
    if values['hitRate'] is not None:
        values['hitRate'] *= 100
    values['avgCapture'] = ratio(stats.getCapturePoints(), battles)
    values['avgDefence'] = ratio(stats.getDroppedCapturePoints(), battles)
    values['damageRatio'] = ratio(values['avgDamage'], values['avgReceived'])
    values['damageHP'] = ratio(values['avgDamage'], vehicle.descriptor.maxHealth)
    values['marks'] = (number(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating'), 0) / 100
                       if vehicle.level >= 5 and battles else None)
    values['marksOnGun'] = number(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'marksOnGun'), 0)
    mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
    values['mastery'] = int(bounded(mastery.getValue() if mastery else 0, 0, 4, 0))
    values['wn8effd'] = ratio(values['avgDamage'], values['wn8expd'])
    values.update(ratings(values, expected, vehicle.level))
    return values


def render_macro(template, values):
    def color(key, value):
        return getStatisticColor(COLOR_KEYS.get(key, key), value, settings_service.getComponentDict(config).get(CAROUSEL_STATS.COLOR_RATING, 1))
    def icon(key):
        if key == 'marksOnGun':
            rank = int(bounded(values.get('marksOnGun'), 0, 3, 0))
            nation = values.get('nation', 'ussr')
            suffix = 'mark' if rank == 1 else 'marks'
            return 'coui://gui/maps/icons/marksOnGun/95x85/%s_%d_%s.png' % (nation, rank, suffix) if rank else ''
        if key == 'mastery':
            rank = int(bounded(values.get('mastery'), 0, 4, 0))
            return 'coui://gui/maps/icons/library/proficiency/class_icons_%d.png' % rank if rank else ''
        return 'coui://gui/maps/icons/' + ICONS[key] if key in ICONS else ''
    return layout.render(template, values, color, icon)


from Driftkings.settings.templates.lobby.carousel import CarouselStatsSettings as Settings


config = Settings()


class CarouselData(object):
    def __init__(self):
        self.cache = {}
        self.account = None
        self.images = CarouselImages()

    def invalidate(self):
        self.cache.clear()

    def build_panel_model(self, requested):
        account = getattr(BigWorld.player(), 'databaseID', None)
        if account != self.account:
            self.account = account
            self.invalidate()
        result = {'config': get_view_config(config, g_rowModels), 'vehicles': {}}
        inventory = ServicesLocator.itemsCache.items.getVehicles(REQ_CRITERIA.INVENTORY)
        criteria = set(key.lstrip('-') for key in settings_service.getComponentDict(config)[CAROUSEL_STATS.CAROUSEL]['sorting_criteria'])
        result['sortValues'] = {}
        if criteria.intersection(STAT_SORT_KEYS):
            for cd, vehicle in inventory.items():
                try:
                    if cd not in self.cache:
                        self.cache[cd] = collect(vehicle)
                    values = self.cache[cd]
                    result['sortValues'][str(cd)] = dict((key, values.get({'markOfMastery': 'mastery', 'damageRating': 'marks'}.get(key, key))) for key in criteria.intersection(STAT_SORT_KEYS))
                except Exception:
                    LOG.debug('Sorting dossier unavailable for %s', cd, exc_info=True)
        if 'battlePassPoints' in criteria:
            from helpers import dependency
            from skeletons.gui.game_control import IBattlePassController
            battlePass = dependency.instance(IBattlePassController)
            for cd in inventory:
                result['sortValues'].setdefault(str(cd), {})['battlePassPoints'] = battlePass.getVehicleProgression(cd)[0] if battlePass.isVisible() else None
        for cd in requested:
            vehicle = inventory.get(cd)
            if vehicle is None:
                continue
            try:
                if cd not in self.cache:
                    self.cache[cd] = collect(vehicle)
                values = dict(self.cache[cd], selected=bool(g_currentVehicle.isPresent() and g_currentVehicle.intCD == cd))
                result['vehicles'][str(cd)] = dict((mode, layout.build_profile(settings_service.getComponentDict(config)[CAROUSEL_STATS.CAROUSEL][mode],
                    lambda template: render_macro(template, values), settings_service.getComponentDict(config)[CAROUSEL_STATS.SHOW_ICONS])) for mode in ('normal','small'))
            except Exception:
                LOG.debug('Dossier unavailable for %s',cd,exc_info=True)
        result['images'] = self.images.collect(result['vehicles'])
        return result


g_data = CarouselData()

from Driftkings.views.hangar.carousel import CarouselController, get_view_config, install_gameface


g_rowModels = weakref.WeakKeyDictionary()
g_filterPresenters = weakref.WeakSet()


def install_carousel_layout():
    from gui.impl.gen.view_models.views.lobby.hangar.sub_views.vehicle_filter_model import VehicleFilterModel
    @override(VehicleFilterModel, 'setCarouselRowCount')
    def set_rows(original, model, value):
        try:
            g_rowModels[model] = value
        except TypeError:
            pass
        rows = layout.row_count(settings_service.getComponentDict(config)[CAROUSEL_STATS.CAROUSEL], value) if settings_service.getComponentDict(config)[GLOBAL.ENABLED] else value
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
        order = settings_service.getComponentDict(config)[CAROUSEL_STATS.CAROUSEL]['nations_order'] if settings_service.getComponentDict(config)[GLOBAL.ENABLED] else []
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

    from gui.impl.lobby.hangar.presenters.vehicle_inventory_presenter import VehicleInventoryPresenter
    from gui.impl.gen import R
    @override(VehicleInventoryPresenter, 'createToolTipContent')
    def tooltip(original, presenter, event, contentID):
        if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[CAROUSEL_STATS.CAROUSEL]['suppressCarouselTooltips'] and contentID == R.views.mono.hangar.vehicle_tooltip():
            return None
        return original(presenter, event, contentID)


g_controller = CarouselController()
def init():
    try:
        install_carousel_layout()
        install_gameface()
        g_controller.start()
    except Exception:
        LOG.exception('Gameface carousel statistics integration unavailable')


def fini():
    g_controller.stop()
    for model, native in list(g_rowModels.items()):
        model.setCarouselRowCount(native)
    g_rowModels.clear()
    for presenter in list(g_filterPresenters):
        presenter._VehicleFiltersDataProvider__updateModel()
    g_filterPresenters.clear()
