# -*- coding: utf-8 -*-
import logging
import math
from Driftkings.core.marks_calculator import ceil_damage, ceil_damage_tens, combined_damage
from Driftkings.views.marks_model import delta_model

import BigWorld
from CurrentVehicle import g_currentVehicle
from dossiers2.ui.achievements import ACHIEVEMENT_BLOCK, MARK_OF_MASTERY_RECORD
from gui.Scaleform.daapi.view.lobby.profile.ProfileUtils import ProfileUtils
from gui.shared.gui_items.dossier.achievements.mark_on_gun import MarkOnGunAchievement
from gui.shared.personality import ServicesLocator

from Driftkings._constants import GLOBAL, MARKS_ON_GUN_HANGAR
from Driftkings.common import logException, getStatisticColor, getMoeDamageColor
from Driftkings.common import loadJson
from Driftkings.common.utils.achievement_dossiers import getAchievementDossier
from Driftkings.core.cache import cache_directory
from Driftkings.core.hooks import override
from Driftkings.settings.service import settings_service
from Driftkings.stats import getVehicleInfoData

LOG = logging.getLogger('Driftkings.MarksOnGunHangar')
FEATURE = 'DriftkingsMarksOnGunHangar'
RESOURCE = 'mods/Driftkings/MarksOnGunHangar/model'
ASSETS = 'coui://gui/gameface/mods/Driftkings/MarksOnGunHangar/'
g_controller = None
THRESHOLDS = (65, 85, 95)


def finite(value, default=0.0):
    try:
        value = float(value)
        return default if math.isnan(value) or math.isinf(value) else value
    except (ValueError, TypeError, OverflowError):
        return default


def goal(percent, moving_average, tier, selection=0, earned_marks=0):
    percent = max(0.0, min(100.0, finite(percent)))
    earned_marks = max(0, min(3, int(finite(earned_marks))))
    selection = max(0, min(3, int(finite(selection))))
    # Awarded marks are retained even if the current percentage later falls.
    progress_marks = max(earned_marks, sum(percent >= limit for limit in THRESHOLDS))
    mark = selection or min(3, progress_marks + 1)
    threshold = THRESHOLDS[mark - 1]
    eligible = finite(tier) >= 5
    achieved = eligible and (earned_marks >= mark or percent >= threshold)
    estimate = None
    average = finite(moving_average)
    if eligible and percent > 0 and average > 0:
        # Local proportional approximation, NOT a server threshold or a forecast
        # of the damage needed in the next single battle.
        estimate = int(math.ceil(average * threshold / percent / 10.0) * 10)
    return {'eligible': eligible, 'mark': mark, 'threshold': threshold,
            'achieved': achieved, 'gap': max(0.0, threshold - percent),
            'estimate': estimate, 'percent': percent}


def record_snapshot(history, vehicle_id, battles, percent, average):
    """Store one snapshot per observed battle counter, not per panel repaint."""
    vehicles = history.setdefault('vehicles', {})
    key = str(vehicle_id)
    points = vehicles.setdefault(key, [])
    sample = {'battles': max(0, int(finite(battles))),
              'percent': max(0.0, min(100.0, finite(percent))),
              'average': max(0.0, finite(average))}
    if points and sample['battles'] < points[-1]['battles']:
        # Reset/replaced dossier: do not turn a decreasing counter into a battle.
        points[:] = []
    if points and sample['battles'] == points[-1]['battles']:
        if points[-1] == sample:
            return False
        points[-1] = sample
    else:
        points.append(sample)
    del points[:-21]
    return True


def trend(history, vehicle_id, last_battles=10):
    points = history.get('vehicles', {}).get(str(vehicle_id), [])
    if len(points) < 2:
        return {'battles': 0, 'delta': None, 'points': [p['percent'] for p in points]}
    last_battles = max(1, min(20, int(finite(last_battles, 10))))
    start = len(points) - 2
    while start > 0 and points[-1]['battles'] - points[start]['battles'] < last_battles:
        start -= 1
    selected = points[start:]
    return {'battles': selected[-1]['battles'] - selected[0]['battles'],
            'delta': round(selected[-1]['percent'] - selected[0]['percent'], 2),
            'points': [p['percent'] for p in selected]}


