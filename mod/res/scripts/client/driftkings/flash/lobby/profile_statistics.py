# -*- coding: utf-8 -*-
"""Format the native Flash statistics and vehicle dossier fields."""
from driftkings.common.utils.colorratting import getColor, getRatingColors, getStatisticColor
from driftkings.common.utils.formatting import hexToDecimal
from driftkings.core.hooks import override
from driftkings.core.profile_ratings import account_wn8, parse_thresholds, pure_random_stats, vehicle_wn8
from driftkings.logger import get_logger
from driftkings.settings.service import settings_service

LOG = get_logger("ProfileStatistics")


def enabled(surface='statistics'):
    settings = settings_service.getComponentDict('profile_ratings')
    return settings.get('enabled', True) and settings.get(surface + 'Colors', True)


def colored(text, metric, value, surface='statistics'):
    settings = settings_service.getComponentDict('profile_ratings')
    if not enabled(surface) or value is None or value < 0:
        return text
    scale = settings.get('colorScale', 0)
    if metric in ('survival', 'damageReceivedHP'):
        survival = metric == 'survival'
        if not settings.get('colorSurvival' if survival else 'colorReceivedDamage', True):
            return text
        key = 'survivalThresholds' if survival else 'receivedDamageThresholds'
        limits = parse_thresholds(settings.get(key, '20,30,40,50,60' if survival else '25,50,75,100,125'), 100 if survival else 500)
        if not survival:
            limits = [limit / 100.0 for limit in limits]
        palette = getRatingColors(scale)['colorRating']
        names = ('very_bad', 'bad', 'normal', 'good', 'very_good', 'unique')
        bands = [{'value': limit, 'color': palette[name]} for limit, name in zip(limits + [1e30], names if survival else reversed(names))]
        color = getColor({metric: bands}, metric, value)
    else:
        color = getStatisticColor(metric, value, scale)
    return u'<font color="{}">{}</font>'.format(color, text)


def vehicle_renderers(container, depth=0):
    """CLIK keeps visible renderers inside its nested content sprite."""
    if depth > 8:
        return
    for index in range(int(container.numChildren)):
        child = container.getChildAt(index)
        if hasattr(child, 'battlesTF') and hasattr(child, 'vehicleTF'):
            yield child
        elif hasattr(child, 'numChildren'):
            for renderer in vehicle_renderers(child, depth + 1):
                yield renderer


def paint_vehicle_list(view):
    """Color native text fields without changing the sortable row values."""
    if not view.isActive:
        return
    try:
        listing = view.flashObject.listComponent.techniqueList
        count = int(listing.numChildren)
        painted = 0
        for renderer in vehicle_renderers(listing):
            if not renderer.data:
                continue
            painted += 1
            row_id = int(renderer.data.id)
            colors = view._dkVehicleColors.get(row_id, {}) if enabled('vehicle') else {}
            for field_name in ('vehicleTF', 'battlesTF', 'winsTF'):
                field = getattr(renderer, field_name)
                key = (str(renderer.name), field_name)
                if key not in view._dkVehicleOriginalColors:
                    view._dkVehicleOriginalColors[key] = int(field.textColor)
                value = colors.get(field_name, view._dkVehicleOriginalColors[key])
                if int(field.textColor) != value:
                    field.textColor = value
        if not getattr(view, '_dkVehiclePaintReported', False):
            LOG.info('Vehicle list: children=%s renderers=%s colorRows=%s active=%s',
                     count, painted, len(view._dkVehicleColors), view.isActive)
            view._dkVehiclePaintReported = True
    except (AttributeError, TypeError, ValueError, ReferenceError):
        if not getattr(view, '_dkVehiclePaintReported', False):
            LOG.exception('Cannot access native vehicle-list text fields')
            view._dkVehiclePaintReported = True


