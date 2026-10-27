# -*- coding: utf-8 -*-
from driftkings.common.utils.color_rating_data import color_tables
from driftkings.core.vehicle_markers.colors import normalize, palette
from driftkings.core.vehicle_markers.config import prepare
from driftkings.core.vehicle_markers.ratings import values as rating_values
from driftkings.core.vehicle_markers.schema import FILES, STATE_KEYS
from driftkings.settings.controls_schema import field
from driftkings.settings.definitions.base import SectionDefinition
from driftkings.settings.vehicle_markers_store import VehicleMarkersStore


# Sample vehicle for the marker preview. The client's vehicle cache supplies the live values; these come from
# res/scripts/item_defs/vehicles/usa (list.xml: tier 8 heavyTank; A12_T32.xml: hull 1320 + top turret 330 HP).
SAMPLE_VEHICLE = {'name': 'usa:A12_T32', 'vehicle': 'T32', 'level': 8, 'vtype': 'heavyTank', 'maxHp': 1650}


def sample_vehicle():
    result = dict(SAMPLE_VEHICLE)
    try:
        from items import vehicles
        nation, ident = vehicles.g_list.getIDsByName(result['name'])
        vehicle_type = vehicles.g_cache.vehicle(nation, ident)
        # Top turret, as most players field it; the battle reads the installed one.
        turrets = vehicle_type.turrets[0] if vehicle_type.turrets else ()
        result.update(vehicle=vehicle_type.shortUserString, level=vehicle_type.level,
                      vtype=vehicles.getVehicleClassFromVehicleType(vehicle_type) or result['vtype'],
                      maxHp=vehicle_type.hulls[0].maxHealth + max([turret.maxHealth for turret in turrets] or [0]))
    except Exception:
        pass
    nation, ident = result['name'].split(':')
    result.update(contour='gui/maps/icons/vehicle/contour/%s-%s.png' % (nation, ident),
                  typeIcon='gui/maps/icons/vehicleTypes/%s.png' % result['vtype'],
                  levelIcon='gui/maps/icons/levels/tank_level_%d.png' % result['level'],
                  tank='coui://gui/maps/shop/vehicles/600x450/%s.png' % ident)
    return result


class VehicleMarkersSettings(SectionDefinition):
    NAME = 'vehicle_markers'
    STORAGE_CLASS = VehicleMarkersStore
    STORAGE_FILES = FILES

    def normalize_loaded(self, values):
        # Validate the marker files as the battle will read them; the files keep their templates.
        prepare(values)
        return values

    def normalize_changes(self, values, changes):
        return self.normalize_loaded(values)

    def getControlColumns(self):
        items = [field(['markers', 'debug'], self.i18n['UI_debug'], tooltip=self.i18n['UI_debug_tip'])]
        items.append(field(['markers', 'colorRating'], self.i18n['UI_setting_colorRating_text'], 'Dropdown',
                           choices=range(len(color_tables)), choice_labels=[table['ScaleColor'] for table in color_tables],
                           tooltip=self.i18n['UI_setting_colorRating_tooltip']))
        items.append(field(['markers', 'ratingType'], self.i18n['UI_preview_ratingType'], 'Dropdown',
                           choices=('wn8', 'wnx', 'eff'), choice_labels=('WN8', 'WNX', 'EFF'),
                           tooltip=self.i18n['UI_preview_ratingType']))
        # One editor per marker file: markers.json, then the four state files.
        for key in ('markers',) + STATE_KEYS:
            items.append(field([key], self.i18n['UI_' + key], 'TextArea', jsonValue=True,
                               maxLength=524288, tooltip=self.i18n['UI_' + key + '_tip']))
        return (items, [])

    def getPanelPreview(self):
        labels = dict((key[11:], value) for key, value in self.i18n.items() if key.startswith('UI_preview_'))
        labels['colorRating'] = self.i18n['UI_setting_colorRating_text']
        for team in ('ally', 'enemy', 'squad', 'teamKiller'):
            labels[team + 'Dead'] = labels[team] + ' / ' + labels['dead']
        palettes = []
        for index, table in enumerate(color_tables):
            shared = palette(index)
            palettes.append({'name': table['ScaleColor'], 'colors': normalize({}, shared['colors']),
                             'damageColors': shared['damageColors'],
                             'ratings': dict((metric, rating_values({'battles': 15000, 'wn8': 2000, 'wnx': 1800,
                                 'eff': 1400, 'xwn8': 75, 'xeff': 65, 'winrate': 55}, metric, index))
                                 for metric in ('wn8', 'wnx', 'eff'))})
        vehicle = sample_vehicle()
        return {'kind': 'vehicleMarkers', 'labels': labels,
                'palettes': palettes, 'vehicle': vehicle,
                'tank': vehicle['tank']}