from Driftkings.settings.templates.lobby.gun_marks import MarksOnGunHangarSettings as Settings


MARK_LEVELS = (0.0, 20.0, 40.0, 55.0, 65.0, 85.0, 95.0, 100.0)


def read_colors(rating_color, rating_value):
    return getStatisticColor(rating_color, rating_value, settings_service.getComponentDict(config).get(MARKS_ON_GUN_HANGAR.COLOR_RATING, 0))


config = Settings()


class MarksOnGunData(object):
    _MASTERY_LABELS = {
        1: '3rd class',
        2: '2nd class',
        3: '1st class',
        4: 'Ace Tanker'
    }

    @staticmethod
    def _safe(value, default=0.0):
        try:
            if value is None or math.isnan(value):
                return default
        except TypeError:
            if value is None:
                return default
        return value

    @staticmethod
    def _normalizeDigits(value):
        return ceil_damage(value)

    @staticmethod
    def _normalizeDigitsCoeff(value):
        return ceil_damage_tens(value)

    @staticmethod
    def _calcPercent(ema, start, end, damage, percent):
        if not damage or not percent:
            return 0.0
        while start <= end < 100.001 and ema < 30000:
            ema += 0.1
            start = ema / damage * percent
        return ema

    @staticmethod
    def _format_int(value):
        return '{:,}'.format(int(value)).replace(',', ' ')

    @staticmethod
    def _format_float(value, digits=2):
        fmt = '%%.%sf' % digits
        return fmt % float(value)

    @staticmethod
    def _escape_html(value):
        text = unicode(value if value is not None else '')
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _mastery_label(self, value):
        return self._MASTERY_LABELS.get(int(value or 0), '--')

    def _pick_color(self, value, levels):
        return getMoeDamageColor(value, levels, settings_service.getComponentDict(config).get(MARKS_ON_GUN_HANGAR.COLOR_RATING, 0))

    def _color_by_wn8(self, wn8):
        return read_colors('wn8', wn8)

    def _color_by_winrate(self, winrate):
        return read_colors('winrate', winrate)

    def _calculate_wn8(self, vehicle, random_stats, winrate):
        if not random_stats.getBattlesCount():
            return 0
        vehicleCD = getattr(vehicle, 'intCD', None) or getattr(vehicle, 'compactDescr', None)
        if not vehicleCD:
            return 0
        vInfo = getVehicleInfoData(vehicleCD)
        if not vInfo:
            return 0
        expected = {}
        for key in ('wn8expDamage', 'wn8expSpot', 'wn8expFrag', 'wn8expDef', 'wn8expWinRate'):
            expected[key] = self._safe(vInfo.get(key), 0.0)
        if not all(expected.values()):
            return 0
        damage = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamage()))
        spot = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgEnemiesSpotted()))
        frags = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgFrags()))
        defence = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCount, random_stats.getDroppedCapturePoints)))

        r_damage = float(damage) / max(1.0, expected['wn8expDamage'])
        r_spot = float(spot) / max(1.0, expected['wn8expSpot'])
        r_frag = float(frags) / max(1.0, expected['wn8expFrag'])
        r_def = float(defence) / max(1.0, expected['wn8expDef'])
        r_win = float(winrate) / max(1.0, expected['wn8expWinRate'])

        r_winc = max(0.0, (r_win - 0.71) / (1.0 - 0.71))
        r_damagec = max(0.0, (r_damage - 0.22) / (1.0 - 0.22))
        r_spotc = max(0.0, min(r_damagec + 0.1, max(0.0, (r_spot - 0.38) / (1.0 - 0.38))))
        r_fragc = max(0.0, min(r_damagec + 0.2, max(0.0, (r_frag - 0.12) / (1.0 - 0.12))))
        r_defc = max(0.0, min(r_damagec + 0.1, max(0.0, (r_def - 0.10) / (1.0 - 0.10))))
        return int(980 * r_damagec + 210 * r_damagec * r_fragc + 155 * r_fragc * r_spotc + 75 * r_defc * r_fragc + 145 * min(1.8, r_winc))

    def _get_mastery_info(self, dossier):
        mastery_value = 0
        mastery_icon = ''
        try:
            mastery = dossier.getTotalStats().getAchievement(MARK_OF_MASTERY_RECORD)
            if mastery is not None:
                mastery_value = int(mastery.getValue() or 0)
                mastery_icon = mastery.getSmallIcon().replace('../', '')
                if mastery_icon and not mastery_icon.startswith('img://'):
                    mastery_icon = 'img://%s' % mastery_icon
        except Exception:
            mastery_value = 0
            mastery_icon = ''
        return {
            'value': mastery_value,
            'icon': mastery_icon
        }

    def calc_statistics(self, percent, damage):
        percent = self._safe(percent, 0.0)
        damage = self._safe(damage, 0.0)
        if damage <= 0.0:
            damage = 1.0
        next_percent = math.floor(percent) + 1
        next_damage = self._calcPercent(damage, percent, next_percent, damage, percent)
        p20 = self._calcPercent(0.0, 0.0, 20.0, damage, percent)
        p40 = self._calcPercent(0.0, 0.0, 40.0, damage, percent)
        p55 = self._calcPercent(0.0, 0.0, 55.0, damage, percent)
        p65 = self._calcPercent(0.0, 0.0, 65.0, damage, percent)
        p85 = self._calcPercent(0.0, 0.0, 85.0, damage, percent)
        p95 = self._calcPercent(0.0, 0.0, 95.0, damage, percent)
        p100 = self._calcPercent(0.0, 0.0, 100.0, damage, percent)
        data = [0.0, p20, p40, p55, p65, p85, p95, p100]
        idx = None
        for level in MARK_LEVELS:
            if level >= percent:
                idx = level
                break
        if idx is None:
            idx = 100.0
        check = MARK_LEVELS.index(idx)
        limit2 = data[check]
        delta = limit2 - next_damage
        for value in xrange(len(data)):
            if data[value] == next_damage or data[value] == limit2:
                continue
            if value > check:
                data[value] = self._normalizeDigitsCoeff(data[value] + delta)
        if next_percent == 101:
            next_percent = 100
            next_damage = data[7]
        return (next_percent, next_damage, data[1], data[2], data[3], data[4], data[5], data[6], data[7])

    def collect(self, dossier=None):
        vehicle = g_currentVehicle.item
        if dossier is None:
            if not vehicle:
                return None
            dossier = g_currentVehicle.getDossier()
        else:
            vehicle = ServicesLocator.itemsCache.items.getItemByCD(dossier.getCompactDescriptor())
        if dossier is None:
            return None

        random_stats = dossier.getRandomStats()
        # Use one battle mode throughout; total stats combine several modes.
        battles = int(self._safe(random_stats.getBattlesCount(), 0))
        wins = int(self._safe(random_stats.getWinsCount(), 0))
        winrate = 100.0 * wins / battles if battles else 0.0

        avg_damage = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamage()))
        track = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCountVer2, random_stats.getDamageAssistedTrack)))
        radio = self._safe(ProfileUtils.getValueOrUnavailable(random_stats._getAvgValue(random_stats.getBattlesCountVer2, random_stats.getDamageAssistedRadio)))
        stun = self._safe(ProfileUtils.getValueOrUnavailable(random_stats.getAvgDamageAssistedStun()))
        current_damage = int(combined_damage(avg_damage, track, radio, stun))

        wn8 = self._calculate_wn8(vehicle, random_stats, winrate)
        mastery = self._get_mastery_info(dossier)
        damage_rating = self._safe(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'damageRating') / 100.0, 0.0)
        moving_avg_damage = self._safe(dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'movingAvgDamage'), 0.0)

        result = {
            'vehicleName': vehicle.shortUserName,
            'vehicleID': vehicle.intCD,
            'tier': vehicle.level,
            'earnedMarks': dossier.getRecordValue(ACHIEVEMENT_BLOCK.TOTAL, 'marksOnGun'),
            'randomBattles': battles,
            'battles': battles,
            'wins': wins,
            'winRate': winrate,
            'winRateColor': self._color_by_winrate(winrate),
            'wn8': wn8,
            'wn8Color': self._color_by_wn8(wn8),
            'masteryValue': mastery['value'],
            'masteryIcon': mastery['icon'],
            'hasMoE': vehicle.level >= 5 and damage_rating > 0.0
        }

        if damage_rating <= 0.0:
            result.update({
                'damageRating': 0.0,
                'currentDamage': current_damage,
                'movingAvgDamage': 0.0
            })
            return result

        next_percent, need_damage, p20, p40, p55, p65, p85, p95, p100 = self.calc_statistics(damage_rating, moving_avg_damage)
        levels = [p20, p40, p55, p65, p85, p95, p100]
        result.update({
            'damageRating': damage_rating,
            'currentDamage': current_damage,
            'movingAvgDamage': moving_avg_damage,
            'nextPercent': int(next_percent),
            'needDamage': int(need_damage),
            'p20': self._normalizeDigits(p20),
            'p40': self._normalizeDigits(p40),
            'p55': self._normalizeDigits(p55),
            'p65': self._normalizeDigits(p65),
            'p85': self._normalizeDigits(p85),
            'p95': self._normalizeDigits(p95),
            'p100': self._normalizeDigits(p100),
            'currentDamageColor': self._pick_color(current_damage, levels),
            'movingAvgDamageColor': self._pick_color(moving_avg_damage, levels),
            'needDamageColor': self._pick_color(int(need_damage), levels)
        })
        return result

    def build_tooltip(self, dossier):
        data = self.collect(dossier)
        if data is None or not data.get('hasMoE'):
            return None
        c20 = read_colors('mog', 20.0)
        c40 = read_colors('mog', 40.0)
        c55 = read_colors('mog', 55.0)
        c65 = read_colors('mog', 65.0)
        c85 = read_colors('mog', 85.0)
        c95 = read_colors('mog', 95.0)
        c100 = read_colors('mog', 100.0)
        ctx = {
            'nextPercent': data['nextPercent'],
            'needDamage': '<font color="%s">%s</font>' % (data['needDamageColor'], self._format_int(data['needDamage'])),
            'currentMovingAvgDamage': '<font color="%s">%s</font>' % (data['movingAvgDamageColor'], self._format_int(data['movingAvgDamage'])),
            'currentDamage': '<font color="%s">%s</font>' % (data['currentDamageColor'], self._format_int(data['currentDamage'])),
            'mastery': self._mastery_label(data['masteryValue']),
            'wn8': data['wn8'] if data['wn8'] else '--',
            'winRate': '%s%%' % self._format_float(data['winRate']) if data['battles'] else '--',
            '_20': data['p20'],
            '_40': data['p40'],
            '_55': data['p55'],
            '_65': data['p65'],
            '_85': data['p85'],
            '_95': data['p95'],
            '_100': data['p100'],
            'c20': c20,
            'c40': c40,
            'c55': c55,
            'c65': c65,
            'c85': c85,
            'c95': c95,
            'c100': c100
        }
        template = config.i18n['UI_tooltipsFull'] if settings_service.getComponentDict(config)[MARKS_ON_GUN_HANGAR.SHOW_TOOLTIP_TARGETS] else config.i18n['UI_tooltips']
        return template.format(**ctx)

    def build_panel_model(self):
        result = {'config': get_view_config(config), 'state': 'empty',
                  'vehicle': config.i18n['UI_panel_chooseVehicle'], 'message': config.i18n['UI_panel_selectVehicle'],
                  'labels': {key[9:]: value for key, value in config.i18n.items() if key.startswith('UI_panel_')}}
        if not g_currentVehicle.isPresent():
            return result
        data = self.collect()
        if data is None:
            result.update(vehicle=unicode(g_currentVehicle.item.shortUserName),
                          message=config.i18n['UI_panel_noDossier'])
            return result
        target = goal(data['damageRating'], data['movingAvgDamage'], data['tier'],
                      settings_service.getComponentDict(config)[MARKS_ON_GUN_HANGAR.GOAL_SELECTION], data['earnedMarks'])
        recent = g_history.observe(data) if target['eligible'] else {'delta': None, 'battles': 0}
        mastery = max(0, min(4, int(finite(data['masteryValue']))))
        icon = ('gui/maps/icons/achievement/32x32/markOfMastery%s.png' % mastery
                if mastery else 'gui/maps/icons/achievements/summary/mastery/mastery_empty_small.png')
        result.update({
            'state': 'data', 'vehicle': unicode(data['vehicleName']), 'tier': data['tier'],
            'target': target, 'recent': recent,
            'delta': delta_model(recent.get('delta')),
            'progress': target['percent'] / 100.0,
            'displayMarks': max(max(0, min(3, int(finite(data['earnedMarks'])))), sum(data['damageRating'] >= limit for limit in THRESHOLDS)),
            'thirdAchieved': bool(target['eligible'] and (data['damageRating'] >= 95 or data['earnedMarks'] >= 3)),
            'earnedMarks': max(0, min(3, int(finite(data['earnedMarks'])))),
            'average': self._format_int(data['movingAvgDamage']),
            'estimate': '~' + self._format_int(target['estimate']) if target['estimate'] is not None else '--',
            'mastery': config.i18n['UI_panel_mastery%s' % mastery],
            'masteryIcon': 'coui://' + icon,
            'wn8': self._format_int(data['wn8']) if data['wn8'] else '--',
            'wn8Color': data['wn8Color'], 'winRateColor': data['winRateColor'],
            'winRate': ('%.2f%%' % data['winRate']) if data['battles'] else '--',
            'battles': self._format_int(data['battles'])
        })
        return result