def install():
    from gui.Scaleform.daapi.view.lobby.profile import ProfileUtils as fields
    from gui.Scaleform.daapi.view.lobby.profile.profile_statistics_vos import ProfileAllStatisticsVO
    from gui.Scaleform.daapi.view.lobby.profile.ProfileStatistics import ProfileStatistics
    from gui.Scaleform.daapi.view.lobby.profile.ProfileTechnique import ProfileTechnique
    from gui.Scaleform.genConsts.PROFILE_DROPDOWN_KEYS import PROFILE_DROPDOWN_KEYS

    from driftkings.stats.vehinfo import getVehicleInfoData

    # Native dossier rendering is synchronous. A stack keeps nested requests
    # isolated and never reuses the previously selected tank or player.
    vehicle_context = []

    @override(ProfileTechnique, '_receiveVehicleDossier')
    def vehicle_dossier(original, view, vehicle_id, database_id):
        vehicle = view.itemsCache.items.getItemByCD(vehicle_id)
        hp = vehicle.descriptor.maxHealth if vehicle is not None else None
        dossier = view.itemsCache.items.getVehicleDossier(vehicle_id, database_id)
        vehicle_context.append((vehicle_id, hp, view._battlesType, dossier))
        try:
            result = original(view, vehicle_id, database_id)
            if enabled('vehicle') and view._battlesType == PROFILE_DROPDOWN_KEYS.ALL:
                dossier = view.itemsCache.items.getVehicleDossier(vehicle_id, database_id)
                if dossier is not None:
                    value = vehicle_wn8(pure_random_stats(dossier, vehicle_id), vehicle_id, getVehicleInfoData)
                    if value is not None:
                        scale = settings_service.getComponentDict('profile_ratings').get('colorScale', 0)
                        view._dkVehicleColors.setdefault(vehicle_id, {})['vehicleTF'] = int(
                            getStatisticColor('wn8', value, scale).lstrip('#'), 16)
            return result
        finally:
            vehicle_context.pop()

    # These native fields use HTML text. Keep all other modes/fields unchanged.
    specifications = (
        ('_BattlesCountField', 'battles', 'getBattlesCount', 1),
        ('_WinsEfficiencyField', 'winrate', 'getWinsEfficiency', 100),
        ('_SurvivalField', 'survival', 'getSurvivalEfficiency', 100),
        ('_DamageCoefficientField', 'tdv', 'getDamageEfficiency', 1),
        ('_HitsField', 'hitsRatio', 'getHitsEfficiency', 100),
        ('_AvgDmgField', 'avgDamage', 'getAvgDamage', 1),
        ('_AvgEnemiesSpottedField', 'avgSpotted', 'getAvgEnemiesSpotted', 1),
        ('_AvgDestroyedField', 'avgFrags', 'getAvgFrags', 1),
    )

    def handler(metric, method, scale):
        def build(original, field, stats, current):
            text = original(field, stats, current)
            value = getattr(stats, method)()
            return colored(text, metric, value * scale if value is not None else None,
                           'vehicle' if vehicle_context else 'statistics')
        return build

    for name, metric, method, scale in specifications:
        override(getattr(fields, name), '_buildData')(handler(metric, method, scale))

    @override(fields._AvgReceivedDmgField, '_buildData')
    def received(original, field, stats, current):
        text = original(field, stats, current)
        hp = vehicle_context[-1][1] if vehicle_context else None
        value = stats.getAvgDamageReceived()
        if not hp or hp <= 0 or value is None:
            return text
        return colored(text, 'damageReceivedHP', float(value) / hp, 'vehicle')

    @override(fields.DetailedStatisticsUtils, 'getStatistics')
    def detailed(original, stats, current, layout):
        result = original(stats, current, layout)
        settings = settings_service.getComponentDict('profile_ratings')
        if (not vehicle_context or not settings.get('enabled', True)
                or not settings.get('showVehicleWN8', True)
                or vehicle_context[-1][2] != PROFILE_DROPDOWN_KEYS.ALL or not result):
            return result
        ident = vehicle_context[-1][0]
        dossier = vehicle_context[-1][3]
        value = vehicle_wn8(pure_random_stats(dossier, ident) if dossier else None, ident, getVehicleInfoData)
        if value is None and not settings.get('showUnavailableWN8', True):
            return result
        text = colored(str(value), 'wn8', value, 'vehicle') if value is not None else '--'
        # Copy the native containers so no shared layout/dossier is mutated.
        result = list(result)
        result[0] = dict(result[0])
        result[0]['data'] = list(result[0]['data']) + [
            {'label': 'WN8', 'data': text, 'tooltip': '', 'tooltipData': None}]
        return result

    @override(ProfileAllStatisticsVO, '_getHeaderData')
    def header(original, vo, data):
        result = [dict(item) for item in original(vo, data)]
        stats, dossier = data[0], data[1]
        for index, metric, value in ((0, 'battles', stats.getBattlesCount()),
                                      (1, 'winrate', stats.getWinsEfficiency() * 100 if stats.getWinsEfficiency() is not None else None),
                                      (2, 'avgDamage', stats.getAvgDamage())):
            result[index]['text'] = colored(result[index]['text'], metric, value)
        settings = settings_service.getComponentDict('profile_ratings')
        if settings.get('enabled', True) and settings.get('showPlayerWN8', True):
            value = account_wn8(pure_random_stats(dossier), getVehicleInfoData)
            if value is None and not settings.get('showUnavailableWN8', True):
                return tuple(result)
            text = colored(str(value), 'wn8', value) if value is not None else '--'
            item = fields.ProfileUtils.packLditItemData(text, 'WN8', '', 'avgPersonalRating40x32.png')
            # Appended after the native mastery badge; no native item is replaced.
            result.append(item)
        return tuple(result)

    @override(ProfileTechnique, '_getTechniqueListVehicles')
    def vehicles(original, view, target_data, *args, **kwargs):
        rows = original(view, target_data, *args, **kwargs)
        view._dkVehicleColors = {}
        if not enabled('vehicle'):
            return rows
        scale = settings_service.getComponentDict('profile_ratings').get('colorScale', 0)

        def color(metric, value):
            return hexToDecimal(getStatisticColor(metric, value, scale))

        for row in rows:
            # WN8 is defined for random battles only. Never use win rate as a
            # substitute when the vehicle dossier/expected values are missing.
            values = {'battlesTF': color('battles', row['battlesCount'])}
            if 'winsEfficiency' in row and view._battlesType != PROFILE_DROPDOWN_KEYS.FALLOUT:
                values['winsTF'] = color('winrate', row['winsEfficiency'])
            if view._battlesType == PROFILE_DROPDOWN_KEYS.ALL:
                dossier = view.itemsCache.items.getVehicleDossier(row['id'], view._userID)
                if dossier is not None:
                    value = vehicle_wn8(pure_random_stats(dossier, row['id']), row['id'], getVehicleInfoData)
                    if value is not None:
                        values['vehicleTF'] = color('wn8', value)
            view._dkVehicleColors[row['id']] = values
        return rows

    def refresh_view(view):
        if view.isActive:
            view.invokeUpdate()
            if isinstance(view, ProfileTechnique) and view._selectedVehicleIntCD is not None:
                view.requestData(view._selectedVehicleIntCD)

    def changed(view):
        def refresh(*args):
            refresh_view(view)
        return refresh

    def populated(original, view):
        if isinstance(view, ProfileTechnique):
            from driftkings.ui import CyclicTimerEvent
            view._dkVehiclePaintReported = False
            view._dkVehicleColors = {}
            view._dkVehicleOriginalColors = {}
            view._dkVehicleColorTimer = CyclicTimerEvent(0.2, lambda: paint_vehicle_list(view))
        result = original(view)
        if isinstance(view, ProfileTechnique):
            view._dkVehicleColorTimer.start()
        view._dkProfileColorsChanged = changed(view)
        settings_service.onModSettingsChanged.connect(view._dkProfileColorsChanged, 'profile_ratings')
        return result

    def disposed(original, view):
        timer = getattr(view, '_dkVehicleColorTimer', None)
        if timer is not None:
            timer.stop()
            del view._dkVehicleColorTimer
            del view._dkVehicleColors
            del view._dkVehicleOriginalColors
        callback = getattr(view, '_dkProfileColorsChanged', None)
        if callback is not None:
            settings_service.onModSettingsChanged.disconnect(callback)
            del view._dkProfileColorsChanged
        return original(view)

    for target in (ProfileStatistics, ProfileTechnique):
        override(target, '_populate')(populated)
        override(target, '_dispose')(disposed)