class ProgressHistory(object):
    def __init__(self):
        self.cachePath = cache_directory('gun_marks_hangar')
        self.account = None
        self.data = {'vehicles': {}}

    def observe(self, data):
        account = getattr(BigWorld.player(), 'databaseID', None)
        if not account:
            return {'delta': None, 'battles': 0}
        name = 'progress_%s' % int(account)
        if account != self.account:
            self.account = account
            loaded = loadJson(config.ID, name, {'vehicles': {}}, self.cachePath)
            self.data = {'vehicles': {}}
            if isinstance(loaded, dict) and isinstance(loaded.get('vehicles'), dict):
                for vehicle, points in loaded['vehicles'].items():
                    if isinstance(points, list):
                        for point in points[-21:]:
                            if isinstance(point, dict) and all(k in point for k in ('battles', 'percent', 'average')):
                                record_snapshot(self.data, vehicle, point['battles'], point['percent'], point['average'])
        if record_snapshot(self.data, data['vehicleID'], data['randomBattles'], data['damageRating'], data['movingAvgDamage']):
            loadJson(config.ID, name, self.data, self.cachePath, True, quiet=True)
        return trend(self.data, data['vehicleID'], settings_service.getComponentDict(config)[MARKS_ON_GUN_HANGAR.HISTORY_BATTLES])


g_history = ProgressHistory()

g_data = MarksOnGunData()


from Driftkings.views.hangar.gun_marks import MarksOnGunHangarController, get_view_config, install_gameface


@override(MarkOnGunAchievement, 'getUserCondition')
@logException
def new__getUserCondition(func, *args):
    dossier = getAchievementDossier(args[0])
    if settings_service.getComponentDict(config)[GLOBAL.ENABLED] and settings_service.getComponentDict(config)[MARKS_ON_GUN_HANGAR.SHOW_IN_STATISTIC] and dossier is not None:
        tooltip = g_data.build_tooltip(dossier)
        if tooltip:
            return tooltip
    return func(*args)


g_controller = MarksOnGunHangarController()
def init():
    try:
        install_gameface()
        g_controller.start()
    except Exception:
        LOG.exception('Gameface hangar integration unavailable')


def fini():
    g_controller.stop()
